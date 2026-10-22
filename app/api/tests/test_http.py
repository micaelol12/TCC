import importlib
import unittest
from dataclasses import replace
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

route_module = importlib.import_module('app.routes.analyze')


class HttpContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_health_and_capabilities_do_not_call_providers(self):
        health = self.client.get('/api/health')
        self.assertEqual(health.json(), {'status': 'ok'})
        self.assertEqual(health.headers['cache-control'], 'no-store')
        capabilities = self.client.get('/api/capabilities')
        self.assertIn('modes', capabilities.json())
        self.assertNotIn('TYPESAFE_API_KEY', capabilities.text)

    def test_invalid_payload_does_not_echo_text_or_profile(self):
        secret = 'conteúdo político privado único'
        response = self.client.post('/api/analyze', json={'text': secret, 'processing_level': 'low', 'personal_score': 88})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)
        self.assertNotIn('88', response.text)

    def test_char_limit_and_unavailable_mode(self):
        with patch.object(route_module, 'settings', replace(route_module.settings, max_chars=10, typesafe_key='', maritaca_key='')):
            large = self.client.post('/api/analyze', json={'text': 'x' * 11, 'processing_level': 'low'})
            self.assertEqual(large.status_code, 413)
            unavailable = self.client.post('/api/analyze', json={'text': 'texto', 'processing_level': 'high'})
            self.assertEqual(unavailable.status_code, 503)


if __name__ == '__main__':
    unittest.main()
