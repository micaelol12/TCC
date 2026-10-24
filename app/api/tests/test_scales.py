"""Fixtures brutas e paridade determinística; nenhum provedor remoto é consultado."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.polarity import ESCALA_5_NIVEIS, ESCALA_9_NIVEIS, validar_escala, valor_nivel
from app.experiment_config import ExperimentConfig, config_hash
from app.pipeline import domain
from app.pipeline.aggregation import aggregate
from app.pipeline.clients import jev_questions
from app.pipeline.strategies import classify_chunk
from app.pipeline.validation import schema_for, validate_answer
from app.report_schemas import ReportAnalysis
from app.schemas import AnalysisResponse, Chunk, LogicalCalls
from tests import test_experiments

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook

TEXT = "Vamos ampliar o benefício das famílias de baixa renda."
AXES = ('economic', 'diplomatic', 'state', 'society')


def sete():
    data = ESCALA_9_NIVEIS.model_dump(mode='json')
    data['id'] = 'experimental_arbitraria_7'
    data['niveis'] = [n for n in data['niveis'] if abs(n['codigo']) != 1]
    for n, code, value in zip(data['niveis'], [101, 88, 22, -7, -9, -55, -99], [0., .1, .4, .5, .6, .7, 1.]):
        n.update(codigo=code, valor=value)
    for axis in AXES:
        data['rubricas_por_eixo'][axis] = {n['chave']: data['rubricas_por_eixo'][axis][n['chave']] for n in data['niveis']}
    return validar_escala(data)


def raw(escala, index, relevant=True, confidence=.99):
    return {k: v for axis in AXES for k, v in {
        f'{axis}_relevancia': {'choice': 'A' if relevant else 'B', 'probabilities': {'A': .99 if relevant else .01, 'B': .01 if relevant else .99}},
        f'{axis}_polaridade': {'probabilities': {str(i): int(i == index) for i in range(len(escala.niveis))}, 'confidence': confidence},
    }.items()}


class ScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = carregar_pipeline_notebook()

    def test_initial_notebook_cell_initializes_helpers_in_the_kernel_namespace(self):
        notebook = json.loads((ROOT / 'Pipeline - Passo a Passo.ipynb').read_text(encoding='utf-8'))
        kernel = {'__name__': '__main__'}
        exec(''.join(notebook['cells'][0]['source']), kernel)
        self.assertIn('_score_campo', kernel)
        self.assertIs(kernel['_normalizar_polaridade_ordinal'].__globals__, kernel)
        kernel['ESCALA_ATUAL'] = kernel['ESCALA_9_NIVEIS']
        response = raw(ESCALA_9_NIVEIS, 5)['economic_polaridade']
        result = kernel['_normalizar_polaridade_ordinal'](response, True)
        self.assertEqual(result['valor_0_100'], 62.5)
        self.assertNotIn('pipeline_real', kernel)
        self.assertNotIn('registros_playground', kernel)

    def test_reported_decision_example_runs_without_the_intermediate_helper_cells(self):
        notebook = json.loads((ROOT / 'Pipeline - Passo a Passo.ipynb').read_text(encoding='utf-8'))
        sources = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
        example = next(s for s in sources if 'def distribuicao_simulada(' in s)
        decision = next(s for s in sources if s.startswith('decisao_exemplo = decidir_jev('))
        kernel = {'__name__': '__main__'}
        exec(''.join(notebook['cells'][0]['source']), kernel)
        kernel['display'] = lambda *args, **kwargs: None
        for name in ('ESCALA_5_NIVEIS', 'ESCALA_9_NIVEIS'):
            for primitive in ('score', 'choice'):
                kernel['ESCALA_ATUAL'] = kernel[name]
                kernel['CONFIG_JEV_LLM_2_POLOS']['primitiva_polaridade'] = primitive
                exec(example, kernel)
                exec(decision, kernel)
                result = kernel['decisao_exemplo']
                self.assertTrue(result['relevante'])
                self.assertEqual(result['status'], 'direcional')
                self.assertEqual(result['valor_0_100'], 75)

    def test_invalid_objects_fail_locally_and_are_deeply_immutable(self):
        source = ESCALA_5_NIVEIS.model_dump(mode='json')
        instance = validar_escala(source)
        source['niveis'][0]['valor'] = .1
        source['rubricas_por_eixo']['economic']['sem_posicao']['exemplos'][0] = 'alterado'
        self.assertEqual(instance.hash, ESCALA_5_NIVEIS.hash)
        with self.assertRaises(TypeError): instance.rubricas_por_eixo['economic']['sem_posicao'] = None
        with self.assertRaises(ValueError): instance.niveis[0].valor = .1
        mutations = [
            lambda d: d.update(versao=True), lambda d: d.update(id=' '),
            lambda d: d['niveis'].pop(), lambda d: d.update(niveis=d['niveis'][:1]),
            lambda d: d['niveis'][0].update(codigo=True), lambda d: d['niveis'][0].update(rotulo=' '),
            lambda d: d['niveis'][0].update(codigo=0), lambda d: d['niveis'][0].update(chave='sem_posicao'),
            lambda d: d['niveis'][0].update(valor=float('nan')), lambda d: d['niveis'][0].update(valor=.1),
            lambda d: d['niveis'][2].update(valor=.4), lambda d: d['niveis'][1].update(valor=.75),
            lambda d: d['niveis'][1].update(polo=None), lambda d: d['niveis'][0].update(polo='A'),
            lambda d: d['rubricas_por_eixo'].pop('state'),
            lambda d: d['rubricas_por_eixo']['state'].pop('sem_posicao'),
            lambda d: d['rubricas_por_eixo']['state']['sem_posicao'].update(situacao=' '),
        ]
        for mutate in mutations:
            data = ESCALA_5_NIVEIS.model_dump(mode='json'); mutate(data)
            with self.subTest(data=str(data)[:90]), self.assertRaises(ValueError): validar_escala(data)
        with self.assertRaises(ValueError):
            self.ns['CascataJevLLM2Polos'](None, None, self.ns['AXIS_SPECS'], escala=data, usar_fallback=False)
        for invalid in ({}, False, 0, []):
            with self.assertRaises(ValueError):
                self.ns['CascataJevLLM2Polos'](None, None, self.ns['AXIS_SPECS'], escala=invalid, usar_fallback=False)

    def test_hash_uses_full_normalized_content(self):
        original = ESCALA_5_NIVEIS.model_dump(mode='json')
        reordered = {key: original[key] for key in reversed(list(original))}
        self.assertEqual(validar_escala(reordered).hash, ESCALA_5_NIVEIS.hash)
        changed = deepcopy(original)
        changed['rubricas_por_eixo']['state']['sem_posicao']['situacao'] += ' Nova âncora.'
        self.assertNotEqual(validar_escala(changed).hash, ESCALA_5_NIVEIS.hash)
        self.assertNotEqual(config_hash(ExperimentConfig(escala=changed)), config_hash(ExperimentConfig(escala=original)))

    def test_same_raw_fixtures_have_exact_parity_for_5_9_and_arbitrary_7(self):
        for escala in (ESCALA_5_NIVEIS, ESCALA_9_NIVEIS, sete()):
            notebook_scale = self.ns['validar_escala'](escala.model_dump(mode='json'))
            self.assertEqual(notebook_scale.hash, escala.hash)
            config = ExperimentConfig(escala=escala)
            for index, n in enumerate(escala.niveis):
                for primitive in ('score', 'choice'):
                    answer = raw(escala, index)['economic_polaridade']
                    if primitive == 'choice':
                        answer['probabilities'] = {level.chave: int(i == index) for i, level in enumerate(escala.niveis)}
                    actual = domain._normalizar_polaridade_ordinal(answer, True, primitive, escala)
                    expected = self.ns['_normalizar_polaridade_ordinal'](answer, True, primitive, notebook_scale)
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual['nivel'], n.codigo)
                    self.assertEqual(actual['classe'], n.polo or 'C')
                    self.assertEqual(actual['valor_0_100'], 100 * n.valor)
                    item = schema_for(['economic'], escala).model_validate({'eixos': [{'eixo': 'economic', 'relevante': True, 'nivel': n.codigo, 'evidencia': TEXT}]}).eixos[0]
                    llm = domain.decidir_llm(item, TEXT, {'relevante': True}, [], 'fake', None, escala)
                    self.assertEqual(llm['valor_0_100'], actual['valor_0_100'])
                    self.assertEqual(llm['classe'], actual['classe'])
                rows = [{axis: {'relevante': True, 'nivel': n.codigo, 'method': 'jev', 'reason': [], 'quote': None} for axis in AXES}]
                api = aggregate(rows, 1, config)[0]
                nb = self.ns['resumir_eixo_ordinal']([{**self.ns['decisao_vazia']('economic'), **actual, 'relevante': True}], escala=notebook_scale)
                self.assertEqual(api.pole_a, nb['índice A'])
                self.assertEqual(api.level_counts_by_key[n.chave], nb[f'n {n.chave}'])
                self.assertEqual(api.pole_a, 100 * n.valor)
                self.assertEqual(domain.criar_rubrica_polaridade_ordinal('economic', escala=escala), self.ns['criar_rubrica_polaridade_ordinal']('economic', escala=notebook_scale))
            questions = jev_questions(escala)
            self.assertEqual(len(questions['economic_polaridade'].criteria), len(escala.niveis))

    def test_center_absence_tie_and_masses_are_distinct(self):
        scale = sete()
        center = raw(scale, 3)['economic_polaridade']
        self.assertEqual(domain._normalizar_polaridade_ordinal(center, True, escala=scale)['status'], 'sem_posicao')
        absent = domain._normalizar_polaridade_ordinal(center, False, escala=scale)
        self.assertEqual(absent['status'], 'sem_evidencia'); self.assertIsNone(absent['valor_0_100'])
        center['probabilities'] = {str(i): .5 if i in (0, 6) else 0 for i in range(7)}
        tie = domain._normalizar_polaridade_ordinal(center, True, escala=scale)
        self.assertEqual(tie['status'], 'empate'); self.assertIsNone(tie['nivel'])
        self.assertEqual(tie['p_polo_A'], .5); self.assertEqual(tie['p_polo_B'], .5)
        center['probabilities'] = dict(zip(map(str, range(7)), [.05, .1, .15, .1, .2, .15, .25]))
        d = domain._normalizar_polaridade_ordinal(center, True, escala=scale)
        self.assertEqual(d['nivel'], -99)  # MAP, never the expectation or a confidence-based interpolation.
        self.assertAlmostEqual(d['p_polo_A'], .6); self.assertAlmostEqual(d['p_polo_B'], .3)

    def test_llm_rejects_other_scale_and_noninteger_levels(self):
        payload = {'eixos': [{'eixo': 'economic', 'relevante': True, 'nivel': 3, 'evidencia': TEXT}]}
        self.assertEqual(validate_answer(payload, ['economic'], TEXT, ESCALA_9_NIVEIS)['economic']['nivel'], 3)
        for bad in (3, True, 1.0, '1'):
            payload['eixos'][0]['nivel'] = bad
            with self.assertRaises(ValueError): validate_answer(payload, ['economic'], TEXT, ESCALA_5_NIVEIS)
            with self.assertRaises(ValueError): self.ns['_esquema_resposta'](['economic'], self.ns['ESCALA_5_NIVEIS']).model_validate(payload)

    def test_saved_summary_and_reports_use_original_snapshot(self):
        scale = ESCALA_5_NIVEIS
        config = ExperimentConfig(escala=scale)
        d = self.ns['decidir_jev']('economic', raw(scale, 3), config.jev_config())
        record = {'texto': TEXT, 'eixos': {a: d for a in AXES}, 'eixos_jev': {a: d for a in AXES}, 'escala': scale.model_dump(mode='json')}
        previous = self.ns['ESCALA_ATUAL']
        try:
            self.ns['ESCALA_ATUAL'] = self.ns['ESCALA_9_NIVEIS']
            self.assertEqual(self.ns['resumir_documento']([record])['índice A'].to_list(), [75] * 4)
        finally: self.ns['ESCALA_ATUAL'] = previous
        rows = [{a: {'relevante': True, 'nivel': 1, 'method': 'jev', 'reason': [], 'quote': None} for a in AXES}]
        response = AnalysisResponse(processing_level='low', models_used=[], axes=aggregate(rows, 1, config),
            chunks=[Chunk(index=0, text=TEXT)], logical_calls=LogicalCalls(jev=1, llm=0), warnings=[], escala=scale, escala_hash=scale.hash)
        snapshot = response.model_dump(mode='json')
        self.assertEqual(ReportAnalysis.model_validate(snapshot).model_dump(mode='json'), snapshot)
        snapshot['axes'][0]['level_counts_by_key']['sem_posicao'] = 5
        with self.assertRaises(ValueError): ReportAnalysis.model_validate(snapshot)

    def test_historical_config_hashes_do_not_gain_a_scale_field(self):
        for version in ('jev-2-polos-mvp-1', 'jev-2-polos-evidence-2', 'jev-9-niveis-evidence-3', 'jev-escalas-ordinal-4', 'jev-escalas-ordinal-5'):
            data = ExperimentConfig().model_dump(mode='json', exclude={'regra_decisao'} | (set() if version == 'jev-escalas-ordinal-5' else {'primitiva_polaridade'}) | (set() if version in ('jev-escalas-ordinal-4', 'jev-escalas-ordinal-5') else {'escala'}))
            if version == 'jev-2-polos-mvp-1':
                for key in ('semantic_evidence_check','jev_evidence_search','evidence_existence_min'): data.pop(key)
            expected = hashlib.sha256(json.dumps({'config_version': '1', 'pipeline_version': version, 'effective_config': data}, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
            self.assertEqual(config_hash(ExperimentConfig.model_validate(data), version), expected)


class ConcurrentScaleTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_fallback_and_high_use_their_request_scale(self):
        async def run(scale, mode):
            class Jev:
                async def system_one(self, **kwargs):
                    await asyncio.sleep(0)
                    return {'answers': raw(scale, len(scale.niveis)-1, confidence=.01)}
            class Llm:
                responses = None
                def __init__(self): self.responses = self; self.prompt = None
                async def parse(self, **kwargs):
                    self.prompt = kwargs
                    await asyncio.sleep(0)
                    payload = {'eixos': [{'eixo': a, 'relevante': True, 'nivel': 1, 'evidencia': TEXT} for a in AXES]}
                    return SimpleNamespace(output_parsed=kwargs['text_format'].model_validate(payload), model='fake')
            llm = Llm()
            config = ExperimentConfig(escala=scale)
            decisions, calls, _ = await classify_chunk(TEXT, mode, Jev(), jev_questions(scale), llm, SimpleNamespace(), config)
            self.assertIn(f'{scale.niveis[-1].codigo}={scale.niveis[-1].chave}', llm.prompt['instructions'])
            return aggregate([decisions], 1, config)[0].pole_a, calls
        results = await asyncio.gather(run(ESCALA_5_NIVEIS, 'medium'), run(ESCALA_9_NIVEIS, 'medium'), run(ESCALA_5_NIVEIS, 'high'))
        self.assertEqual([r[0] for r in results], [75., 62.5, 75.])
        self.assertEqual(results[0][1], {'jev': 1, 'llm': 1})


class HttpScaleTests(unittest.TestCase):
    setUp = test_experiments.ExperimentHttpTests.setUp
    tearDown = test_experiments.ExperimentHttpTests.tearDown

    def test_invalid_scale_is_rejected_before_clients_are_created(self):
        for invalid in ({}, False, [], {'id': 'incompleta'}):
            response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'medium', 'experiment_config': {'escala': invalid}})
            self.assertEqual(response.status_code, 422)
        for factory in self.mocks: factory.assert_not_called()

    def test_each_http_result_carries_the_scale_that_scored_it(self):
        for scale, value in ((ESCALA_5_NIVEIS, 75), (ESCALA_9_NIVEIS, 62.5)):
            index = next(i for i, n in enumerate(scale.niveis) if n.codigo == 1)
            self.jev.response = {'answers': raw(scale, index), 'model': 'simulado'}
            response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'low', 'experiment_config': {'escala': scale.model_dump(mode='json')}})
            self.assertEqual(response.status_code, 200, response.text)
            data = response.json()
            self.assertEqual(data['schema_version'], '3')
            self.assertEqual(data['escala_hash'], scale.hash)
            self.assertEqual(data['effective_config']['escala'], scale.model_dump(mode='json'))
            self.assertEqual(data['axes'][0]['pole_a'], value)
            self.assertEqual(sum(data['axes'][0]['level_counts_by_key'].values()), 1)


if __name__ == '__main__': unittest.main()
