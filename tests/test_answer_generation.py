"""Unit tests for grounded answer synthesis through the OpenAI Responses API."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException


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
        response = SimpleNamespace(output_text="Revenue grew 15% quarter-over-quarter (Source: Chunk ID 12).")

        with patch("app.router.answer_client.responses.create", new=AsyncMock(return_value=response)) as create:
            result = await _synthesize_answer("How did revenue change?", context)

        self.assertEqual(result.answer, response.output_text)
        self.assertEqual(result.retrieved_context, context)
        create.assert_awaited_once()
        kwargs = create.await_args.kwargs
        self.assertEqual(kwargs["model"], settings.ANSWER_MODEL)
        self.assertEqual(kwargs["input"], "How did revenue change?")
        self.assertEqual(kwargs["max_output_tokens"], 2048)
        self.assertFalse(kwargs["store"])
        self.assertIn("ONLY", kwargs["instructions"])
        self.assertIn("Chunk ID: 12", kwargs["instructions"])

    async def test_synthesize_answer_returns_insufficient_information_for_empty_retrieval(self) -> None:
        with patch("app.router.answer_client.responses.create", new=AsyncMock()) as create:
            result = await _synthesize_answer("How did revenue change?", [])

        self.assertIn("could not find", result.answer)
        self.assertEqual(result.retrieved_context, [])
        create.assert_not_awaited()

    async def test_synthesize_answer_translates_openai_failure_to_bad_gateway(self) -> None:
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

        with patch(
            "app.router.answer_client.responses.create",
            new=AsyncMock(side_effect=RuntimeError("service unavailable")),
        ):
            with self.assertRaises(HTTPException) as raised:
                await _synthesize_answer("How did revenue change?", context)

        self.assertEqual(raised.exception.status_code, 502)
        self.assertIn("OpenAI answer synthesis failure", raised.exception.detail)
