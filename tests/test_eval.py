"""Unit tests for evaluation aggregation without live provider calls."""

import os
import unittest


os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("COHERE_API_KEY", "test-cohere-key")

from eval.run_eval import run_metrics, stability_summary


class EvaluationMetricsTests(unittest.TestCase):
    def test_retrieval_metrics_exclude_questions_without_expected_sources(self) -> None:
        questions = [
            {"id": "q1", "expected_behavior": "answer"},
            {"id": "q2", "expected_behavior": "refuse"},
        ]
        results = [
            {
                "id": "q1", "expected_behavior": "answer", "expected_source": ["source.md"],
                "decision": "answer", "retrieval_hit": True, "mrr": 1.0,
                "retrieved_context": [{"rerank_score": 0.9}],
                "timings_ms": {"retrieve": 1, "rerank": 2, "synthesize": 3, "total": 6},
            },
            {
                "id": "q2", "expected_behavior": "refuse", "expected_source": [],
                "decision": "refuse", "retrieval_hit": None, "mrr": None,
                "retrieved_context": [],
                "timings_ms": {"retrieve": 1, "rerank": 0, "synthesize": 1, "total": 2},
            },
        ]

        metrics = run_metrics(results, questions)

        self.assertEqual(metrics["retrieval"]["eligible_questions"], 1)
        self.assertEqual(metrics["retrieval"]["hits"], 1)
        self.assertEqual(metrics["retrieval"]["mrr"], 1.0)
        self.assertEqual(metrics["decision_accuracy"]["denominator"], 2)
        self.assertEqual(metrics["attempted"], 2)
        self.assertEqual(metrics["failed"], 0)
        self.assertEqual(metrics["correct_over_all_attempted"]["denominator"], 2)
        self.assertEqual(metrics["completed_accuracy"]["denominator"], 2)

    def test_stability_marks_failed_or_changed_decisions_unstable(self) -> None:
        questions = [
            {"id": "q1", "question": "Stable?"},
            {"id": "q2", "question": "Unstable?"},
        ]
        runs = [
            {"results": [{"id": "q1", "decision": "answer"}, {"id": "q2", "decision": "answer"}]},
            {"results": [{"id": "q1", "decision": "answer"}, {"id": "q2", "decision": "refuse"}]},
        ]

        summary = stability_summary(runs, questions, 2)

        self.assertEqual(summary["stable_count"], 1)
        self.assertEqual(summary["unstable_questions"][0]["id"], "q2")
        self.assertEqual(summary["unstable_questions"][0]["decisions"], ["answer", "refuse"])

    def test_attempted_and_completed_accuracy_keep_failures_separate(self) -> None:
        questions = [
            {"id": "q1", "expected_behavior": "answer"},
            {"id": "q2", "expected_behavior": "refuse"},
        ]
        results = [
            {
                "id": "q1", "expected_behavior": "answer", "expected_source": ["source.md"],
                "decision": "answer", "retrieval_hit": True, "mrr": 1.0,
                "retrieved_context": [{"rerank_score": 0.9}],
                "timings_ms": {"retrieve": 1, "rerank": 2, "synthesize": 3, "total": 6},
            },
            {
                "id": "q2", "expected_behavior": "refuse", "expected_source": [],
                "error": "provider unavailable",
            },
        ]

        metrics = run_metrics(results, questions)

        self.assertEqual(metrics["attempted"], 2)
        self.assertEqual(metrics["failed"], 1)
        self.assertEqual(metrics["correct_over_all_attempted"], {"correct": 1, "denominator": 2, "percentage": 50.0})
        self.assertEqual(metrics["completed_accuracy"], {"correct": 1, "denominator": 1, "percentage": 100.0})
