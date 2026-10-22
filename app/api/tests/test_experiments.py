import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
import importlib
import json
import os
from pathlib import Path
import random
import sqlite3
from statistics import mean
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.main import app
from app.environment import load_environment
from app.settings import Settings
from app.lab_credentials import set_key, sessions, lock
from app.experiment_config import ExperimentConfig, ExperimentOverrides, config_hash, resolve_config
from app.pipeline.aggregation import aggregate
from app.pipeline.segmentation import split_text
from app.pipeline.strategies import classify_chunk
from app.pipeline.domain import motivos_fallback
from test_pipeline import FakeJev, FakeLlm, answers, llm_payload, TEXT, AXES
from test_reports import report_payload

analyze_route = importlib.import_module('app.routes.analyze')
reports_route = importlib.import_module('app.routes.reports')


def lab_settings(**changes):
    with patch.dict(os.environ, {}, clear=True):
        return Settings(app_env='lab', experimental_config_enabled=True, typesafe_key='test-secret-typesafe',
                        maritaca_key='test-secret-maritaca', **changes)


class SettingsTests(unittest.TestCase):
    def test_validates_environment_without_leaking_values(self):
        for variable, value in [('CHUNK_TOKENS', 'private-bad-value'), ('JEV_LEVEL_CONFIDENCE_MIN', 'nan'),
                                ('BOOTSTRAP_SAMPLES', '1'), ('CONCURRENT_REQUESTS', '0'), ('EXPERIMENTAL_CONFIG_ENABLED', 'yes')]:
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: value}, clear=True):
                with self.assertRaises(ValueError) as raised:
                    Settings()
                self.assertIn(variable, str(raised.exception))
                self.assertNotIn('private-bad-value', str(raised.exception))
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'APP_ENV=lab'):
                Settings(app_env='production', experimental_config_enabled=True)
        self.assertNotIn('test-secret', repr(lab_settings()))

    def test_lab_file_precedence_and_database_isolation(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, {'APP_ENV': 'lab', 'CHUNK_TOKENS': '800'}, clear=True):
            root = Path(directory)
            api = root / 'app' / 'api'
            api.mkdir(parents=True)
            (root / '.env').write_text('MARITACA_API_KEY=root-key\n', encoding='utf-8')
            (api / '.env').write_text('MARITACA_API_KEY=normal-key\nREPORTS_DB_PATH=normal.sqlite3\n', encoding='utf-8')
            (api / '.env.lab').write_text('CHUNK_TOKENS=400\nMARITACA_API_KEY=lab-key\nEXPERIMENTAL_CONFIG_ENABLED=true\n', encoding='utf-8')
            load_environment(root)
            settings = Settings()
            self.assertEqual(settings.chunk_tokens, 800)
            self.assertEqual(settings.maritaca_key, '')
            self.assertNotIn('MARITACA_API_KEY', os.environ)
            self.assertTrue(settings.reports_db_path.endswith('reports-lab.sqlite3'))


