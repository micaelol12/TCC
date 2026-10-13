import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from app.environment import load_environment


class EnvironmentTests(unittest.TestCase):
    def test_reads_root_env_with_quoted_values(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            (root / ".env").write_text('TYPESAFE_API_KEY="test root key"\nMARITACA_API_KEY=test-maritaca\n', encoding="utf-8")
            load_environment(root)
            self.assertEqual(os.environ["TYPESAFE_API_KEY"], "test root key")
            self.assertEqual(os.environ["MARITACA_API_KEY"], "test-maritaca")

    def test_process_then_api_then_root_precedence(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"TYPESAFE_API_KEY": "process-key"}, clear=True):
            root = Path(directory)
            api = root / "app" / "api"
            api.mkdir(parents=True)
            (root / ".env").write_text("TYPESAFE_API_KEY=root-key\nMARITACA_API_KEY=root-maritaca\nMAX_CHARS=60000\n", encoding="utf-8")
            (api / ".env").write_text("TYPESAFE_API_KEY=api-key\nMARITACA_API_KEY=api-maritaca\n", encoding="utf-8")
            load_environment(root)
            self.assertEqual(os.environ["TYPESAFE_API_KEY"], "process-key")
            self.assertEqual(os.environ["MARITACA_API_KEY"], "api-maritaca")
            self.assertEqual(os.environ["MAX_CHARS"], "60000")

    def test_missing_files_are_allowed(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            load_environment(Path(directory))
            self.assertNotIn("TYPESAFE_API_KEY", os.environ)


if __name__ == "__main__":
    unittest.main()
