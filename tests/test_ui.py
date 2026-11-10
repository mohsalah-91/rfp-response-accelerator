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
        self.assertIn("textContent", script.text)

    async def test_existing_public_routes_remain_available(self) -> None:
        root = await self.client.get("/")
        health = await self.client.get("/health")
        docs = await self.client.get("/docs")

        self.assertEqual(root.status_code, 200)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(docs.status_code, 200)
