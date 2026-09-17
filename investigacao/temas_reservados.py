"""R3/R4/R6/R7/R8: avaliação exploratória com tema e autores reservados.

Silva e Paraboni (2023), §§3–4.1.2, artigo local; Kapoor/Narayanan (2023),
DOI 10.1016/j.patter.2023.100804; Yin et al. (2019), §3, ACL D19-1404.
Adaptação: remove um tema de treino/dev, preservando partições por autoria.
Não é teste cego: os textos de teste foram avaliados em rodadas anteriores.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import time

import numpy as np

from .dados import BRMORAL_TARGETS
from .experimentos import manifest
from .modelos import E5, NLI, conditioned, fit_head
from .protocolo import classification_metrics, connected_groups, evidence_state, grouped_bootstrap, validate_corpus, write_json

# R3/R7: verbalização explícita do alvo, não reanotação do texto. Fixada antes da execução.
PROPOSITIONS = dict(zip(BRMORAL_TARGETS.values(), [
    'O casamento entre pessoas do mesmo sexo deve ser permitido.',
    'O porte de armas deve ser legalizado.',
    'O aborto deve ser legalizado.',
    'A pena de morte deve ser adotada.',
    'As drogas devem ser legalizadas.',
    'A maioridade penal deve ser reduzida.',
    'As cotas raciais devem ser adotadas.',
    'As igrejas devem ser isentas de impostos.',
]))


def held_out(rows, target, metadata):
    """R4: remove tema de treino/dev; teste usa apenas tema retido, autores originais."""
    validate_corpus(rows, metadata)
    train = [r for r in rows if r['split'] == 'train' and r['target'] != target]
    dev = [r for r in rows if r['split'] == 'dev' and r['target'] != target]
    test = [r for r in rows if r['split'] == 'test' and r['target'] == target]
    validate_corpus(train + dev + test, metadata)
    if target in {r['target'] for r in train + dev}:
        raise ValueError('Tema reservado presente no ajuste')
    return train, dev, test


def evaluate(rows):
    """R3/R4: macro-F1 por classe, BA/MCC; cobertura e acerto seletivo separados."""
    accepted = [r for r in rows if r['state'] in {'favoravel', 'contraria'}]
    return {**classification_metrics([r['truth'] for r in rows], [r['prediction'] for r in rows]),
            'coverage': len(accepted) / len(rows),
            'accepted_accuracy': sum(r['truth'] == r['prediction'] for r in accepted) / len(accepted) if accepted else None}


def run(data, output):
    """R4/R6/R7: protocolo anterior à inferência; C só no dev dos outros temas."""
    import joblib
    import torch
    if output.exists():
        raise ValueError('Use diretório novo')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    corpus, metadata = data / 'corpus.jsonl', data / 'corpus.meta.json'
    rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    meta = json.loads(metadata.read_text(encoding='utf-8'))
    audit = validate_corpus(rows, meta)
    targets = sorted({r['target'] for r in rows})
    if set(targets) != set(PROPOSITIONS):
        raise ValueError('Temas não correspondem ao protocolo')
    protocol = {'experiment': 'leave_one_topic_out_with_disjoint_authors', 'seed': 13,
                'cs': [.01, .1, 1., 10.], 'head_threshold': .7, 'nli_threshold': .7, 'nli_margin': .2,
                'propositions': PROPOSITIONS, 'test_previously_inspected': True,
                'topic_held_out_from_train_and_dev': True, 'author_partitions_preserved': True,
                'encoder_finetuned': False, 'label_source': 'corpus_publico',
                'nli_variants': ['literal', 'O autor concorda com a seguinte afirmação: {proposition}']}
    write_json(output / 'protocol.json', protocol)
    write_json(output / 'audit.json', audit)
    e5 = E5(revision='d128750597153bb5987e10b1c3493a34e5a4502a', device='cuda', batch_size=1, low_vram=True)
    predictions, selections = [], []
    for i, target in enumerate(targets):
        train, dev, test = held_out(rows, target, meta)
        head, selection = fit_head(e5, train, dev, seed=13)
        folder = output / f'topic_{i}'
        folder.mkdir(parents=True, exist_ok=True)
        joblib.dump(head, folder / 'head.joblib')
        write_json(folder / 'partitions.json', {s: [r['id'] for r in group] for s, group in [('train', train), ('dev', dev), ('test', test)]})
        selections.append({'held_out': target, **selection, 'train_n': len(train), 'dev_n': len(dev), 'test_n': len(test)})
        probs = head.predict_proba(e5.encode([conditioned(r) for r in test]))
        majority = Counter(r['label'] for r in train).most_common(1)[0][0]
        for row, p in zip(test, probs):
            label = str(head.classes_[int(np.argmax(p))])
            common = {k: row[k] for k in ('id', 'author_id', 'family_id', 'target', 'label_source')}
            predictions.append({**common, 'truth': row['label'], 'method': 'e5_tema_reservado', 'prediction': label,
                                'state': ('favoravel' if label == 'favor' else 'contraria') if max(p) >= .7 else 'incerta',
                                'probabilities': dict(zip(head.classes_, map(float, p)))})
            predictions.append({**common, 'truth': row['label'], 'method': 'maioria_treino', 'prediction': majority,
                                'state': 'favoravel' if majority == 'favor' else 'contraria'})
        print(f'Tema {i + 1}/{len(targets)} concluído: {target}', flush=True)
    write_json(output / 'selections.json', selections)
    nli = NLI(revision='8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c', device='cuda', batch_size=1, low_vram=True)
    test = [r for r in rows if r['split'] == 'test']
    for method in ('nli_proposicao', 'nli_posicao_autor'):
        hypotheses = [PROPOSITIONS[r['target']] if method == 'nli_proposicao' else
                      f"O autor concorda com a seguinte afirmação: {PROPOSITIONS[r['target']]}" for r in test]
        probs = nli.predict([(r['text'], h) for r, h in zip(test, hypotheses)])
        for row, hypothesis, p in zip(test, hypotheses, probs):
            predictions.append({**{k: row[k] for k in ('id', 'author_id', 'family_id', 'target', 'label_source')},
                                'truth': row['label'], 'method': method, 'hypothesis': hypothesis,
                                'prediction': 'favor' if p['entailment'] > p['contradiction'] else 'against',
                                'state': evidence_state([{**p, 'text': row['text']}]), 'probabilities': p})
    metrics = []
    for method in sorted({r['method'] for r in predictions}):
        for target in [None, *targets]:
            subset = [r for r in predictions if r['method'] == method and (target is None or r['target'] == target)]
            metrics.append({'method': method, 'target': target, **evaluate(subset)})
    left = {r['id']: r['prediction'] for r in predictions if r['method'] == 'nli_posicao_autor'}
    right = {r['id']: r['prediction'] for r in predictions if r['method'] == 'nli_proposicao'}
    interval = grouped_bootstrap([r['label'] for r in test], [left[r['id']] for r in test],
                                [right[r['id']] for r in test], connected_groups(test), seed=13)
    write_json(output / 'interval_nli.json', {'comparison': 'posicao_autor_menos_proposicao', **interval})
    write_json(output / 'predictions.json', predictions)
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'manifest.json', manifest({**protocol, 'encoder': e5.info, 'nli': nli.info},
               [corpus, metadata, Path(__file__)], started))
    print(json.dumps([m for m in metrics if m['target'] is None], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.output)