class AlgorithmTests(unittest.IsolatedAsyncioTestCase):
    def test_all_thresholds_use_strict_less_than(self):
        config = ExperimentConfig(relevance_margin_min=0.7, level_confidence_min=0.8, direction_margin_min=0.3).jev_config()
        decision = {'margem_relevancia': 0.7, 'confianca_nivel': 0.8, 'margem_direcao': 0.3, 'relevante': True, 'nivel': 1}
        self.assertEqual(motivos_fallback(decision, config), [])
        for name, reason in [('margem_relevancia', 'relevancia_ambigua'), ('confianca_nivel', 'baixa_confianca_nivel'), ('margem_direcao', 'direcao_ambigua')]:
            self.assertEqual(motivos_fallback({**decision, name: decision[name] - 0.01}, config), [reason])

    async def test_authentication_errors_do_not_retry_or_expose_provider_messages(self):
        class AuthenticationError(Exception):
            status_code = 401
        llm = SimpleNamespace(responses=SimpleNamespace(parse=AsyncMock(side_effect=AuthenticationError('private-provider-key'))))
        settings = lab_settings()
        result, _, _ = await classify_chunk(TEXT, 'high', None, None, llm, settings, settings.algorithm_defaults())
        self.assertEqual(llm.responses.parse.await_count, 1)
        self.assertEqual(result['economic']['reason'], ['falha_autenticacao_llm'])
        jev = SimpleNamespace(system_one=AsyncMock(side_effect=AuthenticationError('private-provider-key')))
        result, _, _ = await classify_chunk(TEXT, 'low', jev, {}, None, settings, settings.algorithm_defaults())
        self.assertEqual(result['economic']['reason'], ['falha_autenticacao_jev'])
        self.assertNotIn('private-provider-key', json.dumps(result))

    async def test_concurrent_thresholds_and_models_are_independent(self):
        settings = lab_settings(allowed_llm_models=('sabia-4', 'test-model'))
        loose = resolve_config(settings, ExperimentOverrides(level_confidence_min=0.3))
        strict = resolve_config(settings, ExperimentOverrides(level_confidence_min=0.9, llm_model='test-model'))
        first_llm, second_llm = FakeLlm(llm_payload()), FakeLlm(llm_payload())
        results = await asyncio.gather(
            classify_chunk(TEXT, 'medium', FakeJev({'answers': answers(0.6)}), {}, first_llm, settings, loose),
            classify_chunk(TEXT, 'medium', FakeJev({'answers': answers(0.6)}), {}, second_llm, settings, strict))
        self.assertEqual([item[1]['llm'] for item in results], [0, 1])
        self.assertEqual(first_llm.calls, 0)
        self.assertEqual(second_llm.calls, 1)
        self.assertEqual(settings.level_confidence_min, 0.5)
        high_llm = FakeLlm(llm_payload())
        high = await classify_chunk(TEXT, 'high', None, None, high_llm, settings, strict)
        self.assertEqual(high[1], {'jev': 0, 'llm': 1})
        with self.assertRaises(ValidationError):
            strict.level_confidence_min = 0.1

    def test_segmentation_bootstrap_and_sufficiency(self):
        text = 'Ação pública, educação e cooperação 😀. ' * 60
        smaller, _ = split_text(text, max_tokens=12000, chunk_tokens=100)
        larger, _ = split_text(text, max_tokens=12000, chunk_tokens=600)
        self.assertGreater(len(smaller), len(larger))
        self.assertEqual(''.join(smaller), text)
        rows = [{axis: {'relevante': True, 'nivel': level, 'method': 'jev', 'reason': [], 'quote': None} for axis in AXES} for level in (-2, 1, 2)]
        baseline = aggregate(rows, 3)[0]
        rng = random.Random(42)
        samples = sorted(mean(rng.choices([0, 75, 100], k=3)) for _ in range(2000))
        self.assertEqual(baseline.ci95, (samples[49], samples[1949]))
        config = ExperimentConfig(min_valid_chunks=2, bootstrap_samples=200, bootstrap_seed=11)
        changed = aggregate(rows, 3, config)[0]
        self.assertEqual(changed.pole_a, baseline.pole_a)
        self.assertTrue(changed.sufficient_evidence)
        self.assertNotIn('evidencia_limitada', changed.reason_codes)
        self.assertEqual(changed, aggregate(rows, 3, config)[0])
        self.assertIsNone(aggregate(rows[:1], 1, config)[0].ci95)


