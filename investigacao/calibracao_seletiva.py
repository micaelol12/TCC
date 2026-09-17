"""R4/R7: seleção exploratória de limiares, sem calibrar probabilidades.

Kapoor/Narayanan (2023), DOI 10.1016/j.patter.2023.100804: isolamento de ajuste;
Yin et al. (2019), §3, ACL D19-1404: inferência por hipótese. Critérios de
80% de acerto e 25% de cobertura são decisões locais, não garantias dos artigos.
"""
import argparse
import json
from pathlib import Path
import time

from .experimentos import manifest
from .modelos import NLI
from .protocolo import digest, evidence_state, validate_corpus, write_json
from .temas_reservados import PROPOSITIONS

METHODS = ('nli_proposicao', 'nli_posicao_autor')
THRESHOLDS = (.5, .6, .7, .8, .9, .95)
MARGINS = (0., .1, .2, .3, .4)


def apply_policy(row, threshold, margin, abstain=False):
    """R7: E/C/N e abstenção; não interpreta probabilidade como intensidade."""
    state = 'incerta' if abstain else evidence_state([
        {**row['probabilities'], 'text': row['id']}], threshold, margin)
    return {**row, 'state': state}


def selective_metrics(rows):
    """R4: denominadores explícitos; classes verdadeiras ausentes não somem."""
    accepted = [r for r in rows if r['state'] in {'favoravel', 'contraria'}]
    correct = sum(r['prediction'] == r['truth'] for r in accepted)
    return {'n': len(rows), 'accepted': len(accepted), 'correct': correct,
            'errors': len(accepted) - correct, 'coverage': len(accepted) / len(rows) if rows else 0.,
            'accepted_accuracy': correct / len(accepted) if accepted else None,
            'accepted_by_truth': {label: sum(r['truth'] == label for r in accepted) for label in ('favor', 'against')}}


def choose(dev_rows, held_target):
    """R4: somente dev de outros temas; maior cobertura sujeita a restrições.

    >=80% acerto empírico, >=25% cobertura, >=10 aceitos por classe verdadeira.
    Empate: maior acerto, menor limiar/margem, ordem fixa de métodos. Sem candidato:
    abster em todos os casos, sem relaxar condições ao ver os resultados.
    """
    if not dev_rows or any(r.get('split') != 'dev' for r in dev_rows):
        raise ValueError('Seleção exige exclusivamente desenvolvimento')
    if any(r['target'] == held_target for r in dev_rows):
        raise ValueError('Tema reservado presente na seleção')
    candidates = []
    for method in METHODS:
        rows = [r for r in dev_rows if r['method'] == method]
        if not rows:
            raise ValueError('Comparador ausente no desenvolvimento')
        for threshold in THRESHOLDS:
            for margin in MARGINS:
                metric = selective_metrics([apply_policy(r, threshold, margin) for r in rows])
                eligible = (metric['accepted_accuracy'] is not None and metric['accepted_accuracy'] >= .8
                            and metric['coverage'] >= .25 and min(metric['accepted_by_truth'].values()) >= 10)
                candidates.append({'method': method, 'threshold': threshold, 'margin': margin,
                                   'eligible': eligible, 'dev': metric})
    valid = [r for r in candidates if r['eligible']]
    if not valid:
        return {'abstain_all': True, 'reason': 'Nenhum candidato satisfaz os critérios no dev'}, candidates
    selected = max(valid, key=lambda r: (r['dev']['coverage'], r['dev']['accepted_accuracy'],
                                        -r['threshold'], -r['margin'], -METHODS.index(r['method'])))
    return {**selected, 'abstain_all': False}, candidates


