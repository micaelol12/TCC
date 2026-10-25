"""Replay and edge cases for the experimental rule; no remote inference."""
import asyncio
from copy import deepcopy
import unittest

from pydantic import ValidationError
from app.experiment_config import ExperimentConfig, config_hash
from app.execution_store import public_request
from app.pipeline.domain import _normalizar_polaridade_ordinal, motivos_fallback
from app.pipeline.strategies import classify_chunk
from app.polarity import ESCALA_5_NIVEIS, ESCALA_9_NIVEIS, validar_escala
from app.report_schemas import ReportAnalysis
from app.schemas import AnalysisResponse
import test_experiments as experiments
from test_pipeline import AXES, TEXT, FakeJev, FakeLlm, llm_payload


# Recorded JEV distributions for the same 349-character nationalism definition.
FIVE = [.46, .37, .17, 0, 0]
NINE = [.26, .28, .13, .01, .32, 0, 0, 0, 0]


def raw(scale, values, primitive='choice', relevant=True):
    keys = [n.chave for n in scale.niveis] if primitive == 'choice' else list(map(str, range(len(values))))
    return {key: value for axis in AXES for key, value in {
        f'{axis}_relevancia': {'choice': 'A' if relevant else 'B', 'probabilities': {'A': .99 if relevant else .01, 'B': .01 if relevant else .99}},
        f'{axis}_polaridade': {'probabilities': dict(zip(keys, values)), 'confidence': .24},
    }.items()}


class DecisionRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tcc_lib.notebook_pipeline import carregar_pipeline_notebook
        cls.notebook = carregar_pipeline_notebook()

    def test_replay_preserves_raw_distribution_and_separates_intensity(self):
        for primitive in ('score', 'choice'):
            for scale, values, old_level, new_level in ((ESCALA_5_NIVEIS, FIVE, -2, -2), (ESCALA_9_NIVEIS, NINE, 0, -3)):
                response = raw(scale, values, primitive)['diplomatic_polaridade']
                original = _normalizar_polaridade_ordinal(response, True, primitive, scale)
                grouped = _normalizar_polaridade_ordinal(response, True, primitive, scale, 'polo_primeiro')
                self.assertEqual(original['nivel'], old_level)
                self.assertEqual(grouped['nivel'], new_level)
                self.assertEqual(grouped['nivel_jev_bruto'], old_level)
                self.assertEqual(grouped['probabilities_nivel'], original['probabilities_nivel'])
                self.assertEqual(grouped['probabilities_abc'], original['probabilities_abc'])
                self.assertEqual(grouped['confianca_nivel'], .24)
                reasons = motivos_fallback({'relevante': True, 'margem_relevancia': .98, **grouped}, ExperimentConfig(escala=scale, regra_decisao='polo_primeiro').jev_config())
                self.assertEqual(reasons, ['intensidade_ambigua'] if scale.id == 'ordinal_9_v1' else [])
                if scale.id == 'ordinal_9_v1':
                    self.assertAlmostEqual(grouped['probabilidade_nivel_condicional'], .28/.68)
                    self.assertAlmostEqual(grouped['margem_grupo'], .36)

    def test_mirror_ties_absence_and_direction_uncertainty(self):
        for values, expected, group in ((NINE[::-1], 3, 'A'),
                                       ([0, .34, .34, 0, .32, 0, 0, 0, 0], None, 'B'),
                                       ([.5, 0, 0, 0, .5, 0, 0, 0, 0], None, None),
                                       ([.1, 0, 0, 0, .8, 0, 0, 0, .1], 0, 'C'),
                                       ([.3, 0, 0, 0, .4, 0, 0, 0, .3], 0, 'C')):
            d = _normalizar_polaridade_ordinal(raw(ESCALA_9_NIVEIS, values)['diplomatic_polaridade'], True, 'choice', ESCALA_9_NIVEIS, 'polo_primeiro')
            self.assertEqual(d['nivel'], expected)
            self.assertEqual(d['grupo_mais_provavel'], group)
            if values[4] == .4:
                self.assertIn('direcao_ambigua', motivos_fallback({'relevante': True, 'margem_relevancia': .98, **d}, ExperimentConfig(regra_decisao='polo_primeiro').jev_config()))
        absent = _normalizar_polaridade_ordinal(raw(ESCALA_9_NIVEIS, NINE)['diplomatic_polaridade'], False, 'choice', ESCALA_9_NIVEIS, 'polo_primeiro')
        self.assertIsNone(absent['nivel'])
        self.assertIsNone(absent['valor_0_100'])
        self.assertEqual(absent['status'], 'sem_evidencia')

    def test_notebook_parity_and_arbitrary_codes(self):
        data = ESCALA_9_NIVEIS.model_dump(mode='json')
        for n, code in zip(data['niveis'], (-99, -75, -51, -12, 8, 9, 11, 30, 50)):
            n['codigo'] = code
        scale = validar_escala(data)
        for rule in ('nivel', 'polo_primeiro'):
            response = raw(scale, NINE)['diplomatic_polaridade']
            api = _normalizar_polaridade_ordinal(response, True, 'choice', scale, rule)
            nb_scale = self.notebook['validar_escala'](data)
            nb = self.notebook['_normalizar_polaridade_ordinal'](response, True, 'choice', nb_scale, rule)
            self.assertEqual(api, nb)
            self.assertEqual(api['nivel'], 8 if rule == 'nivel' else -75)

    def test_default_hash_and_invalid_rules(self):
        self.assertEqual(ExperimentConfig().regra_decisao, 'nivel')
        self.assertNotEqual(config_hash(ExperimentConfig()), config_hash(ExperimentConfig(regra_decisao='polo_primeiro')))
        with self.assertRaises(ValidationError): ExperimentConfig(regra_decisao='unknown')
        with self.assertRaises(ValueError): _normalizar_polaridade_ordinal({}, True, regra_decisao='unknown')
        with self.assertRaises(ValueError): config_hash(ExperimentConfig(regra_decisao='polo_primeiro'), 'jev-escalas-ordinal-5')


class DecisionStrategyTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_rules_and_llm_review_preserve_initial_diagnostic(self):
        async def run(rule, mode):
            config = ExperimentConfig(primitiva_polaridade='choice', regra_decisao=rule)
            llm = FakeLlm(llm_payload())
            result, calls, _ = await classify_chunk(TEXT, mode, FakeJev({'answers': raw(config.escala, NINE)}), {}, llm, experiments.lab_settings(), config)
            return result, calls
        original, grouped, reviewed = await asyncio.gather(run('nivel', 'low'), run('polo_primeiro', 'low'), run('polo_primeiro', 'medium'))
        self.assertEqual(original[0]['diplomatic']['nivel'], 0)
        self.assertEqual(grouped[0]['diplomatic']['nivel'], -3)
        self.assertEqual(grouped[1], {'jev': 1, 'llm': 0})
        self.assertEqual(reviewed[1], {'jev': 1, 'llm': 1})
        self.assertEqual(reviewed[0]['diplomatic']['nivel'], 1)
        self.assertEqual(reviewed[0]['diplomatic']['jev_diagnostic']['nivel'], -3)


class DecisionHttpTests(unittest.TestCase):
    setUp = experiments.ExperimentHttpTests.setUp
    tearDown = experiments.ExperimentHttpTests.tearDown

    def test_request_snapshot_diagnostic_report_and_rejected_tampering(self):
        self.jev.response = {'answers': raw(ESCALA_9_NIVEIS, NINE), 'model': 'jev-test'}
        config = {'primitiva_polaridade': 'choice', 'regra_decisao': 'polo_primeiro'}
        response = self.client.post('/api/analyze', json={'text': TEXT, 'processing_level': 'low', 'experiment_config': config})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        axis = result['axes'][1]
        self.assertEqual(axis['pole_a'], 12.5)
        self.assertIn('intensidade_ambigua', axis['reason_codes'])
        self.assertEqual(axis['jev_diagnostics'][0]['nivel_jev_bruto'], 0)
        self.assertEqual(result['effective_config']['regra_decisao'], 'polo_primeiro')
        self.assertEqual(ReportAnalysis.model_validate(result).model_dump(mode='json'), result)
        self.assertEqual(public_request({'text': TEXT, 'experiment_config': config}, self.settings)[2], config)
        broken = deepcopy(result)
        broken['axes'][1]['jev_diagnostics'][0]['probabilities_abc']['B'] = 1
        with self.assertRaises(ValidationError): AnalysisResponse.model_validate(broken)
        broken = deepcopy(result)
        broken['axes'][1]['jev_diagnostics'][0]['chunk_index'] = 99
        with self.assertRaises(ValidationError): AnalysisResponse.model_validate(broken)
        old = deepcopy(result)
        old['pipeline_version'] = 'jev-escalas-ordinal-5'
        old['effective_config'].pop('regra_decisao')
        old['effective_config'].pop('chunk_strategy')
        for a in old['axes']: a.pop('jev_diagnostics', None)
        old['config_hash'] = config_hash(ExperimentConfig.model_validate(old['effective_config']), old['pipeline_version'])
        self.assertEqual(AnalysisResponse.model_validate(old).model_dump(mode='json'), old)


if __name__ == '__main__': unittest.main()