class ExperimentHttpTests(unittest.TestCase):
    def setUp(self):
        self.settings = lab_settings(allowed_jev_models=('jev-1.13.0', 'jev-test'), allowed_llm_models=('sabia-4', 'llm-test'))
        self.settings_patch = patch.object(analyze_route, 'settings', self.settings)
        self.settings_patch.start()
        analyze_route.recent_requests.clear()
        analyze_route.daily['calls'] = 0
        self.jev = FakeJev({'answers': answers(), 'model': 'jev-test'})
        self.jev.aclose = AsyncMock()
        self.llm = FakeLlm(llm_payload())
        self.llm.close = AsyncMock()
        self.factories = [patch.object(analyze_route, 'jev_client', return_value=self.jev),
                          patch.object(analyze_route, 'jev_questions', return_value={}),
                          patch.object(analyze_route, 'llm_client', return_value=self.llm)]
        self.mocks = [factory.start() for factory in self.factories]
        self.token = set_key(None, 'typesafe', 'test-secret-typesafe')
        set_key(self.token, 'maritaca', 'test-secret-maritaca')
        self.client = TestClient(app, headers={'X-Lab-Session': self.token})

    def tearDown(self):
        self.client.close()
        with lock:
            sessions.pop(self.token, None)
        for factory in self.factories:
            factory.stop()
        self.settings_patch.stop()

    def test_invalid_configs_and_disabled_lab_call_no_providers(self):
        for config in ({'chunk_tokens': True}, {'chunk_tokens': 99}, {'chunk_tokens': None},
                       {'bootstrap_samples': 10001}, {'relevance_margin_min': 1.01},
                       {'llm_model': 'unknown'}, {'min_valid_chunks': 21}, {'MARITACA_API_KEY': 'private-key'}):
            with self.subTest(config=config):
                response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'medium', 'experiment_config': config})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('private-key', response.text)
        with patch.object(analyze_route, 'settings', replace(self.settings, app_env='production', experimental_config_enabled=False)):
            denied = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'low', 'experiment_config': {}})
            self.assertEqual(denied.status_code, 403)
        for factory in self.mocks:
            factory.assert_not_called()
        self.assertEqual(analyze_route.daily['calls'], 0)

    def test_capabilities_and_results_are_public_snapshots(self):
        caps = self.client.get('/api/capabilities')
        self.assertTrue(caps.json()['experimental']['enabled'])
        self.assertNotIn('test-secret', caps.text)
        response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'low', 'experiment_config': {'jev_model': 'jev-test', 'min_valid_chunks': 1}})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result['effective_config']['jev_model'], 'jev-test')
        self.assertTrue(result['axes'][0]['sufficient_evidence'])
        self.assertEqual(result['config_hash'], config_hash(ExperimentConfig.model_validate(result['effective_config'])))
        self.assertEqual(result['environment'], 'lab')
        self.mocks[0].assert_called_once_with('test-secret-typesafe', 'jev-test')
        self.assertNotIn('test-secret', response.text)

    def test_two_http_requests_preserve_their_own_configuration(self):
        configs = [{'chunk_tokens': 100, 'min_valid_chunks': 1}, {'chunk_tokens': 600, 'min_valid_chunks': 16}]
        with ThreadPoolExecutor(max_workers=2) as workers:
            responses = list(workers.map(lambda config: self.client.post('/api/analyze', json={
                'text': TEXT, 'processing_level': 'low', 'experiment_config': config}), configs))
        for response, expected in zip(responses, configs):
            self.assertEqual(response.status_code, 200, response.text)
            for name, value in expected.items():
                self.assertEqual(response.json()['effective_config'][name], value)
        self.assertNotEqual(responses[0].json()['config_hash'], responses[1].json()['config_hash'])

    def test_max_chunks_and_budget_still_apply(self):
        settings = replace(self.settings, max_chunks=1, min_valid_chunks=1)
        with patch.object(analyze_route, 'settings', settings):
            response = self.client.post('/api/analyze', json={'text': TEXT * 50, 'processing_level': 'low', 'experiment_config': {'chunk_tokens': 100}})
            self.assertEqual(response.status_code, 413)
            self.mocks[0].assert_not_called()
        with patch.object(analyze_route, 'settings', replace(self.settings, daily_calls=1)):
            response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'medium', 'experiment_config': {}})
            self.assertEqual(response.status_code, 429)

    def test_report_retains_metadata_and_rejects_tampering_or_wrong_environment(self):
        payload = report_payload()
        config = self.settings.algorithm_defaults()
        payload['analysis'].update(effective_config=config.model_dump(), config_version='1',
            config_hash=config_hash(config, payload['analysis']['pipeline_version']), environment='lab')
        reports_route.recent_requests.clear()
        with TemporaryDirectory() as directory:
            database = str(Path(directory) / 'lab.sqlite3')
            with patch.object(reports_route, 'settings', replace(self.settings, reports_db_path=database)):
                response = self.client.post('/api/reports', json=payload)
                self.assertEqual(response.status_code, 201, response.text)
                with closing(sqlite3.connect(database)) as connection:
                    saved = json.loads(connection.execute('SELECT analysis_json FROM classification_reports').fetchone()[0])
                self.assertEqual(saved, payload['analysis'])
                self.assertNotIn('test-secret', json.dumps(saved))
                payload['analysis']['config_hash'] = '0' * 64
                self.assertEqual(self.client.post('/api/reports', json=payload).status_code, 422)
                payload['analysis']['config_hash'] = config_hash(config, payload['analysis']['pipeline_version'])
            with patch.object(reports_route, 'settings', replace(self.settings, app_env='production', experimental_config_enabled=False)):
                self.assertEqual(self.client.post('/api/reports', json=payload).status_code, 422)


if __name__ == '__main__':
    unittest.main()
