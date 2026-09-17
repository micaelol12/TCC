"""R4/R7: investigação bilateral no desenvolvimento, sem consultar teste.

Yin et al. (2019), §3, ACL D19-1404 fundamenta hipóteses de classe; comparar
apoio/oposição e agregar templates é adaptação local. Não reajusta pesos.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from .experimentos import manifest
from .modelos import NLI
from .protocolo import classification_metrics, write_json
from .temas_reservados import PROPOSITIONS


def hypotheses(target):
    """R7: hipóteses simétricas de classe; não altera a proposição com negação."""
    p = PROPOSITIONS[target]
    return {
        'nominal': [f'O autor é favorável a {target}.', f'O autor é contrário a {target}.'],
        'concordancia': [f'O autor concorda com a seguinte afirmação: {p}',
                         f'O autor discorda da seguinte afirmação: {p}'],
        'defesa': [f'O texto defende a seguinte posição: {p}',
                   f'O texto rejeita a seguinte posição: {p}'],
    }


def score_candidates(probabilities):
    """R7: diferenças entailment e E−C, pesos iguais, sem usar rótulos."""
    scores = {}
    for form, (positive, negative) in probabilities.items():
        scores[form + '_entailment'] = positive['entailment'] - negative['entailment']
        scores[form + '_signed'] = (positive['entailment'] - positive['contradiction'] -
                                   negative['entailment'] + negative['contradiction']) / 2
    for variant in ['entailment', 'signed']:
        scores['ensemble_' + variant] = float(np.mean([scores[f + '_' + variant] for f in probabilities]))
    scores['baseline_nominal'] = probabilities['nominal'][0]['entailment'] - probabilities['nominal'][0]['contradiction']
    scores['baseline_autor'] = probabilities['concordancia'][0]['entailment'] - probabilities['concordancia'][0]['contradiction']
    return scores


def run(data, output):
    """R4: desenvolvimento apenas; critério pré-fixado por tema e pesos congelados."""
    import torch
    if output.exists():
        raise ValueError('Use saída nova')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    corpus = data / 'corpus.jsonl'
    rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    rows = [r for r in rows if r['split'] == 'dev']
    protocol = {'data_used': 'dev_only', 'threshold': 0., 'hypotheses': {t: hypotheses(t) for t in PROPOSITIONS},
                'selection': 'mean balanced accuracy across topics; tie minimum topic BA',
                'provisional_success': {'mean_topic_ba': .75, 'minimum_topic_ba': .60},
                'success_is_development_only': True, 'no_test_evaluation': True}
    write_json(output / 'protocol.json', protocol)
    model = NLI(revision='8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c', device='cuda', batch_size=1, low_vram=True)
    results = []
    for i, row in enumerate(rows):
        h = hypotheses(row['target'])
        probabilities = {f: model.predict([(row['text'], s) for s in pair]) for f, pair in h.items()}
        results.append({'id': row['id'], 'target': row['target'], 'truth': row['label'],
                        'family_id': row['family_id'], 'probabilities': probabilities,
                        'scores': score_candidates(probabilities)})
        if (i + 1) % 100 == 0:
            write_json(output / 'progress.json', {'completed': i + 1, 'total': len(rows)})
            print(f'{i+1}/{len(rows)} exemplos de desenvolvimento', flush=True)
    write_json(output / 'predictions.json', results)
    metrics = []
    for candidate in results[0]['scores']:
        topics = []
        for target in sorted(PROPOSITIONS):
            subset = [r for r in results if r['target'] == target]
            topics.append({'target': target, **classification_metrics([r['truth'] for r in subset],
                           ['favor' if r['scores'][candidate] > 0 else 'against' for r in subset])})
        mean = float(np.mean([r['balanced_accuracy'] for r in topics]))
        minimum = min(r['balanced_accuracy'] for r in topics)
        metrics.append({'candidate': candidate, 'mean_topic_ba': mean, 'min_topic_ba': minimum,
                        'satisfies_provisional_criterion': mean >= .75 and minimum >= .6,
                        'topics': topics, 'global': classification_metrics([r['truth'] for r in results],
                        ['favor' if r['scores'][candidate] > 0 else 'against' for r in results])})
    metrics.sort(key=lambda r: (-r['mean_topic_ba'], -r['min_topic_ba']))
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'selection.json', metrics[0])
    write_json(output / 'manifest.json', manifest({**protocol, 'nli': model.info}, [corpus, Path(__file__)], started))
    print(json.dumps([{k: r[k] for k in ('candidate', 'mean_topic_ba', 'min_topic_ba', 'satisfies_provisional_criterion')} for r in metrics], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.output)
