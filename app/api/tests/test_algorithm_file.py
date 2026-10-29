import importlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.algorithm_file import DEFAULT_CONFIG_PATH, load_algorithm_file
from app.experiment_config import ExperimentConfig, config_hash
from app.main import app
from app.polarity import ESCALA_5_NIVEIS
from app.settings import Settings
from test_pipeline import FakeLlm, TEXT, llm_payload

route = importlib.import_module('app.routes.analyze')


class AlgorithmFileTests(unittest.TestCase):
    def setUp(self):
        windows = {name: os.environ[name] for name in ('APPDATA', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'TEMP', 'TMP', 'SYSTEMROOT') if name in os.environ}
        self.environment = patch.dict(os.environ, windows, clear=True)
        self.environment.start()
        self.directory = TemporaryDirectory()
        self.path = Path(self.directory.name) / 'parameters.json'

    def tearDown(self):
        self.directory.cleanup()
        self.environment.stop()

    def write(self, **changes):
        data = {**ExperimentConfig().model_dump(mode='json'), **changes}
        self.path.write_text(json.dumps(data), encoding='utf-8-sig')
        return data

    def test_official_file_covers_every_lab_parameter_and_is_independent_of_cwd(self):
        data = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding='utf-8'))
        self.assertEqual(set(data), set(ExperimentConfig.model_fields))
        self.assertEqual(Settings().algorithm_defaults(), load_algorithm_file('analysis-config.json'))
        # A separate Lab launch retains its defaults rather than reading the official file.
        with patch('app.settings.load_algorithm_file', side_effect=AssertionError('official file read')):
            self.assertEqual(Settings(app_env='lab').chunk_strategy, 'sentencas')

    def test_all_file_parameters_and_environment_precedence(self):
        data = self.write(escala=ESCALA_5_NIVEIS.model_dump(mode='json'), chunk_strategy='sentencas',
            primitiva_polaridade='choice', regra_decisao='polo_primeiro', chunk_tokens=350,
            relevance_margin_min=.7, level_confidence_min=.65, direction_margin_min=.3,
            min_valid_chunks=2, bootstrap_samples=300, bootstrap_seed=71,
            jev_model='jev-test', llm_model='sabiazinho-4', semantic_evidence_check=True,
            jev_evidence_search=True, evidence_existence_min=.8)
        with patch.dict(os.environ, {'ALGORITHM_CONFIG_PATH': str(self.path)}):
            settings = Settings()
            self.assertEqual(settings.algorithm_defaults().model_dump(mode='json'), data)
            with patch.dict(os.environ, {'CHUNK_TOKENS': '450', 'SEMANTIC_EVIDENCE_CHECK': 'false'}):
                overridden = Settings()
            self.assertEqual(overridden.chunk_tokens, 450)
            self.assertFalse(overridden.semantic_evidence_check)
            self.assertEqual(overridden.escala, settings.escala)
        self.write(chunk_tokens=700)
        self.assertEqual(settings.chunk_tokens, 350)  # fixed until a new startup
        self.assertEqual(Settings(algorithm_config_path=str(self.path)).chunk_tokens, 700)

    def test_invalid_files_fail_closed_without_exposing_contents(self):
        for content in ('{', '[]', '{"MARITACA_API_KEY":"private-key"}',
                        '{"chunk_tokens":true}', '{"chunk_tokens":null}',
                        '{"evidence_existence_min":1.2}', '{"semantic_evidence_check":"true"}',
                        '{"escala":{"id":"invalid"}}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'ALGORITHM_CONFIG_PATH') as error:
                    Settings(algorithm_config_path=str(self.path))
                self.assertNotIn('private-key', str(error.exception))
        with self.assertRaises(ValueError):
            Settings(algorithm_config_path=str(self.path.with_name('missing.json')))
        self.write(chunk_tokens=1000)
        with self.assertRaisesRegex(ValueError, 'MAX_TOKENS'):
            Settings(algorithm_config_path=str(self.path), max_tokens=500)
        self.write(llm_model='sabiazinho-4')
        with self.assertRaisesRegex(ValueError, 'modelos permitidos'):
            Settings(algorithm_config_path=str(self.path), allowed_llm_models=('sabia-4',))

    def test_official_http_uses_file_model_scale_and_hash_without_client_overrides(self):
        data = self.write(escala=ESCALA_5_NIVEIS.model_dump(mode='json'), chunk_strategy='sentencas',
            llm_model='gemini-3.1-flash-lite', chunk_tokens=300, min_valid_chunks=1,
            bootstrap_samples=200, bootstrap_seed=17)
        settings = Settings(app_env='production', algorithm_config_path=str(self.path), gemini_key='test-key')
        llm = FakeLlm(llm_payload())
        llm.close = AsyncMock()
        route.recent_requests.clear()
        route.daily['calls'] = 0
        with patch.object(route, 'settings', settings), patch.object(route, 'gemini_client', return_value=llm) as factory, \
             patch.object(route, 'llm_client') as maritaca, TestClient(app) as client:
            caps = client.get('/api/capabilities').json()
            self.assertEqual(caps['analysis_defaults'], data)
            self.assertEqual(caps['experimental'], {'enabled': False})
            self.assertEqual(caps['modes'], {'low': False, 'medium': False, 'high': True})
            self.assertNotIn('test-key', json.dumps(caps))
            response = client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'high'})
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
            self.assertEqual(result['effective_config'], data)
            self.assertEqual(result['config_hash'], config_hash(settings.algorithm_defaults()))
            self.assertEqual(result['escala_hash'], settings.escala.hash)
            self.assertNotIn('lab_execution_id', result)
            factory.assert_called_once_with('test-key', settings.timeout_seconds)
            maritaca.assert_not_called()
            self.assertEqual(client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'high',
                'experiment_config': {'chunk_tokens': 500}}).status_code, 403)

    def test_modes_require_the_configured_provider_and_semantic_checker(self):
        self.write(llm_model='gemini-3.1-flash-lite', semantic_evidence_check=True)
        for keys, high in (({'maritaca_key': 'key'}, False), ({'gemini_key': 'key'}, False),
                           ({'gemini_key': 'key', 'typesafe_key': 'key'}, True)):
            with self.subTest(keys=list(keys)):
                settings = Settings(algorithm_config_path=str(self.path), **keys)
                with patch.object(route, 'settings', settings), TestClient(app) as client:
                    self.assertIs(client.get('/api/capabilities').json()['modes']['high'], high)
