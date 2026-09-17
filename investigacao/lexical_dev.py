"""Baseline lexical em temas reservados, usando somente treino/dev.

Santos/Paraboni (2019), Moral Stance Recognition and Polarity Classification
from Twitter and Elicited Text, §§3.3.1–3.3.3, ACL R19-1123: n-gramas e
classificadores. Adaptação: TF-IDF sem seleção ANOVA, regressão logística,
pesos por (tema,classe); não é reprodução dos resultados originais.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from .experimentos import manifest
from .protocolo import classification_metrics, validate_corpus, write_json


def topic_weights(rows):
    """R4: adaptação local, equaliza massa de cada tema/classe usando treino apenas."""
    counts = Counter((r['target'], r['label']) for r in rows)
    return np.array([len(rows) / (len(counts) * counts[(r['target'], r['label'])]) for r in rows])


def run(data, output):
    """R4: corpus auditado, vocabulário só treino sem tema de avaliação dev."""
    if output.exists():
        raise ValueError('Use saída nova')
    started = time.perf_counter()
    corpus = data / 'corpus.jsonl'
    rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    meta = json.loads((data / 'corpus.meta.json').read_text(encoding='utf-8'))
    validate_corpus(rows, meta)
    rows = [r for r in rows if r['split'] in {'train', 'dev'}]
    protocol = {'data': 'train/dev only; dev target excluded from train', 'cs': [1., 10.],
                'ngrams': {'char': [3, 5], 'word': [1, 2]}, 'min_df': 2, 'max_features': 50000,
                'weights': 'equal topic/class mass', 'features': 'text only',
                'selection': 'mean_topic_ba, then min_topic_ba', 'test_evaluated': False}
    write_json(output / 'protocol.json', protocol)
    results = []
    for target in sorted({r['target'] for r in rows}):
        train = [r for r in rows if r['split'] == 'train' and r['target'] != target]
        dev = [r for r in rows if r['split'] == 'dev' and r['target'] == target]
        assert not {r['author_id'] for r in train} & {r['author_id'] for r in dev}
        for analyzer, ngrams in [('char', (3, 5)), ('word', (1, 2))]:
            vectorizer = TfidfVectorizer(analyzer=analyzer, ngram_range=ngrams, min_df=2,
                                         max_features=50000, sublinear_tf=True)
            x = vectorizer.fit_transform([r['text'] for r in train])
            d = vectorizer.transform([r['text'] for r in dev])
            for c in (1., 10.):
                model = LogisticRegression(C=c, max_iter=2000, random_state=13)
                model.fit(x, [r['label'] for r in train], sample_weight=topic_weights(train))
                p = model.predict(d)
                results.extend({'id': r['id'], 'target': target, 'truth': r['label'],
                                'prediction': str(y), 'candidate': f'{analyzer}_C{c}'} for r, y in zip(dev, p))
        print('Concluído:', target, flush=True)
    metrics = []
    for candidate in sorted({r['candidate'] for r in results}):
        s = [r for r in results if r['candidate'] == candidate]
        topics = []
        for t in sorted({r['target'] for r in s}):
            z = [r for r in s if r['target'] == t]
            topics.append({'target': t, **classification_metrics([r['truth'] for r in z], [r['prediction'] for r in z])})
        mean = float(np.mean([r['balanced_accuracy'] for r in topics])); minimum = min(r['balanced_accuracy'] for r in topics)
        metrics.append({'candidate': candidate, 'mean_topic_ba': mean, 'min_topic_ba': minimum,
                        'satisfies_provisional_criterion': mean >= .75 and minimum >= .6,
                        'topics': topics, 'global': classification_metrics([r['truth'] for r in s], [r['prediction'] for r in s])})
    metrics.sort(key=lambda r: (-r['mean_topic_ba'], -r['min_topic_ba']))
    write_json(output / 'predictions.json', results)
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'manifest.json', manifest(protocol, [corpus, Path(__file__)], started))
    print(json.dumps([{k:v for k,v in r.items() if k not in {'topics','global'}} for r in metrics], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.output)
