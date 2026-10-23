import ast
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import matplotlib
matplotlib.use('Agg')

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


def load_definitions(source, ns, filename):
    nodes = [n for n in ast.parse(source).body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), ns)


class NotebookExperimentTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb = json.loads((ROOT / 'TCC.ipynb').read_text(encoding='utf-8'))
        cls.pipeline = carregar_pipeline_notebook()
        seven = cls.pipeline['ESCALA_9_NIVEIS'].model_dump(mode='json')
        seven['id'] = 'experimental_7_benchmark'
        seven['niveis'] = [n for n in seven['niveis'] if abs(n['codigo']) != 4]
        for i, n in enumerate(seven['niveis']): n['valor'] = i / 6
        for axis in seven['rubricas_por_eixo']:
            seven['rubricas_por_eixo'][axis] = {n['chave']: seven['rubricas_por_eixo'][axis][n['chave']] for n in seven['niveis']}
        cls.pipeline['ESCALA_TESTE_7'] = cls.pipeline['validar_escala'](seven)

    def context(self):
        ns = {'__name__': 'tcc_experiment_test'}
        with patch('IPython.display.display'):
            load_definitions(''.join(self.nb['cells'][424]['source']), ns, 'experimento-texto')
            load_definitions(''.join(self.nb['cells'][425]['source']), ns, 'experimento-benchmark')
            load_definitions(''.join(self.nb['cells'][428]['source']).split('\n\n_j9t_config =')[0], ns, 'experimento-json')
        # The common benchmark is loaded without its historical demonstration or providers.
        common = next(c for c in self.nb['cells'] if c['cell_type'] == 'code' and 'def executar_benchmark_8values(' in ''.join(c['source']))
        load_definitions(''.join(common['source']), ns, 'benchmark-comum')
        return ns

    async def test_scale_selection_uses_the_common_benchmark_without_repeating_inference(self):
        ns = self.context()
        ns['effect_to_axis'] = self.pipeline['EFFECT_TO_AXIS']
        question = self.pipeline['Question'](id=1, question='Vamos ampliar os serviços públicos de saúde.', effect=self.pipeline['Effect'](econ=10, dipl=10, govt=10, scty=10))
        for name in ('ESCALA_5_NIVEIS', 'ESCALA_9_NIVEIS', 'ESCALA_TESTE_7'):
            scale = self.pipeline[name]
            class Jev:
                calls = 0
                async def system_one(self, **kwargs):
                    self.calls += 1
                    return {'model': 'simulado', 'answers': {k: v for axis in self_axes for k, v in {
                        f'{axis}_relevancia': {'choice': 'A', 'probabilities': {'A': .99, 'B': .01}},
                        f'{axis}_polaridade': {'probabilities': {str(i): int(n.codigo == 1) for i, n in enumerate(scale.niveis)}, 'confidence': .99},
                    }.items()}}
            self_axes = self.pipeline['AXIS_SPECS']
            jev = Jev()
            async def classify(text):
                return await ns['_executar_teste_jev_9_niveis'](text, escala=scale, cliente=jev)
            original = ns['executar_benchmark_8values']
            with patch.dict(ns, executar_benchmark_8values=unittest.mock.Mock(wraps=original)):
                details, summary = await ns['executar_benchmark_jev_9_niveis_8values']([question], classificar=classify, escala=scale, pausa_segundos=0)
                ns['executar_benchmark_8values'].assert_called_once()
            self.assertEqual(jev.calls, 1)
            self.assertTrue(details['passou'].all())
            self.assertEqual(len(details), 4)
            self.assertEqual(summary['casos'].sum(), 4)
            self.assertEqual(set(details['escala_hash']), {scale.hash})
            self.assertEqual(details.attrs['escala'], scale.model_dump(mode='json'))

    async def test_json_evaluation_preserves_documents_failures_and_exports(self):
        for name in ('ESCALA_5_NIVEIS', 'ESCALA_9_NIVEIS'):
            await self.verify_json_evaluation(name)

    async def verify_json_evaluation(self, name):
        ns = self.context()
        config = deepcopy(ns['CONFIG_TEXTOS_9_NIVEIS'])
        config['escala'] = self.pipeline[name].model_dump(mode='json')
        config.update(arquivo=str(ROOT / config['arquivo']), dividir_em_chunks=False, tentativas=1, pausa_segundos=0, n_bootstrap=200)
        runtime = ns['_runtime_textos9'](config)
        runtime['ns']['display'] = lambda *args, **kwargs: None
        prepared = runtime['ns']['preparar_textos_teste'](config)[:2]
        self.assertEqual(len(prepared), 2)
        scale = runtime['ns']['validar_escala'](config['escala'])
        calls = []
        async def classify(text):
            calls.append(text)
            if text == prepared[0]['chunks'][0]: raise ValueError('falha simulada')
            return {'model': 'simulado', 'answers': {k: v for axis in scale.rubricas_por_eixo for k, v in {
                f'{axis}_relevancia': {'choice': 'A', 'probabilities': {'A': .99, 'B': .01}},
                f'{axis}_polaridade': {'probabilities': {str(i): int(i == len(scale.niveis)-1) for i in range(len(scale.niveis))}, 'confidence': .99},
            }.items()}}, None
        pipeline = ns['_PipelineTextos9'](runtime, config, classificar=classify)
        context = {'escala': scale.model_dump(mode='json'), 'escala_hash': scale.hash}
        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / 'protocolo.json').write_text(json.dumps(context), encoding='utf-8')
            results = await runtime['ns']['avaliar_textos_teste'](prepared, pipeline, context, config, output)
            self.assertIsNotNone(results[0]['erro']); self.assertIsNone(results[1]['erro'])
            self.assertEqual(len(calls), 2)
            saved = json.loads((output / prepared[1]['id'] / 'resultado.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['registros'][0]['escala_hash'], scale.hash)
            self.assertTrue((output / prepared[1]['id'] / 'fluxograma.html').is_file())
            self.assertIn('100 × valor da alternativa', (output / prepared[1]['id'] / 'fluxograma.html').read_text(encoding='utf-8'))
            runtime['relatorio'].salvar_relatorio_textos(results, output)
            self.assertTrue(list(output.glob('*.html')))

    def test_comparison_separates_document_sizes_and_rejects_changed_chunks(self):
        ns = self.pipeline
        rounds = {}
        for name in ('ESCALA_5_NIVEIS', 'ESCALA_9_NIVEIS'):
            scale = ns[name]
            d = {**ns['decisao_vazia']('economic'), 'relevante': True, 'nivel': 1, 'valor_0_100': ns['valor_nivel'](1, scale), 'classe': 'A', 'status': 'direcional', 'metodo': 'jev_ordinal', 'modelo': 'simulado'}
            record = {'texto': 'Texto fixo.', 'eixos': {axis: d for axis in ns['AXIS_SPECS']}, 'escala': scale.model_dump(mode='json'), 'config': {'escala': scale.model_dump(mode='json')}, 'latencia_total_s': .1, 'chamadas_jev': 1}
            rounds[name] = {'curto': [record], 'longo': [record, deepcopy(record)]}
        comparison = ns['comparar_rodadas_escalas'](rounds)
        self.assertEqual(set(comparison['documentos']['base']), {'trecho único', 'múltiplos trechos'})
        self.assertEqual(len(comparison['mudancas_para_revisao']), 12)
        self.assertIn(0, comparison['frequencias']['contagem'].to_list())
        rounds['ESCALA_9_NIVEIS']['curto'][0]['texto'] = 'Outro texto.'
        with self.assertRaises(ValueError): ns['comparar_rodadas_escalas'](rounds)


if __name__ == '__main__': unittest.main()
