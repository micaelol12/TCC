"""R4/R7/R10: média fixa de margens NLI; adaptação experimental no dev.

Não há alegação de equivalência de calibração entre arquiteturas. Pesos 1/2
fixados antes de observar a combinação; nenhuma escolha usando teste.
"""
import json
from pathlib import Path
import numpy as np
from .protocolo import classification_metrics, write_json


def combine(left, right):
    """R4: união por ID, verifica alvo/rótulo, média aritmética com pesos fixos."""
    left = {r['id']: r for r in left}
    right = {r['id']: r for r in right}
    if set(left) != set(right):
        raise ValueError('IDs diferentes')
    results = []
    for key, l in left.items():
        r = right[key]
        if l['target'] != r['target'] or l['truth'] != r['truth']:
            raise ValueError('Alvo/rótulo incompatível')
        score = (l['scores']['baseline_autor'] + r['scores']['concordancia']) / 2
        results.append({'id': key, 'target': l['target'], 'truth': l['truth'], 'score': score,
                        'prediction': 'favor' if score > 0 else 'against'})
    return results


def run(root):
    """R4: protocolo primeiro; escolhas dos componentes vieram somente do dev."""
    runs = root / 'analises/execucoes'
    output = runs / 'ensemble_dev_20260917'
    if output.exists():
        raise ValueError('Saída já existe')
    write_json(output / 'protocol.json', {'weights': [.5, .5], 'threshold': 0., 'split': 'dev',
        'components': ['mdeberta baseline_autor', 'bge concordancia'], 'test_used': False,
        'success': {'mean_topic_ba': .75, 'min_topic_ba': .6}})
    left = json.loads((runs / 'nli_bilateral_dev_gpu_20260917/predictions.json').read_text(encoding='utf-8'))
    right = json.loads((runs / 'bge_dev_gpu_20260917/predictions.json').read_text(encoding='utf-8'))
    results = combine(left, right)
    topics = []
    for target in sorted({r['target'] for r in results}):
        s = [r for r in results if r['target'] == target]
        topics.append({'target': target, **classification_metrics([r['truth'] for r in s], [r['prediction'] for r in s])})
    mean = float(np.mean([r['balanced_accuracy'] for r in topics])); minimum = min(r['balanced_accuracy'] for r in topics)
    metrics = {'mean_topic_ba': mean, 'min_topic_ba': minimum,
               'satisfies_provisional_criterion': mean >= .75 and minimum >= .6,
               'topics': topics, 'global': classification_metrics([r['truth'] for r in results], [r['prediction'] for r in results])}
    write_json(output / 'predictions.json', results)
    write_json(output / 'metrics.json', metrics)
    print(json.dumps({k:v for k,v in metrics.items() if k != 'topics'}, indent=2))


if __name__ == '__main__':
    run(Path.cwd())
