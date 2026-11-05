"""Import regressions for startup paths that must avoid tokenizer initialization."""

import os
import subprocess
import sys
import unittest


class ImportRegressionTests(unittest.TestCase):
    def test_app_main_import_does_not_initialize_tiktoken(self) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
                "OPENAI_API_KEY": "test-openai-key",
                "COHERE_API_KEY": "test-cohere-key",
            }
        )
        script = (
            "import tiktoken\n"
            "def fail_if_called(*args, **kwargs):\n"
            "    raise AssertionError('tiktoken.get_encoding must not run during app import')\n"
            "tiktoken.get_encoding = fail_if_called\n"
            "import app.main\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            check=False,
            env=environment,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
