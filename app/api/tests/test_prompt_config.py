"""Configurable policy reaches providers, snapshots and history without remote calls."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.execution_store import public_request
from app.experiment_config import ExperimentConfig, config_hash
from app.pipeline.aggregation import aggregate
from app.pipeline.clients import jev_questions
from app.pipeline.domain import criar_questoes_eixo, criar_rubrica_polaridade_ordinal
from app.pipeline.strategies import classify_chunk
from app.polarity import CONTEXTO_POSICAO_POLITICA, instrucoes_escala
from app.report_schemas import ReportAnalysis
from app.schemas import AnalysisResponse, Chunk, LogicalCalls
from test_pipeline import AXES, TEXT, answers, llm_payload
import test_experiments

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


class PromptConfigTests(unittest.IsolatedAsyncioTestCase):
    def test_validation_hash_and_historical_roundtrip(self):
        for value in ('', ' \n\t', None, True, 42, 'a' * 20001):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                ExperimentConfig(contexto_posicao_politica=value)
        default = ExperimentConfig()
        custom = ExperimentConfig(contexto_posicao_politica='Classifique apenas a posição do autor.')
        self.assertNotEqual(config_hash(default), config_hash(custom))
        with self.assertRaises(ValueError):
            config_hash(custom, 'jev-escalas-ordinal-11')
        effective = default.model_dump(mode='json', exclude={'contexto_posicao_politica'})
        public = {'config_version': '1', 'pipeline_version': 'jev-escalas-ordinal-11', 'effective_config': effective}
        original_hash = hashlib.sha256(json.dumps(public, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        self.assertEqual(config_hash(default, public['pipeline_version']), original_hash)
        rows = [{a: {'relevante': True, 'nivel': 0, 'method': 'jev', 'reason': [], 'quote': None} for a in AXES}]
        snapshot = AnalysisResponse(processing_level='low', models_used=[], axes=aggregate(rows, 1, default),
            chunks=[Chunk(index=0, text=TEXT)], logical_calls=LogicalCalls(jev=1, llm=0), warnings=[],
            escala=default.escala, escala_hash=default.escala.hash).model_dump(mode='json')
        snapshot.update(**public, config_hash=original_hash, environment='development')
        self.assertEqual(ReportAnalysis.model_validate(snapshot).model_dump(mode='json'), snapshot)

    async def test_context_is_isolated_across_modes_and_evidence_calls(self):
        async def run(mode):
            context = f'Política exclusiva da execução {mode}.\nConsidere somente a posição do autor.'
            seen = []

            class Jev:
                async def system_one(self, **kwargs):
                    await asyncio.sleep(0)
                    seen.extend(q.instructions for q in kwargs['questions'].values())
                    if any(k.endswith('_polaridade') for k in kwargs['questions']):
                        return {'answers': answers(confidence=.01)}
                    result = {}
                    for key in kwargs['questions']:
                        if key.endswith('_exists'):
                            result[key] = {'noul': 1.0}
                        else:
                            selected = 'S000' if key.endswith('_where') else 'sustenta'
                            result[key] = {'choice': selected, 'confidence': 1.0,
                                'probabilities': {k: float(k == selected) for k in kwargs['questions'][key].criteria}}
                    return {'answers': result}

            class Llm:
                def __init__(self):
                    self.responses = self

                async def parse(self, **kwargs):
                    await asyncio.sleep(0)
                    seen.append(kwargs['instructions'])
                    seen.extend(q['instructions'] for r in json.loads(kwargs['input'])['rubricas'].values() for q in r.values())
                    return SimpleNamespace(output_parsed=llm_payload(), model='fake-llm')

            config = ExperimentConfig(contexto_posicao_politica=context,
                semantic_evidence_check=True, jev_evidence_search=True)
            decisions, calls, _ = await classify_chunk(TEXT, mode, Jev(), jev_questions(
                config.escala, config.primitiva_polaridade, context), Llm(), SimpleNamespace(), config)
            self.assertTrue(seen)
            self.assertTrue(all(instruction.startswith(context + ' ') for instruction in seen))
            self.assertTrue(all(CONTEXTO_POSICAO_POLITICA not in instruction for instruction in seen))
            self.assertTrue(all(d.get('evidence_audit') for d in decisions.values()))
            self.assertEqual(calls['llm'], int(mode != 'low'))
            return config_hash(config)

        hashes = await asyncio.gather(*(run(mode) for mode in ('low', 'medium', 'high')))
        self.assertEqual(len(set(hashes)), 3)

    def test_notebook_and_api_share_custom_context(self):
        ns = carregar_pipeline_notebook()
        context = 'Considere definições e falas citadas como posições expressas.'
        scale = ExperimentConfig().escala
        self.assertEqual(instrucoes_escala(scale, context), ns['instrucoes_escala'](scale, context))
        for axis in AXES:
            self.assertEqual(criar_questoes_eixo(axis, contexto_posicao_politica=context),
                ns['criar_questoes_eixo'](axis, contexto_posicao_politica=context))
            self.assertEqual(criar_rubrica_polaridade_ordinal(axis, escala=scale, contexto_posicao_politica=context),
                ns['criar_rubrica_polaridade_ordinal'](axis, escala=scale, contexto_posicao_politica=context))
        pipeline = ns['CascataJevLLM2Polos'](None, None, ns['AXIS_SPECS'],
            usar_fallback=False, contexto_posicao_politica=context)
        self.assertEqual(pipeline.config['contexto_posicao_politica'], context)
        self.assertTrue(all(q.instructions.startswith(context + ' ') for q in pipeline.perguntas.values()))


class PromptHttpTests(unittest.TestCase):
    setUp = test_experiments.ExperimentHttpTests.setUp
    tearDown = test_experiments.ExperimentHttpTests.tearDown

    def test_lab_override_reaches_questions_snapshot_and_log(self):
        context = 'Classifique apenas o posicionamento do autor.\nRespeite críticas.'
        payload = {'text': TEXT, 'processing_level': 'low',
                   'experiment_config': {'contexto_posicao_politica': context}}
        with patch.object(test_experiments.analyze_route, 'jev_questions', wraps=jev_questions) as questions:
            response = self.client.post('/api/analyze', json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(questions.call_args.args[2], context)
        self.assertEqual(result['effective_config']['contexto_posicao_politica'], context)
        self.assertEqual(public_request(payload, self.settings)[2]['contexto_posicao_politica'], context)
        self.assertEqual(ReportAnalysis.model_validate(result).model_dump(mode='json'), result)
        self.assertEqual(result['config_hash'], config_hash(ExperimentConfig.model_validate(result['effective_config'])))
        self.assertIn('contexto_posicao_politica', self.client.get('/api/capabilities').json()['experimental']['defaults'])
        for value in ('', '  ', 'a' * 20001, 1, None):
            payload['experiment_config']['contexto_posicao_politica'] = value
            self.assertEqual(self.client.post('/api/analyze', json=payload).status_code, 422)