def run(data, natural_run, output):
    """R4/R7: dev inferido na GPU; seleção persistida antes de ler previsões teste."""
    import torch
    if output.exists():
        raise ValueError('Use uma pasta nova')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    corpus, metadata = data / 'corpus.jsonl', data / 'corpus.meta.json'
    rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    meta = json.loads(metadata.read_text(encoding='utf-8'))
    validate_corpus(rows, meta)
    source_manifest = json.loads((natural_run / 'manifest.json').read_text(encoding='utf-8'))
    if digest(corpus.read_text(encoding='utf-8')) not in source_manifest['input_hashes'].values():
        raise ValueError('Corpus diferente da rodada natural')
    protocol = {'thresholds': THRESHOLDS, 'margins': MARGINS, 'min_accuracy_dev': .8,
                'min_coverage_dev': .25, 'min_accepted_each_truth_class': 10,
                'methods': METHODS, 'test_previously_inspected': True,
                'probabilities_calibrated': False, 'no_guarantee_of_test_risk': True,
                'fallback': 'abstain_all', 'propositions': PROPOSITIONS}
    write_json(output / 'protocol.json', protocol)
    dev = [r for r in rows if r['split'] == 'dev']
    model = NLI(revision='8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c', device='cuda', batch_size=1, low_vram=True)
    development = []
    for method in METHODS:
        hypotheses = [PROPOSITIONS[r['target']] if method == 'nli_proposicao' else
                      f"O autor concorda com a seguinte afirmação: {PROPOSITIONS[r['target']]}" for r in dev]
        probs = model.predict([(r['text'], h) for r, h in zip(dev, hypotheses)])
        for row, p in zip(dev, probs):
            development.append({**{k: row[k] for k in ('id', 'target', 'split', 'author_id', 'family_id')},
                                'truth': row['label'], 'method': method, 'probabilities': p,
                                'prediction': 'favor' if p['entailment'] > p['contradiction'] else 'against'})
    write_json(output / 'development_predictions.json', development)
    selections = {}
    for target in sorted(PROPOSITIONS):
        subset = [r for r in development if r['target'] != target]
        selection, grid = choose(subset, target)
        selections[target] = {**selection, 'development_ids': sorted({r['id'] for r in subset})}
        write_json(output / f'grid_{len(selections)}.json', {'held_target': target, 'candidates': grid})
    write_json(output / 'frozen_selections.json', selections)
    # R4: leitura do teste somente depois de congelar todas as seleções.
    test_predictions = json.loads((natural_run / 'predictions.json').read_text(encoding='utf-8'))
    test_rows = {r['id']: r for r in rows if r['split'] == 'test'}
    evaluated = []
    for row in test_predictions:
        if row['method'] not in METHODS:
            continue
        original = test_rows[row['id']]
        if original['label'] != row['truth'] or original['target'] != row['target']:
            raise ValueError('Predição não corresponde ao corpus')
        evaluated.append({**apply_policy(row, .7, .2), 'policy': row['method'] + '_fixo'})
        selected = selections[row['target']]
        if selected['abstain_all']:
            if row['method'] == METHODS[0]:
                evaluated.append({**apply_policy(row, .7, .2, True), 'policy': 'selecionada_dev'})
        elif row['method'] == selected['method']:
            evaluated.append({**apply_policy(row, selected['threshold'], selected['margin']), 'policy': 'selecionada_dev'})
    metrics = []
    for policy in sorted({r['policy'] for r in evaluated}):
        for target in [None, *sorted(PROPOSITIONS)]:
            subset = [r for r in evaluated if r['policy'] == policy and (target is None or r['target'] == target)]
            if target is None and {r['id'] for r in subset} != set(test_rows):
                raise ValueError('Avaliação deve conter todos os IDs de teste')
            metrics.append({'policy': policy, 'target': target, **selective_metrics(subset)})
    write_json(output / 'test_decisions.json', evaluated)
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'manifest.json', manifest({**protocol, 'nli': model.info},
               [corpus, metadata, natural_run / 'predictions.json', Path(__file__)], started))
    print(json.dumps([r for r in metrics if r['target'] is None], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--natural-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.natural_run, args.output)
