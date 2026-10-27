"""Executa as demonstrações didáticas locais até o bloco de APIs, sem ler planos de governo."""
import ast
import asyncio
import contextlib
import io
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')


async def main():
    path = Path(__file__).resolve().parents[1] / 'Pipeline - Passo a Passo.ipynb'
    nb = json.loads(path.read_text(encoding='utf-8'))
    ns = {'__name__': 'local_notebook_demos'}
    count = 0
    for c in nb['cells']:
        source = ''.join(c['source'])
        if '--nine' in sys.argv:
            source = source.replace('ESCALA_ATUAL = ESCALA_5_NIVEIS', 'ESCALA_ATUAL = ESCALA_9_NIVEIS')
        if c['cell_type'] == 'markdown' and source.startswith('## Trocar os dublês'):
            break
        if c['cell_type'] != 'code' or source.startswith(('planos_governo =', 'plano_escolhido =')):
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            result = eval(compile(source, f'{path.name}:{c.get("id")}', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), ns)
            if result is not None: await result
        count += 1
    ns['plt'].close('all')
    print(f'{count} células didáticas locais executadas; zero chamadas remotas.')


if __name__ == '__main__': asyncio.run(main())
