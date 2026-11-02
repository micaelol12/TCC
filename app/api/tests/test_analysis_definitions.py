"""File changes reach both editions, providers, evidence and provenance."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.algorithm_file import DEFAULT_CONFIG_PATH, load_algorithm_file
from app.experiment_config import ExperimentConfig, config_hash
from app.pipeline.aggregation import aggregate
from app.pipeline.clients import jev_questions
from app.pipeline.strategies import classify_chunk
from app.report_schemas import ReportAnalysis
from app.schemas import AnalysisResponse, Chunk, LogicalCalls
from app.settings import Settings
from test_pipeline import AXES, TEXT, answers, llm_payload


class DefinitionFileTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.path = Path(self.directory.name) / 'analysis-config.json'
        self.data = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding='utf-8'))
        self.marker = 'DEFINICAO_EXCLUSIVA_DO_ARQUIVO'
        self.data['axis_specs']['state']['poles']['B']['description'] = self.marker
        self.data['escala']['rubricas_por_eixo']['state']['polo_B_muito_forte']['situacao'] = self.marker + '_RUBRICA'
        self.path.write_text(json.dumps(self.data), encoding='utf-8')

    def tearDown(self):
        self.directory.cleanup()

    def test_both_editions_load_the_file_and_build_questions_from_its_definitions(self):
        with patch.dict('os.environ', {}, clear=True):
            for edition in ('production', 'lab'):
                settings = Settings(app_env=edition, algorithm_config_path=str(self.path))
                config = settings.algorithm_defaults()
                self.assertEqual(config.model_dump(mode='json'), self.data)
                question = jev_questions(config.escala, config.primitiva_polaridade,
                                         config.contexto_posicao_politica, config.axis_specs)['state_polaridade']
                self.assertIn(self.marker, question.instructions)
                self.assertEqual(question.criteria[0]['situacao'], self.marker + '_RUBRICA')

    def test_file_does_not_fall_back_to_embedded_definitions(self):
        mutations = (
            lambda d: d.pop('axis_specs'),
            lambda d: d['axis_specs'].pop('state'),
            lambda d: d['axis_specs']['state']['poles'].pop('B'),
            lambda d: d['axis_specs']['state']['poles']['B'].update(description=' '),
            lambda d: d['axis_specs']['state'].update(unknown='not allowed'),
        )
        for mutate in mutations:
            data = json.loads(json.dumps(self.data))
            mutate(data)
            self.path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'ALGORITHM_CONFIG_PATH'):
                load_algorithm_file(self.path)

    def test_metadata_is_immutable_and_changes_the_configuration_hash(self):
        config = load_algorithm_file(self.path)
        self.assertNotEqual(config_hash(config), config_hash(ExperimentConfig.model_validate(
            {**self.data, 'axis_specs': json.loads(DEFAULT_CONFIG_PATH.read_text(encoding='utf-8'))['axis_specs']})))
        with self.assertRaises(TypeError):
            config.axis_specs['state'] = config.axis_specs['economic']
        with self.assertRaises(TypeError):
            config.axis_specs['state'].poles['B'] = config.axis_specs['state'].poles['A']

    def test_previous_pipeline_snapshot_round_trips_without_new_metadata(self):
        previous = load_algorithm_file(self.path).model_dump(mode='json')
        previous.pop('axis_specs')
        config = ExperimentConfig.model_validate(previous)
        rows = [{axis: {'relevante': True, 'nivel': 0, 'method': 'jev', 'reason': [], 'quote': None} for axis in AXES}]
        response = AnalysisResponse(pipeline_version='jev-escalas-ordinal-12', processing_level='low',
            models_used=[], axes=aggregate(rows, 1, config), chunks=[Chunk(index=0, text=TEXT)],
            logical_calls=LogicalCalls(jev=1, llm=0), warnings=[], escala=config.escala,
            escala_hash=config.escala.hash, effective_config=config, config_version='1',
            config_hash=config_hash(config, 'jev-escalas-ordinal-12'), environment='development')
        snapshot = response.model_dump(mode='json')
        self.assertNotIn('axis_specs', snapshot['effective_config'])
        self.assertEqual(ReportAnalysis.model_validate(snapshot).model_dump(mode='json'), snapshot)

    async def test_all_modes_and_evidence_use_the_same_request_definitions(self):
        for mode in ('low', 'medium', 'high'):
            config = ExperimentConfig.model_validate({**self.data, 'regra_decisao': 'nivel',
                'semantic_evidence_check': True, 'jev_evidence_search': True})
            requests = []

            class Jev:
                async def system_one(self, **kwargs):
                    requests.append(json.dumps({'state': kwargs['state'], 'instructions':
                        {key: question.instructions for key, question in kwargs['questions'].items()}}, ensure_ascii=False))
                    if any(key.endswith('_polaridade') for key in kwargs['questions']):
                        return {'answers': answers(confidence=.01)}
                    result = {}
                    for key, question in kwargs['questions'].items():
                        if key.endswith('_exists'):
                            result[key] = {'noul': 1.0}
                        else:
                            selected = 'S000' if key.endswith('_where') else 'sustenta'
                            result[key] = {'choice': selected, 'confidence': 1.0,
                                'probabilities': {k: float(k == selected) for k in question.criteria}}
                    return {'answers': result}

            class Llm:
                def __init__(self):
                    self.responses = self

                async def parse(self, **kwargs):
                    requests.append(kwargs['input'])
                    return SimpleNamespace(output_parsed=llm_payload(), model='fake')

            decisions, calls, _ = await classify_chunk(TEXT, mode, Jev(), jev_questions(
                config.escala, config.primitiva_polaridade, config.contexto_posicao_politica,
                config.axis_specs), Llm(), SimpleNamespace(), config)
            self.assertEqual(calls['llm'], int(mode != 'low'))
            self.assertTrue(decisions['state'].get('evidence_audit'))
            self.assertTrue(all(self.marker in request for request in requests))


if __name__ == '__main__':
    unittest.main()
