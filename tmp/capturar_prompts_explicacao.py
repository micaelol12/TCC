"""Capture example LLM inputs locally, without creating provider clients."""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'app' / 'api')]
from app.experiment_config import ExperimentConfig
from app.pipeline.strategies import ask_llm
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook

TEXT = 'Vamos ampliar os programas de transferência de renda para famílias de baixa renda.'
AXES = ['economic', 'diplomatic', 'state', 'society']


class Capture:
    model = 'sabia-4'
    ultima_chamada = None

    def __init__(self):
        self.responses = self
        self.request = None

    def capture(self, model, prompt, instructions, schema):
        self.request = {
            'model': model, 'instructions': instructions,
            'input': json.loads(prompt), 'response_schema': schema.model_json_schema(),
        }
        return schema.model_validate({'eixos': [
            {'eixo': axis, 'relevante': False, 'nivel': None, 'evidencia': ''}
            for axis in AXES
        ]})

    async def parse(self, **kwargs):
        parsed = self.capture(kwargs['model'], kwargs['input'], kwargs['instructions'], kwargs['text_format'])
        return SimpleNamespace(model=self.model, output_parsed=parsed)

    async def generate(self, prompt, response_schema, instructions=None):
        return self.capture(self.model, prompt, instructions, response_schema)


async def main():
    print('Iniciando captura local.', flush=True)
    output = ROOT / 'output' / 'explicacao_llm'
    output.mkdir(parents=True, exist_ok=True)
    config = ExperimentConfig.model_validate(json.loads(
        (ROOT / 'app/api/analysis-config.json').read_text(encoding='utf-8-sig')))
    print('Configuracao carregada.', flush=True)
    api = Capture()
    await ask_llm(api, config.llm_model, TEXT, AXES, config.escala,
                  config.contexto_posicao_politica, config.axis_specs)
    api.request = {'nota': (
        'Exemplo local capturado de ask_llm com os quatro eixos e analysis-config.json, '
        'sem overrides de ambiente ou Lab. input está expandido como objeto para leitura; '
        'a função o envia como string JSON. Nenhuma chamada de rede foi feita. '
        'Nenhuma classificação real está incluída.'), **api.request}
    (output / 'api_4_eixos.json').write_text(json.dumps(api.request, ensure_ascii=False, indent=2), encoding='utf-8')
    print('API capturada.', flush=True)

    ns = carregar_pipeline_notebook()
    notebook = Capture()
    pipeline = ns['CascataJevLLM2Polos'](None, notebook, ns['AXIS_SPECS'])
    await ns['consultar_llm'](pipeline, TEXT, AXES)
    assert notebook.request is not None
    notebook.request = {'nota': (
        'Exemplo local capturado de consultar_llm com a escala base do notebook (cinco níveis). '
        'Configurações de seções e células posteriores podem substituir contexto e escala. '
        'input está expandido como objeto para leitura. Nenhuma chamada de rede foi feita. '
        'Nenhuma classificação real está incluída.'), **notebook.request}
    (output / 'notebook_base_4_eixos.json').write_text(json.dumps(notebook.request, ensure_ascii=False, indent=2), encoding='utf-8')
    for name in ('api_4_eixos.json', 'notebook_base_4_eixos.json'):
        data = json.loads((output / name).read_text(encoding='utf-8'))
        print(name, 'bytes=', (output / name).stat().st_size,
              'axes=', list(data['input']['rubricas']),
              'instructions_chars=', len(data['instructions']), flush=True)
    print('Notebook base scale:', ns['ESCALA_ATUAL'].id, flush=True)


if __name__ == '__main__':
    # The fake client completes synchronously; avoid creating a networking event loop.
    try:
        main().send(None)
    except StopIteration:
        pass
