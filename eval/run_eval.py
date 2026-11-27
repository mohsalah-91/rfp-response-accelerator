"""Run the labeled RFP evaluation directly against the retrieval and answer pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from app.config import settings
from app.database import pool
from app.router import HybridSearchTimings, _hybrid_search_and_rerank, _synthesize_answer


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
QUESTION_PATH = REPOSITORY_ROOT / "incoming-rfp" / "questions.jsonl"
DECISIONS = ("answer", "answer_negative", "answer_partial", "redirect", "refuse")
ANSWERABLE_DECISIONS = {"answer", "answer_negative", "answer_partial"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the RFP question set against the live pipeline.")
    parser.add_argument("--runs", type=int, default=1, help="Number of full passes over the question set (default: 1).")
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.RAG_DEFAULT_TOP_K,
        help="Retrieved chunk depth (default: RAG_DEFAULT_TOP_K).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPOSITORY_ROOT / "eval" / "results.json",
        help="Machine-readable output path (default: eval/results.json).",
    )
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if not 1 <= args.top_k <= 10:
        parser.error("--top-k must be between 1 and 10")
    return args


def load_questions() -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for line in QUESTION_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            questions.append(json.loads(line))
    return questions


def percentile(values: list[int], proportion: float) -> int | None:
    """Return the nearest-rank percentile without adding a statistics dependency."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(proportion * len(ordered)) - 1)]


def latency_summary(results: list[dict[str, Any]]) -> dict[str, dict[str, int | None]]:
    stages = ("retrieve", "rerank", "synthesize", "total")
    return {
        stage: {
            "p50": percentile([result["timings_ms"][stage] for result in results if result.get("timings_ms")], 0.50),
            "p95": percentile([result["timings_ms"][stage] for result in results if result.get("timings_ms")], 0.95),
        }
        for stage in stages
    }


def score_summary(results: list[dict[str, Any]], expected_decisions: set[str]) -> dict[str, float | int | None]:
    scores = [
        result["retrieved_context"][0]["rerank_score"]
        for result in results
        if result["expected_behavior"] in expected_decisions and result.get("retrieved_context")
    ]
    return {"mean_top_1_rerank_score": round(mean(scores), 6) if scores else None, "count": len(scores)}


