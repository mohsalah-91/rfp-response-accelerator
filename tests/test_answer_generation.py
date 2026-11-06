"""Unit tests for structured, grounded answer synthesis."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi import HTTPException
from openai import APIError
from openai.types.responses import ParsedResponse
from pydantic import ValidationError


os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("COHERE_API_KEY", "test-cohere-key")

from app.answer_models import GroundedAnswer
from app.config import settings
from app.main import app
from app.router import SearchResultResponse, _synthesize_answer


class AnswerGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_answer_uses_parsed_responses_api_and_preserves_fields(self) -> None:
        expected = self._answer()
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(return_value=self._response(expected))) as parse:
            result = await _synthesize_answer("How did revenue change?", self._context())

        self.assertEqual(result.answer, expected.answer)
        self.assertEqual(result.decision, "answer")
        self.assertEqual(result.citations, [12])
        self.assertFalse(result.needs_sme_review)
        self.assertEqual(result.reason, expected.reason)
        self.assertEqual(result.retrieved_context, self._context())
        self.assertEqual(result.model_used, settings.ANSWER_MODEL)
        kwargs = parse.await_args.kwargs
        self.assertEqual(kwargs["model"], settings.ANSWER_MODEL)
        self.assertIs(kwargs["text_format"], GroundedAnswer)
        self.assertEqual(kwargs["max_output_tokens"], 4096)
        self.assertFalse(kwargs["store"])
        answer_input = json.loads(kwargs["input"])
        self.assertEqual(answer_input["question"], "How did revenue change?")
        self.assertEqual(answer_input["retrieved_evidence"][0]["chunk_id"], 12)
        self.assertIn("untrusted data", kwargs["instructions"])
        self.assertIn("answer_negative", kwargs["instructions"])
        self.assertIn("Documented product-specific exceptions are not contradictions", kwargs["instructions"])
        self.assertIn("evidence does not provide the identifier", kwargs["instructions"])
        self.assertNotIn("Revenue grew", kwargs["instructions"])

    async def test_answer_negative_requires_and_returns_evidence(self) -> None:
        expected = self._answer(decision="answer_negative", answer="No, this deployment is unsupported.")
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(return_value=self._response(expected))):
            result = await _synthesize_answer("Is this supported?", self._context())
        self.assertEqual(result.decision, "answer_negative")
        self.assertEqual(result.citations, [12])

    async def test_documented_scoped_exception_can_remain_a_complete_answer(self) -> None:
        expected = self._answer(
            answer="TLS 1.2 is accepted only for named legacy integrations requested in writing.",
            reason="The evidence documents the limited legacy-integration exception.",
        )
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(return_value=self._response(expected))):
            result = await _synthesize_answer("Are there any protocol exceptions?", self._context())
        self.assertEqual(result.decision, "answer")
        self.assertFalse(result.needs_sme_review)

    async def test_missing_certification_identifier_is_returned_as_insufficient_evidence(self) -> None:
        expected = self._answer(
            decision="answer_partial",
            answer="The evidence does not provide a certification package identifier.",
            needs_sme_review=True,
            reason="The retrieved evidence does not provide the requested identifier.",
        )
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(return_value=self._response(expected))):
            result = await _synthesize_answer("What is the package identifier?", self._context())
        self.assertEqual(result.decision, "answer_partial")
        self.assertTrue(result.needs_sme_review)

    async def test_empty_retrieval_is_deterministic_and_does_not_call_openai(self) -> None:
        with patch("app.router.answer_client.responses.parse", new=AsyncMock()) as parse:
            result = await _synthesize_answer("How did revenue change?", [])
        self.assertEqual(result.decision, "answer_partial")
        self.assertEqual(result.citations, [])
        self.assertTrue(result.needs_sme_review)
        self.assertIn("No supporting evidence", result.answer)
        self.assertEqual(result.retrieved_context, [])
        parse.assert_not_awaited()

    async def test_http_response_preserves_and_extends_contract(self) -> None:
        expected = self._answer()
        with patch("app.router._hybrid_search_and_rerank", new=AsyncMock(return_value=self._context())), patch(
            "app.router.answer_client.responses.parse", new=AsyncMock(return_value=self._response(expected))
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.post("/documents/answer", json={"query": "How did revenue change?"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["query"], "How did revenue change?")
        self.assertEqual(body["answer"], expected.answer)
        self.assertEqual(body["decision"], "answer")
        self.assertEqual(body["citations"], [12])
        self.assertFalse(body["needs_sme_review"])
        self.assertEqual(body["reason"], expected.reason)
        self.assertEqual(body["model_used"], settings.ANSWER_MODEL)
        self.assertEqual(body["retrieved_context"][0]["id"], 12)

    async def test_rejects_invalid_citation_ids(self) -> None:
        await self._assert_invalid(self._answer(citations=[999]), "OpenAI returned citations outside the retrieved evidence.")

    async def test_rejects_missing_citations_for_substantive_answers(self) -> None:
        await self._assert_invalid(self._answer(citations=[]), "OpenAI returned a substantive answer without citations.")

    async def test_rejects_incomplete_output(self) -> None:
        await self._assert_invalid_response(self._response(self._answer(), status="in_progress"), "OpenAI returned an incomplete answer response.")

    async def test_rejects_provider_refusal_without_application_decision(self) -> None:
        refusal = SimpleNamespace(type="refusal", refusal="blocked")
        response = self._response(None, output=[SimpleNamespace(content=[refusal])])
        await self._assert_invalid_response(response, "OpenAI declined to generate an answer response.")

    async def test_rejects_missing_parsed_output(self) -> None:
        await self._assert_invalid_response(self._response(None), "OpenAI returned no structured answer response.")

    async def test_rejects_empty_answer_or_reason(self) -> None:
        await self._assert_invalid(self._answer(answer="  "), "OpenAI returned an invalid structured answer response.")
        await self._assert_invalid(self._answer(reason="\n"), "OpenAI returned an invalid structured answer response.")

    async def test_rejects_invalid_review_flags_for_insufficient_evidence(self) -> None:
        await self._assert_invalid(self._answer(decision="answer_partial", needs_sme_review=False), "OpenAI returned inconsistent SME review guidance.")
        await self._assert_invalid(self._answer(decision="refuse", needs_sme_review=False), "OpenAI returned inconsistent SME review guidance.")

    async def test_rejects_schema_validation_failures(self) -> None:
        invalid = {"decision": "not-a-decision", "answer": "text", "citations": [12], "needs_sme_review": False, "reason": "reason"}
        with self.assertRaises(ValidationError):
            GroundedAnswer.model_validate(invalid)
        await self._assert_invalid_response(self._response(invalid), "OpenAI returned an invalid structured answer response.")

        try:
            GroundedAnswer.model_validate(invalid)
        except ValidationError as error:
            validation_error = error
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(side_effect=validation_error)):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())
        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "OpenAI returned an invalid structured answer response.")

    async def test_openai_api_errors_are_sanitized(self) -> None:
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(side_effect=APIError("service unavailable", request=MagicMock(), body=None))):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())
        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "OpenAI answer synthesis is currently unavailable.")

    def test_installed_sdk_parsed_response_type_exposes_output_parsed(self) -> None:
        self.assertTrue(hasattr(ParsedResponse, "output_parsed"))

    async def _assert_invalid(self, parsed, detail: str) -> None:
        await self._assert_invalid_response(self._response(parsed), detail)

    async def _assert_invalid_response(self, response, detail: str) -> None:
        with patch("app.router.answer_client.responses.parse", new=AsyncMock(return_value=response)):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())
        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, detail)

    @staticmethod
    def _response(parsed, status="completed", output=None):
        return SimpleNamespace(status=status, output_parsed=parsed, output=output or [])

    @staticmethod
    def _answer(**overrides) -> GroundedAnswer:
        values = {"decision": "answer", "answer": "Revenue grew 15% quarter-over-quarter.", "citations": [12], "needs_sme_review": False, "reason": "The retrieved financial report states the quarterly growth."}
        values.update(overrides)
        return GroundedAnswer(**values)

    @staticmethod
    def _context():
        return [SearchResultResponse(id=12, title="Q2 Financial Report", content="Revenue grew by 15% quarter-over-quarter.", chunk_index=0, rrf_score=0.032, rerank_score=0.91)]
