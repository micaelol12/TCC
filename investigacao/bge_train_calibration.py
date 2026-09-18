"""R4/R10: limiar BGE ajustado só em treino dos outros temas e avaliado no dev.

Calibração de fronteira, não probabilidade. Usa hipótese escolhida no dev anterior;
esta avaliação é exploratória e não valida seleção independente desse template.
"""
import json
from pathlib import Path
import time
import numpy as np
from .bge_dev import BinaryNLI
from .experimentos import manifest
from .nli_bilateral import hypotheses
from .protocolo import classification_metrics, write_json


def fit_threshold(rows):
    """R4: grade fixa de margem; BA média dos temas de treino, empate perto de zero."""
    if not rows or any(r['split'] != 'train' for r in rows):
        raise ValueError('Limiar usa somente treino')
    grid = []
    for threshold in np.linspace(-.5, .5, 21):
        topic_bas = []
        for t in sorted({r['target'] for r in rows}):
            s = [r for r in rows if r['target'] == t]
            m = classification_metrics([r['truth'] for r in s],
                ['favor' if r['score'] > threshold else 'against' for r in s])
            topic_bas.append(m['balanced_accuracy'])
        grid.append({'threshold': float(threshold), 'mean_topic_ba': float(np.mean(topic_bas))})
    return max(grid, key=lambda r: (r['mean_topic_ba'], -abs(r['threshold']))), grid


def run(root):
    """R4/R10: GPU só em treino; desenvolvimento reutilizado por ID, teste intocado."""
    import torch
    runs = root / 'analises/execucoes'
    output = runs / 'bge_train_calibration_20260917'
    if output.exists():
        raise ValueError('Saída já existe')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4); torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    corpus = root / 'analises/dados/brmoral_20260917/corpus.jsonl'
    all_rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    train = [r for r in all_rows if r['split'] == 'train']
    write_json(output / 'protocol.json', {'template': 'concordancia', 'threshold_grid': np.linspace(-.5,.5,21).tolist(),
               'threshold_fit': 'train excluding dev target', 'evaluation': 'dev', 'test_used': False})
    model = BinaryNLI(str(root / 'analises/modelos/bge-m3-zeroshot-v2'))
    predictions = []
    for i, row in enumerate(train):
        positive, negative = hypotheses(row['target'])['concordancia']
        pos = model.predict(row['text'], positive); neg = model.predict(row['text'], negative)
        predictions.append({'id': row['id'], 'split': 'train', 'target': row['target'], 'truth': row['label'],
                            'score': pos - neg, 'probabilities': [pos, neg]})
        if (i+1) % 200 == 0:
            write_json(output / 'train_progress.json', predictions)
            print(f'{i+1}/{len(train)} treino', flush=True)
    write_json(output / 'train_predictions.json', predictions)
    dev = json.loads((runs / 'bge_dev_gpu_20260917/predictions.json').read_text(encoding='utf-8'))
    decisions, selections, topics = [], [], []
    for target in sorted({r['target'] for r in dev}):
        selected, grid = fit_threshold([r for r in predictions if r['target'] != target])
        selections.append({'target': target, **selected, 'grid': grid})
        s = [r for r in dev if r['target'] == target]
        p = ['favor' if r['scores']['concordancia'] > selected['threshold'] else 'against' for r in s]
        decisions.extend({**r, 'prediction': y, 'threshold': selected['threshold']} for r,y in zip(s,p))
        topics.append({'target': target, **classification_metrics([r['truth'] for r in s],p)})
    mean = float(np.mean([r['balanced_accuracy'] for r in topics])); minimum=min(r['balanced_accuracy'] for r in topics)
    metrics={'mean_topic_ba':mean,'min_topic_ba':minimum,'satisfies_provisional_criterion':mean>=.75 and minimum>=.6,
             'topics':topics,'global':classification_metrics([r['truth'] for r in decisions],[r['prediction'] for r in decisions])}
    write_json(output / 'selections.json', selections);write_json(output / 'predictions.json',decisions)
    write_json(output / 'metrics.json',metrics)
    write_json(output / 'manifest.json',manifest({'model':model.info,'test_used':False},[corpus,Path(__file__)],started))
    print(json.dumps({k:v for k,v in metrics.items() if k!='topics'},indent=2))


if __name__ == '__main__':
    run(Path.cwd())