def run_metrics(results: list[dict[str, Any]], questions: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [result for result in results if not result.get("error")]
    correct = sum(result["decision"] == result["expected_behavior"] for result in successful)
    expected_counts = Counter(question["expected_behavior"] for question in questions)
    returned_counts = Counter(result["decision"] for result in successful)
    eligible_retrieval = [result for result in successful if result["expected_source"]]
    hits = sum(result["retrieval_hit"] for result in eligible_retrieval)
    mrr = mean([result["mrr"] for result in eligible_retrieval]) if eligible_retrieval else None
    return {
        "attempted": len(results),
        "failed": len(results) - len(successful),
        "correct_over_all_attempted": {
            "correct": correct,
            "denominator": len(results),
            "percentage": round((correct / len(results)) * 100, 2) if results else None,
        },
        "completed_accuracy": {
            "correct": correct,
            "denominator": len(successful),
            "percentage": round((correct / len(successful)) * 100, 2) if successful else None,
        },
        "decision_accuracy": {
            "correct": correct,
            "denominator": len(successful),
            "percentage": round((correct / len(successful)) * 100, 2) if successful else None,
        },
        "failure_count": len(results) - len(successful),
        "decision_breakdown": {
            decision: {"expected": expected_counts[decision], "returned": returned_counts[decision]}
            for decision in DECISIONS
        },
        "retrieval": {
            "eligible_questions": len(eligible_retrieval),
            "hits": hits,
            "hit_rate_percentage": round((hits / len(eligible_retrieval)) * 100, 2) if eligible_retrieval else None,
            "mrr": round(mrr, 6) if mrr is not None else None,
        },
        "top_1_rerank_score": {
            "answerable": score_summary(successful, ANSWERABLE_DECISIONS),
            "not_answerable": score_summary(successful, set(DECISIONS) - ANSWERABLE_DECISIONS),
        },
        "latency_ms": latency_summary(successful),
    }


async def evaluate_question(question: dict[str, Any], top_k: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": question["id"],
        "section": question["section"],
        "question": question["question"],
        "expected_source": question["expected_source"],
        "expected_behavior": question["expected_behavior"],
    }
    try:
        total_started = time.perf_counter()
        hybrid_timings = HybridSearchTimings()
        retrieved_context = await _hybrid_search_and_rerank(
            question["question"], top_k, pool, hybrid_timings
        )
        synthesize_started = time.perf_counter()
        answer = await _synthesize_answer(question["question"], retrieved_context)
        timings_ms = {
            "retrieve": hybrid_timings.retrieve,
            "rerank": hybrid_timings.rerank,
            "rerank_wait": hybrid_timings.rerank_wait,
            "synthesize": int((time.perf_counter() - synthesize_started) * 1000),
            "total": int((time.perf_counter() - total_started) * 1000),
        }
        sources = set(question["expected_source"])
        first_match_rank = next(
            (rank for rank, chunk in enumerate(retrieved_context, start=1) if chunk.title in sources), None
        )
        result.update(
            {
                "decision": answer.decision,
                "answer": answer.answer,
                "reason": answer.reason,
                "model_used": answer.model_used,
                "citations": answer.citations,
                "needs_sme_review": answer.needs_sme_review,
                "retrieved_context": [chunk.model_dump() for chunk in retrieved_context],
                "retrieval_hit": first_match_rank is not None if sources else None,
                "mrr": round(1 / first_match_rank, 6) if first_match_rank else 0.0 if sources else None,
                "timings_ms": timings_ms,
            }
        )
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    return result


def print_run_summary(run_index: int, metrics: dict[str, Any]) -> None:
    print(f"\nRun {run_index} breakdown")
    print("Decision breakdown:")
    print("  decision          expected  returned")
    for decision, counts in metrics["decision_breakdown"].items():
        print(f"  {decision:<17} {counts['expected']:>8}  {counts['returned']:>8}")
    retrieval = metrics["retrieval"]
    hit_rate = "n/a" if retrieval["hit_rate_percentage"] is None else f"{retrieval['hit_rate_percentage']:.2f}%"
    print(f"Retrieval hit rate: {retrieval['hits']}/{retrieval['eligible_questions']} eligible ({hit_rate}); MRR: {retrieval['mrr']}")
    scores = metrics["top_1_rerank_score"]
    print(f"Mean top-1 rerank score: answerable={scores['answerable']['mean_top_1_rerank_score']} (n={scores['answerable']['count']}), not answerable={scores['not_answerable']['mean_top_1_rerank_score']} (n={scores['not_answerable']['count']})")
    print("Latency (ms):")
    for stage, values in metrics["latency_ms"].items():
        print(f"  {stage:<10} p50={values['p50']}  p95={values['p95']}")


def stability_summary(run_results: list[dict[str, Any]], questions: list[dict[str, Any]], runs: int) -> dict[str, Any]:
    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in run_results:
        for result in run["results"]:
            by_question[result["id"]].append(result)
    unstable = []
    stable_count = 0
    for question in questions:
        results = by_question[question["id"]]
        decisions = sorted({result["decision"] for result in results if result.get("decision")})
        failures = sum(bool(result.get("error")) for result in results)
        fully_stable = len(results) == runs and failures == 0 and len(decisions) == 1
        if fully_stable:
            stable_count += 1
        else:
            unstable.append({"id": question["id"], "question": question["question"], "decisions": decisions, "failure_count": failures})
    return {"stable_count": stable_count, "total_questions": len(questions), "unstable_questions": unstable}


def print_stability(summary: dict[str, Any]) -> None:
    print("\nDecision stability details")
    if not summary["unstable_questions"]:
        print("All questions returned the same decision on every successful run.")
        return
    print("Unstable questions:")
    for item in summary["unstable_questions"]:
        decisions = ", ".join(item["decisions"]) or "no successful decisions"
        print(f"  {item['id']}: {item['question']}")
        print(f"    decisions: {decisions}; failures: {item['failure_count']}")


def print_headline(run_results: list[dict[str, Any]], stability: dict[str, Any] | None) -> None:
    print("\nEvaluation summary")
    for run in run_results:
        metrics = run["metrics"]
        all_attempted = metrics["correct_over_all_attempted"]
        completed = metrics["completed_accuracy"]
        all_percentage = "n/a" if all_attempted["percentage"] is None else f"{all_attempted['percentage']:.2f}%"
        completed_percentage = "n/a" if completed["percentage"] is None else f"{completed['percentage']:.2f}%"
        print(
            f"Run {run['run']}: attempted={metrics['attempted']}; failed={metrics['failed']}; "
            f"correct/all attempted={all_attempted['correct']}/{all_attempted['denominator']} ({all_percentage}); "
            f"completed accuracy={completed['correct']}/{completed['denominator']} ({completed_percentage})"
        )
    if stability is not None:
        print(f"Decision stability: {stability['stable_count']}/{stability['total_questions']} fully stable questions")


async def run_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    questions = load_questions()
    run_results: list[dict[str, Any]] = []
    await pool.open()
    try:
        for run_index in range(1, args.runs + 1):
            print(f"Starting run {run_index}/{args.runs} ({len(questions)} questions, top_k={args.top_k})")
            results = []
            for question_index, question in enumerate(questions, start=1):
                print(f"  Run {run_index}/{args.runs}, question {question_index}/{len(questions)}: {question['id']}...", flush=True)
                result = await evaluate_question(question, args.top_k)
                if result.get("error"):
                    print(f"    failed: {result['error']}", flush=True)
                else:
                    print(f"    decision: {result['decision']}", flush=True)
                results.append(result)
            metrics = run_metrics(results, questions)
            run_results.append({"run": run_index, "results": results, "metrics": metrics})
    finally:
        await pool.close()

    stability = stability_summary(run_results, questions, args.runs) if args.runs > 1 else None
    print_headline(run_results, stability)
    for run in run_results:
        print_run_summary(run["run"], run["metrics"])
    if stability is not None:
        print_stability(stability)
    return {
        "configuration": {"runs": args.runs, "top_k": args.top_k, "question_path": str(QUESTION_PATH.relative_to(REPOSITORY_ROOT))},
        "runs": run_results,
        "aggregates": {
            "per_run": [run["metrics"] for run in run_results],
            "decision_stability": stability,
        },
    }


def main() -> None:
    args = parse_args()
    artifact = asyncio.run(run_evaluation(args))
    output_path = args.out if args.out.is_absolute() else REPOSITORY_ROOT / args.out
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote evaluation artifact: {output_path}")


if __name__ == "__main__":
    main()
