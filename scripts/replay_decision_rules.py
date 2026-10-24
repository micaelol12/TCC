"""Compare decision rules on saved JEV distributions without provider calls."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app' / 'api'))
from app.pipeline.domain import decidir_jev, motivos_fallback


def compare(path, axis):
    source = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() == '.html':
        match = re.search(r'<script id="data" type="application/json">(.*?)</script>', source, re.S)
        if not match:
            raise ValueError(f'{path}: fluxograma sem dados JSON.')
        source = match.group(1)
    data = json.JSONDecoder().raw_decode(source.lstrip())[0]
    rows = []
    for index, record in enumerate(data.get('registros', [])):
        config = deepcopy(record['config'])
        scale = config.get('escala') or record.get('escala') or data.get('escala')
        config['escala'] = scale
        original = record['eixos_jev'][axis]
        levels = original['probabilities_nivel']
        if not levels or original.get('probabilities_relevancia') is None:
            raise ValueError(f'{path}: distribuição original do JEV indisponível.')
        if config['primitiva_polaridade'] == 'score':
            levels = {str(i): levels[n['chave']] for i, n in enumerate(scale['niveis'])}
        rel = original['probabilities_relevancia']
        answers = {
            f'{axis}_relevancia': {'choice': 'A' if original['relevante'] else 'B', 'probabilities': rel, 'noul': rel['A']},
            f'{axis}_polaridade': {'probabilities': levels, 'confidence': original['confianca_nivel']},
        }
        decisions = {}
        for rule in ('nivel', 'polo_primeiro'):
            config['regra_decisao'] = rule
            decision = decidir_jev(axis, answers, config)
            decisions[rule] = {
                **{key: decision[key] for key in ('nivel', 'valor_0_100', 'nivel_jev_bruto', 'probabilities_abc', 'margem_grupo', 'probabilidade_nivel_condicional')},
                'motivos_incerteza': motivos_fallback(decision, config),
            }
        rows.append({'arquivo': str(path), 'chunk': index + 1, 'eixo': axis, 'escala': scale['id'], 'comparacao': decisions})
    if not rows:
        raise ValueError(f'{path}: use o fluxograma completo; o snapshot de parâmetros não inclui as distribuições.')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--axis', choices=('economic', 'diplomatic', 'state', 'society'), default='diplomatic')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = {'tipo': 'replay-local-sem-inferencia', 'chamadas_provedores': 0,
                  'nota': 'Compara somente a regra sobre distribuições já salvas. Não comprova correção semântica nem calibração.',
                  'resultados': [row for path in args.files for row in compare(path, args.axis)]}
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(output)
        else:
            sys.stdout.reconfigure(encoding='utf-8')
            print(output, end='')
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__': main()
