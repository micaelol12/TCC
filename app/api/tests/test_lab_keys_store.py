import asyncio
from contextlib import closing
from dataclasses import replace
import importlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.lab_credentials import sessions, lock
from app.lab_credentials import effective_keys
from starlette.requests import Request
from app.execution_store import recover_interrupted
from app.pipeline.gemini import GeminiClient
from app.pipeline.strategies import schema_for
from test_experiments import lab_settings
from test_pipeline import FakeLlm, llm_payload, TEXT, AXES

main_module = importlib.import_module('app.main')
route_module = importlib.import_module('app.routes.analyze')
key_module = importlib.import_module('app.routes.lab')


class LabKeysAndStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.database = str(Path(self.directory.name) / 'lab.sqlite3')
        self.settings = replace(lab_settings(), maritaca_key='', gemini_key='', reports_db_path=self.database)
        self.patches = [patch.object(module, 'settings', self.settings) for module in (main_module, route_module, key_module)]
        for item in self.patches:
            item.start()
        route_module.recent_requests.clear()
        route_module.daily['calls'] = 0
        with lock:
            sessions.clear()
        self.client = TestClient(app).__enter__()
        self.llm = FakeLlm(llm_payload())
        self.llm.close = AsyncMock()
        self.factories = [patch.object(route_module, 'llm_client', return_value=self.llm), patch.object(route_module, 'gemini_client', return_value=self.llm)]
        self.mocks = [item.start() for item in self.factories]

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in self.patches + self.factories:
            item.stop()
        with lock:
            sessions.clear()
        self.directory.cleanup()

    def key(self, provider, value, token=None):
        response = self.client.post('/api/lab/api-keys', json={'provider': provider, 'api_key': value}, headers={'X-Lab-Session': token} if token else {})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn(value, response.text)
        return response.json()['session_token']

    def analyze(self, token=None, model='sabiazinho-4'):
        return self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'high', 'experiment_config': {'llm_model': model}}, headers={'X-Lab-Session': token, 'X-Lab-Client': 'web'} if token else {})

    def rows(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute('SELECT * FROM lab_executions ORDER BY started_at')]

    def test_keys_release_models_and_isolate_sessions(self):
        initial = self.client.get('/api/capabilities').json()
        self.assertFalse(initial['modes']['high'])
        self.assertIn('sabiazinho-4', initial['experimental']['allowed_models']['llm'])
        self.assertIn('gemini-3.7-flash', initial['experimental']['allowed_models']['llm'])
        maritaca = self.key('maritaca', 'maritaca-secret-UNIQUE')
        gemini = self.key('gemini', 'gemini-secret-UNIQUE')
        first = self.client.get('/api/capabilities', headers={'X-Lab-Session': maritaca})
        second = self.client.get('/api/capabilities', headers={'X-Lab-Session': gemini})
        self.assertTrue(first.json()['experimental']['providers']['maritaca'])
        self.assertFalse(first.json()['experimental']['providers']['gemini'])
        self.assertEqual(second.json()['experimental']['defaults']['llm_model'], 'gemini-3.1-flash-lite')
        self.assertNotIn('secret-UNIQUE', first.text + second.text)
        self.assertEqual(self.analyze(maritaca).status_code, 200)
        self.mocks[0].assert_called_with('maritaca-secret-UNIQUE', self.settings.timeout_seconds)
        self.assertEqual(self.analyze(gemini, 'gemini-3.7-flash').status_code, 200)
        self.mocks[1].assert_called_with('gemini-secret-UNIQUE', self.settings.timeout_seconds)
        unavailable = self.analyze(maritaca, 'gemini-3.7-flash')
        self.assertEqual(unavailable.status_code, 503)
        rows = self.rows()
        self.assertEqual([row['status'] for row in rows], ['completed', 'completed', 'failed'])
        self.assertNotIn('secret-UNIQUE', json.dumps(rows))
        self.assertNotIn(maritaca, json.dumps(rows))
        self.assertNotIn(gemini, json.dumps(rows))
        self.assertEqual(json.loads(rows[1]['analysis_json'])['lab_execution_id'], rows[1]['execution_id'])

    def test_lab_never_falls_back_to_server_keys(self):
        server = SimpleNamespace(app_env='lab', typesafe_key='server-typesafe', maritaca_key='server-maritaca', gemini_key='server-gemini')
        request = Request({'type': 'http', 'headers': []})
        self.assertEqual(effective_keys(server, request), {'typesafe': '', 'maritaca': '', 'gemini': ''})
        for mode in ('low', 'medium', 'high'):
            response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': mode})
            self.assertEqual(response.status_code, 503)
            self.assertIn('API keys', response.json()['detail'])
        for factory in self.mocks:
            factory.assert_not_called()
        server.app_env = 'production'
        self.assertEqual(effective_keys(server, request), {'typesafe': 'server-typesafe', 'maritaca': 'server-maritaca', 'gemini': ''})

    def test_typesafe_registration_removal_reset_and_expiry_gate_modes(self):
        def modes(token=None):
            response = self.client.get('/api/capabilities', headers={'X-Lab-Session': token} if token else {})
            self.assertEqual(response.status_code, 200)
            return response.json()['modes']
        unavailable = {'low': False, 'medium': False, 'high': False}
        self.assertEqual(modes(), unavailable)
        token = self.key('typesafe', 'user-typesafe')
        self.assertEqual(modes(token), {'low': True, 'medium': False, 'high': False})
        self.key('maritaca', 'user-maritaca', token)
        self.assertEqual(modes(token), {'low': True, 'medium': True, 'high': True})
        self.assertEqual(modes(), unavailable)
        self.assertEqual(self.client.delete('/api/lab/api-keys/typesafe', headers={'X-Lab-Session': token}).status_code, 200)
        self.assertEqual(modes(token), {'low': False, 'medium': False, 'high': True})
        self.assertEqual(self.client.delete('/api/lab/session', headers={'X-Lab-Session': token}).status_code, 200)
        self.assertEqual(modes(), unavailable)
        self.assertEqual(self.analyze(token).status_code, 401)
        token = self.key('typesafe', 'user-typesafe')
        with lock:
            sessions[token].expires_at = 0
        self.assertEqual(self.client.get('/api/capabilities', headers={'X-Lab-Session': token}).status_code, 401)
        self.assertEqual(modes(), unavailable)

    def test_remove_expiry_and_invalid_or_nonlab_keys(self):
        token = self.key('gemini', 'test-gemini')
        self.assertEqual(self.client.delete('/api/lab/api-keys/gemini', headers={'X-Lab-Session': token}).status_code, 200)
        self.assertFalse(self.client.get('/api/capabilities', headers={'X-Lab-Session': token}).json()['experimental']['providers']['gemini'])
        with lock:
            sessions[token].expires_at = 0
        self.assertEqual(self.client.get('/api/capabilities', headers={'X-Lab-Session': token}).status_code, 401)
        self.assertEqual(self.analyze(token, 'gemini-3.1-flash-lite').status_code, 401)
        response = self.client.post('/api/lab/api-keys', json={'provider': 'gemini', 'api_key': 'private invalid key'})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('private invalid key', response.text)
        with patch.object(key_module, 'settings', replace(self.settings, app_env='production', experimental_config_enabled=False)):
            self.assertEqual(self.client.post('/api/lab/api-keys', json={'provider': 'gemini', 'api_key': 'a-key'}).status_code, 404)

    def test_every_attempt_is_recorded_without_extra_credentials(self):
        token = self.key('maritaca', 'private-provider-key')
        self.assertEqual(self.rows(), [])
        invalid = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'high', 'api_key': 'private-extra-key'})
        self.assertEqual(invalid.status_code, 422)
        with patch.object(route_module, 'classify_chunk', AsyncMock(side_effect=TimeoutError)):
            self.assertEqual(self.analyze(token).status_code, 504)
        with patch.object(route_module, 'classify_chunk', AsyncMock(side_effect=asyncio.CancelledError)):
            self.assertEqual(self.analyze(token).status_code, 499)
        self.assertEqual([row['error_code'] for row in self.rows()], ['invalid_request', 'timeout', 'cancelled'])
        self.assertTrue(self.rows()[1]['effective_config_json'])
        self.assertNotIn('private-', json.dumps(self.rows()))

    def test_database_failure_prevents_provider_call_and_recovers_pending_records(self):
        token = self.key('maritaca', 'test-key')
        with patch.object(main_module, 'begin_execution', side_effect=sqlite3.OperationalError):
            self.assertEqual(self.analyze(token).status_code, 503)
        self.mocks[0].assert_not_called()
        with patch.object(main_module, 'finish_execution', side_effect=sqlite3.OperationalError):
            self.assertEqual(self.analyze(token).status_code, 503)
        self.assertEqual(self.rows()[0]['status'], 'running')
        recover_interrupted(self.database)
        self.assertEqual(self.rows()[0]['status'], 'interrupted')

    def test_validation_rejections_and_provider_warnings_are_recorded(self):
        token = self.key('maritaca', 'test-key')
        self.llm.responses = SimpleNamespace(parse=AsyncMock(side_effect=httpx.HTTPStatusError('private-provider-key', request=httpx.Request('POST', 'https://example.test'), response=httpx.Response(401))))
        response = self.analyze(token)
        self.assertEqual(response.status_code, 200)
        row = self.rows()[0]
        self.assertEqual(row['status'], 'completed_with_warnings')
        self.assertNotIn('private-provider-key', json.dumps(row))
        self.assertEqual(self.llm.responses.parse.await_count, 1)

    def test_export_is_read_only_and_does_not_overwrite(self):
        token = self.key('maritaca', 'test-key')
        response = self.analyze(token)
        output = Path(self.directory.name) / 'executions.jsonl'
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'export_lab_executions.py'
        result = subprocess.run([sys.executable, str(script), '--database', self.database, '--output', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(data['analysis']['lab_execution_id'], response.json()['lab_execution_id'])
        self.assertEqual(data['effective_config']['llm_model'], 'sabiazinho-4')
        repeated = subprocess.run([sys.executable, str(script), '--database', self.database, '--output', str(output)], capture_output=True, text=True)
        self.assertNotEqual(repeated.returncode, 0)


class GeminiAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_contract_and_returned_model_version(self):
        captured = []
        async def serve(request):
            captured.append(request)
            return httpx.Response(200, json={'modelVersion': 'gemini-3.8-flash', 'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(llm_payload())}]}}]})
        client = GeminiClient('test-key', 10, transport=httpx.MockTransport(serve))
        try:
            result = await client.responses.parse(model='gemini-3.7-flash', input=TEXT, instructions='instruções', text_format=schema_for(list(AXES)))
            self.assertEqual(result.model, 'gemini-3.8-flash')
            self.assertEqual(len(result.output_parsed.eixos), 4)
            self.assertEqual(captured[0].headers['x-goog-api-key'], 'test-key')
            self.assertNotIn('test-key', str(captured[0].url))
            self.assertEqual(json.loads(captured[0].content)['generationConfig']['responseMimeType'], 'application/json')
        finally:
            await client.close()
