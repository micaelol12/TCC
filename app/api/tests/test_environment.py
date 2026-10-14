import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from app.environment import load_environment
from app.settings import Settings


class EnvironmentTests(unittest.TestCase):
    def test_lab_ignores_provider_credentials_from_every_env_file(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {'APP_ENV': 'lab'}, clear=True):
            root = Path(directory)
            api = root / 'app' / 'api'
            api.mkdir(parents=True)
            for path in (root / '.env', api / '.env', api / '.env.lab'):
                path.write_text('TYPESAFE_API_KEY=server-typesafe\nMARITACA_API_KEY=server-maritaca\nGEMINI_API_KEY=server-gemini\nMAX_CHARS=50000\n', encoding='utf-8')
            load_environment(root)
            for name in ('TYPESAFE_API_KEY', 'MARITACA_API_KEY', 'GEMINI_API_KEY'):
                self.assertNotIn(name, os.environ)
            self.assertEqual(os.environ['MAX_CHARS'], '50000')

    def test_lab_settings_discard_process_and_explicit_credentials(self):
        with patch.dict(os.environ, {'APP_ENV': 'lab', 'TYPESAFE_API_KEY': 'server-typesafe',
                                    'MARITACA_API_KEY': 'server-maritaca', 'GEMINI_API_KEY': 'server-gemini'}, clear=True):
            for settings in (Settings(), Settings(typesafe_key='explicit', maritaca_key='explicit', gemini_key='explicit')):
                self.assertEqual((settings.typesafe_key, settings.maritaca_key, settings.gemini_key), ('', '', ''))

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
