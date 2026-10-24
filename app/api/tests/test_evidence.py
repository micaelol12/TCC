import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from app.pipeline.evidence import audit_evidence, sentence_spans
from app.pipeline.domain import _score_evidencia_confere, criar_rubrica_polaridade_ordinal
from app.pipeline.strategies import classify_chunk
from app.pipeline.aggregation import aggregate
from app.experiment_config import ExperimentConfig, config_hash
from app.schemas import AnalysisResponse
from app.execution_store import public_request
from test_pipeline import TEXT, AXES, FakeLlm, llm_payload, answers
from test_experiments import lab_settings, analyze_route
import test_experiments


class EvidenceJev:
    def __init__(self, exists=.95, verdict='contradiz', tie=False, fail=False):
        self.exists, self.verdict, self.tie, self.fail = exists, verdict, tie, fail
        self.requests = []

    async def system_one(self, **kwargs):
        self.requests.append(kwargs)
        if self.fail:
            raise RuntimeError('private-provider-secret')
        questions = kwargs['questions']
        if any(key.endswith('_relevancia') for key in questions):
            return {'answers': answers(), 'model': 'fake-jev'}
        output = {}
        for key, question in questions.items():
            if key.endswith('_exists'):
                output[key] = {'noul': self.exists}
            else:
                keys = list(question.criteria)
                winner = 'S000' if key.endswith('_where') else self.verdict
                output[key] = {'choice': winner, 'confidence': 1.,
                    'probabilities': {k: (1 / len(keys) if self.tie else float(k == winner)) for k in keys}}
        return {'answers': output, 'model': 'fake-jev'}


class EvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_includes_new_extreme_levels(self):
        for level in (-4, -3, 3, 4):
            with self.subTest(level=level):
                decisions = {'economic': {'relevante': True, 'nivel': level, 'method': 'jev', 'quote': None}}
                result, calls, _ = await audit_evidence(TEXT, decisions, EvidenceJev(),
                    {'economic': criar_rubrica_polaridade_ordinal('economic')},
                    _score_evidencia_confere, quote_search=True)
                self.assertEqual(calls, 1)
                self.assertEqual(result['economic']['evidence_audit'][0]['level'], level)
                self.assertEqual(result['economic']['evidence_audit'][0]['status'], 'found')

    async def audit(self, jev, **options):
        decisions = {'economic': {'relevante': True, 'nivel': 1, 'method': 'jev', 'quote': None}}
        snapshot = deepcopy(decisions)
        result = await audit_evidence(TEXT, decisions, jev, {'economic': criar_rubrica_polaridade_ordinal('economic')},
            _score_evidencia_confere, **options)
        self.assertEqual(decisions, snapshot)
        self.assertEqual(result[0]['economic']['nivel'], 1)
        return result

    async def test_search_and_contradiction_are_observational_and_batched(self):
        jev = EvidenceJev()
        result, calls, models = await self.audit(jev, semantic_check=True, quote_search=True)
        d = result['economic']
        self.assertEqual(calls, 2)
        self.assertEqual(d['quote'], TEXT)
        self.assertEqual([a['status'] for a in d['evidence_audit']], ['found', 'contradiz'])
        found = d['evidence_audit'][0]
        self.assertEqual(TEXT[found['start']:found['end']], d['quote'])
        self.assertEqual(models, ['fake-jev', 'fake-jev'])
        self.assertEqual(jev.requests[1]['state']['afirmacoes']['economic']['nivel'], 1)

    async def test_absent_evidence_ties_invalid_response_and_exact_threshold(self):
        for jev, status in [(EvidenceJev(exists=.69), 'not_selected'), (EvidenceJev(tie=True), 'not_selected'),
                            (EvidenceJev(exists=float('nan')), 'invalid'), (EvidenceJev(exists=.7), 'found')]:
            result, calls, _ = await self.audit(jev, quote_search=True, existence_min=.7)
            self.assertEqual(calls, 1)
            self.assertEqual(result['economic']['evidence_audit'][0]['status'], status)
            self.assertEqual(bool(result['economic']['quote']), status == 'found')

    async def test_failure_is_recorded_without_leaking_secrets_or_changing_score(self):
        result, calls, _ = await self.audit(EvidenceJev(fail=True), semantic_check=True, quote_search=True)
        self.assertEqual(calls, 1)
        self.assertEqual(result['economic']['evidence_audit'][0]['status'], 'failed')
        self.assertNotIn('private-provider-secret', json.dumps(result))

    async def test_disabled_checks_do_not_call_and_cancellation_propagates(self):
        jev = EvidenceJev()
        result, calls, _ = await self.audit(jev)
        self.assertEqual(calls, 0)
        self.assertNotIn('evidence_audit', result['economic'])
        cancelled = SimpleNamespace(system_one=AsyncMock(side_effect=asyncio.CancelledError()))
        with self.assertRaises(asyncio.CancelledError):
            await self.audit(cancelled, quote_search=True)

    async def test_high_mode_semantics_only_preserves_aggregation(self):
        settings = lab_settings()
        baseline, _, _ = await classify_chunk(TEXT, 'high', None, None, FakeLlm(llm_payload()), settings, ExperimentConfig())
        audited, calls, _ = await classify_chunk(TEXT, 'high', EvidenceJev(), None, FakeLlm(llm_payload()), settings,
            ExperimentConfig(semantic_evidence_check=True, jev_evidence_search=True))
        self.assertEqual(calls, {'jev': 1, 'llm': 1})
        for before, after in zip(aggregate([baseline], 1), aggregate([audited], 1)):
            self.assertEqual(before.pole_a, after.pole_a)
            self.assertEqual(before.coverage, after.coverage)
            self.assertEqual(before.level_counts, after.level_counts)
            self.assertEqual(after.evidence_audit[0].status, 'contradiz')

    async def test_invalid_or_missing_quote_never_sent_as_semantic_support(self):
        jev = EvidenceJev()
        result, calls, _ = await audit_evidence(TEXT,
            {'economic': {'relevante': True, 'nivel': 1, 'method': 'llm', 'quote': 'Quatro palavras que inexistem'}}, jev,
            {'economic': {}}, _score_evidencia_confere, semantic_check=True)
        self.assertEqual(calls, 0)
        self.assertEqual(result['economic']['evidence_audit'][0]['status'], 'not_literal')

    def test_segment_offsets_are_original_and_cover_long_inputs(self):
        text = '  Ação pública com emoji 😀.\n Outra frase original aqui! ' * 240
        spans = sentence_spans(text)
        self.assertLessEqual(len(spans), 200)
        for span in spans.values():
            self.assertEqual(text[span['start']:span['end']], span['quote'])
        recovered = ''.join(s['quote'] for s in spans.values())
        self.assertEqual(''.join(recovered.split()), ''.join(text.split()))

    def test_public_config_logging_and_legacy_hash(self):
        config = ExperimentConfig(semantic_evidence_check=True, jev_evidence_search=True)
        _, _, saved = public_request({'text': TEXT, 'experiment_config': config.model_dump()}, lab_settings())
        self.assertIs(saved['semantic_evidence_check'], True)
        self.assertNotEqual(config_hash(config), config_hash(ExperimentConfig()))
        old = ExperimentConfig().model_dump(exclude={'regra_decisao', 'primitiva_polaridade', 'escala', 'semantic_evidence_check', 'jev_evidence_search', 'evidence_existence_min'})
        import hashlib
        legacy_hash = hashlib.sha256(json.dumps({'config_version': '1', 'pipeline_version': 'jev-2-polos-mvp-1',
            'effective_config': old}, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        self.assertEqual(config_hash(ExperimentConfig.model_validate(old), 'jev-2-polos-mvp-1'), legacy_hash)


class EvidenceHttpTests(unittest.TestCase):
    setUp = test_experiments.ExperimentHttpTests.setUp
    tearDown = test_experiments.ExperimentHttpTests.tearDown

    def test_high_semantics_requires_typesafe_and_reserves_extra_budget(self):
        from app.lab_credentials import set_key
        set_key(self.token, 'typesafe', '')
        response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'high',
            'experiment_config': {'semantic_evidence_check': True}})
        self.assertEqual(response.status_code, 503)
        self.mocks[0].assert_not_called()
        with patch.object(analyze_route, 'settings', replace(self.settings, daily_calls=1)):
            response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'high',
                'experiment_config': {}})
            self.assertEqual(response.status_code, 200)

    def test_low_search_and_semantics_are_logged_and_budgeted(self):
        jev = EvidenceJev(); jev.aclose = AsyncMock()
        from app.pipeline.clients import jev_questions
        config = {'jev_evidence_search': True, 'semantic_evidence_check': True}
        with patch.object(analyze_route, 'jev_client', return_value=jev), patch.object(analyze_route, 'jev_questions', side_effect=jev_questions):
            with patch.object(analyze_route, 'settings', replace(self.settings, daily_calls=2)):
                denied = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'low', 'experiment_config': config})
                self.assertEqual(denied.status_code, 429)
                self.assertEqual(jev.requests, [])
            response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'low', 'experiment_config': config})
        self.assertEqual(response.status_code, 200, response.text)
        result = AnalysisResponse.model_validate(response.json())
        self.assertEqual(result.logical_calls.jev, 3)
        self.assertEqual(result.axes[0].pole_a, 62.5)
        self.assertEqual(result.axes[0].evidence[0].quote, TEXT)
        self.assertEqual(result.axes[0].evidence_audit[1].status, 'contradiz')
        self.assertEqual(analyze_route.daily['calls'], 3)
