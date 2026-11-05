"""Unit tests for grounded answer synthesis through the OpenAI Responses API."""

import os
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from openai import APIError


os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("COHERE_API_KEY", "test-cohere-key")

from app.router import SearchResultResponse, _synthesize_answer
from app.config import settings


class AnswerGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_synthesize_answer_uses_responses_api_with_retrieved_evidence(self) -> None:
        context = [
            SearchResultResponse(
                id=12,
                title="Q2 Financial Report",
                content="Revenue grew by 15% quarter-over-quarter.",
                chunk_index=0,
                rrf_score=0.032,
                rerank_score=0.91,
            )
        ]
        response = SimpleNamespace(
            status="completed",
            output_text="Revenue grew 15% quarter-over-quarter (Source: Chunk ID 12).",
        )

        with patch("app.router.answer_client.responses.create", new=AsyncMock(return_value=response)) as create:
            result = await _synthesize_answer("How did revenue change?", context)

        self.assertEqual(result.answer, response.output_text)
        self.assertEqual(result.retrieved_context, context)
        create.assert_awaited_once()
        kwargs = create.await_args.kwargs
        self.assertEqual(kwargs["model"], settings.ANSWER_MODEL)
        answer_input = json.loads(kwargs["input"])
        self.assertEqual(answer_input["question"], "How did revenue change?")
        self.assertEqual(answer_input["retrieved_evidence"], [{
            "chunk_id": 12,
            "title": "Q2 Financial Report",
            "chunk_index": 0,
            "content": "Revenue grew by 15% quarter-over-quarter.",
        }])
        self.assertEqual(kwargs["max_output_tokens"], 4096)
        self.assertFalse(kwargs["store"])
        self.assertIn("ONLY", kwargs["instructions"])
        self.assertIn("untrusted data", kwargs["instructions"])
        self.assertNotIn("Revenue grew", kwargs["instructions"])

    async def test_synthesize_answer_returns_insufficient_information_for_empty_retrieval(self) -> None:
        with patch("app.router.answer_client.responses.create", new=AsyncMock()) as create:
            result = await _synthesize_answer("How did revenue change?", [])

        self.assertIn("could not find", result.answer)
        self.assertEqual(result.retrieved_context, [])
        create.assert_not_awaited()

    async def test_synthesize_answer_rejects_incomplete_response(self) -> None:
        with patch(
            "app.router.answer_client.responses.create",
            new=AsyncMock(return_value=SimpleNamespace(status="in_progress", output_text="Partial answer")),
        ):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "OpenAI returned an incomplete or empty answer response.")

    async def test_synthesize_answer_rejects_empty_response_output(self) -> None:
        with patch(
            "app.router.answer_client.responses.create",
            new=AsyncMock(return_value=SimpleNamespace(status="completed", output_text="")),
        ):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "OpenAI returned an incomplete or empty answer response.")

    async def test_synthesize_answer_rejects_whitespace_only_response_output(self) -> None:
        with patch(
            "app.router.answer_client.responses.create",
            new=AsyncMock(return_value=SimpleNamespace(status="completed", output_text="  \n\t  ")),
        ):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "OpenAI returned an incomplete or empty answer response.")

    async def test_synthesize_answer_translates_openai_api_error_to_bad_gateway(self) -> None:
        with patch(
            "app.router.answer_client.responses.create",
            new=AsyncMock(
                side_effect=APIError("service unavailable", request=MagicMock(), body=None)
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", self._context())

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "OpenAI answer synthesis is currently unavailable.")

    @staticmethod
    def _context():
        context = [
            SearchResultResponse(
                id=12,
                title="Q2 Financial Report",
                content="Revenue grew by 15% quarter-over-quarter.",
                chunk_index=0,
                rrf_score=0.032,
                rerank_score=0.91,
            )
        ]
        return context
