"""Tests for the public static RFP response interface."""

import os
import unittest

import httpx


os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("COHERE_API_KEY", "test-cohere-key")

from app.main import app


class UserInterfaceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_ui_and_static_assets_are_served(self) -> None:
        page = await self.client.get("/ui")
        stylesheet = await self.client.get("/ui/static/styles.css")
        script = await self.client.get("/ui/static/app.js")

        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page.headers["content-type"])
        self.assertIn("RFP Response Accelerator", page.text)
        self.assertIn('src="/ui/static/app.js"', page.text)
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn("text/css", stylesheet.headers["content-type"])
        self.assertEqual(script.status_code, 200)
        self.assertIn("javascript", script.headers["content-type"])
        self.assertIn('fetch("/documents/answer"', script.text)
        self.assertIn('fetch("/documents/rfp-questions"', script.text)
        self.assertIn("textContent", script.text)
        self.assertIn('role="tablist"', page.text)
        self.assertIn("Single question", page.text)
        self.assertIn("RFP batch", page.text)
        self.assertIn("Process RFP", page.text)
        self.assertIn("Download response document", page.text)
        self.assertIn('id="decision-rail"', page.text)
        self.assertIn("answer_negative", page.text)
        self.assertIn("Answered: The evidence supports a direct, complete answer.", page.text)
        self.assertIn('aria-label="Answered decision"', page.text)
        self.assertIn('aria-label="Documented no decision"', page.text)
        self.assertIn("Cohere rerank score on a fixed zero to one scale", script.text)
        self.assertIn("rerank_wait", script.text)
        self.assertIn("citation-chip", script.text)
        self.assertIn("metadata-primary-row", page.text)
        self.assertIn("DRAFT — Internal RFP Review Packet", script.text)
        self.assertIn("Safe error information", script.text)
        self.assertIn("parseBatchQuestions", script.text)
        self.assertIn("normalizeQuestionText", script.text)
        self.assertIn("rowKey", script.text)
        self.assertIn("batchResponses = questions.map", script.text)
        self.assertIn("markdownFence", script.text)
        self.assertIn("Cited source ${sourceIndex + 1}", script.text)
        self.assertIn("Paste plain questions", page.text)
        self.assertIn("batchDecisionLabels", script.text)
        self.assertIn("Documented no", script.text)
        self.assertIn("Route by policy", script.text)
        self.assertIn("Insufficient evidence", script.text)
        self.assertIn("Processing error", script.text)
        self.assertIn("decision-rail-label", script.text)

    async def test_existing_public_routes_remain_available(self) -> None:
        root = await self.client.get("/")
        health = await self.client.get("/health")
        docs = await self.client.get("/docs")

        self.assertEqual(root.status_code, 200)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(docs.status_code, 200)

    async def test_rfp_questions_excludes_evaluation_labels(self) -> None:
        response = await self.client.get("/documents/rfp-questions")

        self.assertEqual(response.status_code, 200)
        questions = response.json()
        self.assertEqual(len(questions), 15)
        self.assertTrue(all("expected_behavior" not in question for question in questions))
        self.assertTrue(all(set(question) == {"id", "section", "question"} for question in questions))
