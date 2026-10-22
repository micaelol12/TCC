"""Offline notebook integration check; never executes the real API cells.

Run from the repository root: .venv/Scripts/python.exe analise_jev_llm/test_evidencias_pipeline.py
Pass --save-demo to save only the new simulated demonstration output.
"""
import ast
import asyncio
from contextlib import redirect_stdout
import inspect
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / 'Pipeline - Passo a Passo.ipynb'


async def check(save_demo=False):
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    namespace = {'__name__': '__notebook_test__'}
    saved_outputs = []
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), str(NOTEBOOK), 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    # The didactic prefix contains only declarations and explicit simulated clients.
    # Do not run document processing, credentials or any real execution section.
    for cell in notebook['cells']:
        source = ''.join(cell['source'])
        if source.startswith('## Construir uma avaliação'):
            break
        if cell['cell_type'] != 'code':
            continue
        if source.startswith(('QUESTIONS =', 'planos_governo =', 'from google import')):
            continue
        outputs = []

        def display(value):
            data = {'text/plain': repr(value)}
            if hasattr(value, 'to_html'):
                data['text/html'] = value.to_html(index=False)
            outputs.append({'output_type': 'display_data', 'data': data, 'metadata': {}})

        namespace['display'] = display
        stream = io.StringIO()
        with redirect_stdout(stream):
            result = eval(compile(source, cell['id'], 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), namespace)
            if inspect.isawaitable(result):
                await result
        if cell['id'] == 'lab-evidencias-demo':
            if stream.getvalue():
                outputs.append({'output_type': 'stream', 'name': 'stdout', 'text': stream.getvalue()})
            saved_outputs = outputs
            if save_demo:
                cell['outputs'] = outputs
                cell['execution_count'] = 1
    assert saved_outputs, 'Simulated demonstration did not run'
    baseline_pipeline = namespace['montar_simulacao']()
    text = namespace['TEXTO_DEMO']
    baseline = await baseline_pipeline.classificar(text)
    audit_pipeline = namespace['montar_simulacao']()
    audit_pipeline.config.update(semantic_evidence_check=True, jev_evidence_search=True)
    original_client = audit_pipeline.jev_client
    evidence_client = namespace['JevEvidenciasSimulado']()

    class CombinedFake:
        async def system_one(self, **kwargs):
            if any(key.endswith(('_where', '_relation', '_exists')) for key in kwargs['questions']):
                return await evidence_client.system_one(**kwargs)
            return await original_client.system_one(**kwargs)

    audit_pipeline.jev_client = CombinedFake()
    audited = await audit_pipeline.classificar(text)
    assert audited['chamadas_jev_evidencias'] == 1  # Only LLM economic evidence is eligible in this fixture.
    assert audited['eixos']['economic']['evidence_audit'][0]['status'] == 'contradiz'
    for axis, decision in baseline['eixos'].items():
        for key in ('relevante', 'nivel', 'valor_0_100', 'metodo'):
            assert audited['eixos'][axis][key] == decision[key], (axis, key)
    assert audited['motivos_fallback'] == baseline['motivos_fallback']
    if save_demo:
        NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Notebook: all cells compile; simulated demonstrations and cascade integration passed. No API calls.')


if __name__ == '__main__':
    asyncio.run(check('--save-demo' in sys.argv))
