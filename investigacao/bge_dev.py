"""R10: BGE zeroshot, Laurer et al. (2024), arXiv:2312.17543, §2.

Entailment vs not-entailment; esta última classe não é contradição. Classificação
bilateral compara apoio e oposição explícitos. Adaptação PT, FP16 e 512 tokens.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from .experimentos import manifest
from .nli_bilateral import hypotheses
from .protocolo import classification_metrics, connected_groups, grouped_bootstrap, write_json


class BinaryNLI:
    """R10: leitura de classes do config; probabilidades separadas para cada hipótese."""

    def __init__(self, path):
        """R4/R10: pesos locais, FP16 CUDA, classe not_entailment nunca renomeada."""
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True,
                        dtype=torch.float16).to('cuda').eval()
        labels = self.model.config.id2label
        if set(labels.values()) != {'entailment', 'not_entailment'}:
            raise ValueError('Classes desconhecidas')
        self.entailment = next(int(i) for i, v in labels.items() if v == 'entailment')
        self.info = {'name': 'MoritzLaurer/bge-m3-zeroshot-v2.0',
                     'revision': '9abf1c8aaeb82a2447809c20753ed0b106b76652',
                     'dtype': 'float16', 'device': 'cuda', 'max_length': 512,
                     'id2label': labels, 'pairs': 0, 'truncated': 0}

    def predict(self, text, hypothesis):
        """R10: inferência de par; contagem de truncamento antes de limitar a entrada."""
        import torch
        raw = self.tokenizer(text, hypothesis, truncation=False)['input_ids']
        self.info['pairs'] += 1
        self.info['truncated'] += len(raw) > 512
        inputs = self.tokenizer(text, hypothesis, truncation=True, max_length=512, return_tensors='pt').to('cuda')
        with torch.inference_mode():
            logits = self.model(**inputs).logits.float()
            p = logits.softmax(-1)[0]
        if not torch.isfinite(p).all():
            raise ValueError('Probabilidade não finita')
        return float(p[self.entailment].cpu())


def run(data, model_path, output):
    """R4/R10: somente dev, seleção por média BA entre temas; sem treino/teste."""
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
    protocol = {'split': 'dev', 'templates': ['nominal', 'concordancia'], 'max_length': 512,
                'selection': 'mean_topic_ba then min_topic_ba', 'no_test': True,
                'provisional_success': {'mean_topic_ba': .75, 'minimum_topic_ba': .6}}
    write_json(output / 'protocol.json', protocol)
    model = BinaryNLI(str(model_path))
    results = []
    for i, row in enumerate(rows):
        h = hypotheses(row['target'])
        probs = {f: [model.predict(row['text'], s) for s in h[f]] for f in ['nominal', 'concordancia']}
        scores = {f: p[0] - p[1] for f, p in probs.items()}
        scores['ensemble'] = float(np.mean(list(scores.values())))
        results.append({'id': row['id'], 'target': row['target'], 'truth': row['label'],
                        'probabilities': probs, 'scores': scores})
        if (i + 1) % 100 == 0:
            write_json(output / 'progress.json', {'completed': i + 1, 'total': len(rows)})
            print(f'{i+1}/{len(rows)} desenvolvimento', flush=True)
    metrics = []
    for candidate in results[0]['scores']:
        topics = []
        for target in sorted({r['target'] for r in results}):
            s = [r for r in results if r['target'] == target]
            topics.append({'target': target, **classification_metrics([r['truth'] for r in s],
                           ['favor' if r['scores'][candidate] > 0 else 'against' for r in s])})
        mean = float(np.mean([r['balanced_accuracy'] for r in topics])); minimum = min(r['balanced_accuracy'] for r in topics)
        metrics.append({'candidate': candidate, 'mean_topic_ba': mean, 'min_topic_ba': minimum,
                        'satisfies_provisional_criterion': mean >= .75 and minimum >= .6,
                        'topics': topics, 'global': classification_metrics([r['truth'] for r in results],
                        ['favor' if r['scores'][candidate] > 0 else 'against' for r in results])})
    metrics.sort(key=lambda r: (-r['mean_topic_ba'], -r['min_topic_ba']))
    write_json(output / 'predictions.json', results)
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'selection.json', metrics[0])
    write_json(output / 'manifest.json', manifest({**protocol, 'model': model.info},
               [corpus, Path(__file__), model_path / 'config.json'], started))
    print(json.dumps([{k:v for k,v in r.items() if k not in {'topics','global'}} for r in metrics], indent=2))


def evaluate_selected(data, model_path, selected_dev, old_run, output, training_calibration=None):
    """R4/R8/R10: congela escolha dev antes da avaliação, sem buscar no teste."""
    import torch
    if output.exists():
        raise ValueError('Use saída nova')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    selection = json.loads((selected_dev / 'selection.json').read_text(encoding='utf-8'))
    candidate = selection['candidate']
    if candidate not in {'nominal', 'concordancia', 'ensemble'}:
        raise ValueError('Candidato desconhecido')
    thresholds = {}
    if training_calibration:
        if candidate != 'concordancia':
            raise ValueError('Limiar de treino foi ajustado para concordancia')
        thresholds = {r['target']: r['threshold'] for r in json.loads(
            (training_calibration / 'selections.json').read_text(encoding='utf-8'))}
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    corpus = data / 'corpus.jsonl'
    rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    rows = [r for r in rows if r['split'] == 'test']
    protocol = {'selected_dev': str(selected_dev), 'selection': selection,
                'candidate': candidate, 'threshold': 0., 'topic_thresholds': thresholds,
                'test_previously_inspected': True,
                'no_tuning_on_test': True, 'mean_topic_ba_criterion': .75, 'min_topic_ba_criterion': .6}
    write_json(output / 'frozen_selection.json', protocol)
    model = BinaryNLI(str(model_path))
    results = []
    forms = ['nominal', 'concordancia'] if candidate == 'ensemble' else [candidate]
    for i, row in enumerate(rows):
        h = hypotheses(row['target'])
        probs = {f: [model.predict(row['text'], s) for s in h[f]] for f in forms}
        score = float(np.mean([p[0] - p[1] for p in probs.values()]))
        results.append({'id': row['id'], 'target': row['target'], 'truth': row['label'],
                        'family_id': row['family_id'], 'probabilities': probs, 'score': score,
                        'threshold': thresholds.get(row['target'], 0.),
                        'prediction': 'favor' if score > thresholds.get(row['target'], 0.) else 'against'})
        if (i + 1) % 100 == 0:
            print(f'{i+1}/{len(rows)} teste com configuração congelada', flush=True)
    topics = []
    for target in sorted({r['target'] for r in results}):
        s = [r for r in results if r['target'] == target]
        topics.append({'target': target, **classification_metrics([r['truth'] for r in s], [r['prediction'] for r in s])})
    mean = float(np.mean([r['balanced_accuracy'] for r in topics])); minimum = min(r['balanced_accuracy'] for r in topics)
    metrics = {'candidate': candidate, 'mean_topic_ba': mean, 'min_topic_ba': minimum,
               'satisfies_provisional_criterion': mean >= .75 and minimum >= .6,
               'topics': topics, 'global': classification_metrics([r['truth'] for r in results], [r['prediction'] for r in results])}
    old = json.loads((old_run / 'predictions.json').read_text(encoding='utf-8'))
    old = {r['id']: r for r in old if r['method'] == 'nli_posicao_autor'}
    if set(old) != {r['id'] for r in results} or any(old[r['id']]['truth'] != r['truth'] for r in results):
        raise ValueError('Comparador incompatível')
    interval = grouped_bootstrap([r['truth'] for r in results], [r['prediction'] for r in results],
                                [old[r['id']]['prediction'] for r in results], connected_groups(rows), seed=13)
    write_json(output / 'predictions.json', results)
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'interval.json', interval)
    write_json(output / 'manifest.json', manifest({**protocol, 'model': model.info},
               [corpus, selected_dev / 'selection.json', old_run / 'predictions.json', Path(__file__)], started))
    print(json.dumps({k:v for k,v in metrics.items() if k != 'topics'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--selected-dev', type=Path)
    parser.add_argument('--old-run', type=Path)
    parser.add_argument('--training-calibration', type=Path)
    args = parser.parse_args()
    if args.selected_dev:
        if not args.old_run:
            parser.error('--old-run obrigatório para avaliação')
        evaluate_selected(args.data, args.model_path, args.selected_dev, args.old_run, args.output, args.training_calibration)
    else:
        run(args.data, args.model_path, args.output)
