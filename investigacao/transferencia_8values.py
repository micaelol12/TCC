"""R3/R5/R7: diagnóstico comportamental de transferência BRmoral → 8values.

Ribeiro et al. (2020), CheckList, §2, https://aclanthology.org/2020.acl-main.442/:
expectativas por construção, não anotação humana. Yin et al. (2019), §3,
https://aclanthology.org/D19-1404/: hipótese específica da pergunta.
Fontes e adaptações completas em METODOLOGIA.md. Não estima acurácia documental.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from .experimentos import manifest
from .modelos import E5, NLI, conditioned
from .protocolo import classification_metrics, evidence_state, write_json


def cases(questions):
    """R5: duas formas explícitas de apoio/rejeição, preservando a proposição.

    Não insere 'não' na pergunta, não interpreta effect como rótulo de stance.
    Question_id agrupa todas as variações; não se divide nem treina neste conjunto.
    """
    result = []
    templates = {
        'concordancia': {'favor': 'Concordo com a seguinte afirmação: «{q}»',
                        'against': 'Discordo da seguinte afirmação: «{q}»'},
        'defesa': {'favor': 'Defendo a posição expressa nesta proposição: «{q}»',
                   'against': 'Rejeito a posição expressa nesta proposição: «{q}»'},
    }
    if len({q['id'] for q in questions}) != len(questions):
        raise ValueError('IDs de pergunta duplicados')
    for q in questions:
        for template, labels in templates.items():
            for label, phrase in labels.items():
                result.append({'id': f"{q['id']}:{template}:{label}", 'family_id': str(q['id']),
                               'question_id': q['id'], 'target': q['question'],
                               'text': phrase.format(q=q['question']), 'label': label,
                               'template': template, 'effect': q['effect'],
                               'label_source': 'construcao_controlada', 'split': 'diagnostic'})
    return result


def summarize(rows):
    """R4/R5: métricas condicionais ao template e ordenação pareada, sem retunar."""
    output = []
    for method in sorted({r['method'] for r in rows}):
        for template in ['all', *sorted({r['template'] for r in rows})]:
            subset = [r for r in rows if r['method'] == method and (template == 'all' or r['template'] == template)]
            pairs = {}
            for r in subset:
                pairs.setdefault((r['family_id'], r['template']), {})[r['label']] = r
            accepted = [r for r in subset if r['state'] in {'favoravel', 'contraria'}]
            correct = sum(r['state'] == ('favoravel' if r['label'] == 'favor' else 'contraria') for r in subset)
            output.append({'method': method, 'template': template,
                           **classification_metrics([r['label'] for r in subset], [r['prediction'] for r in subset]),
                           'direction_coverage': len(accepted) / len(subset),
                           'expected_state_accuracy': correct / len(subset),
                           'accuracy_when_accepted': correct / len(accepted) if accepted else None,
                           'pair_ordering': sum(p['favor']['score'] > p['against']['score'] for p in pairs.values()) / len(pairs),
                           'both_sides_correct': sum(p['favor']['prediction'] == 'favor' and p['against']['prediction'] == 'against' for p in pairs.values()) / len(pairs)})
    return output


def format_cases(questions):
    """R5/CheckList §2: fatorial aspas × posição do marcador, rótulo fixo.

    Sem aspas ainda repete literalmente a proposição: não testa paráfrase ou
    generalização natural. Altera apenas dois fatores de superfície, sem treino.
    """
    if len({q['id'] for q in questions}) != len(questions):
        raise ValueError('IDs de pergunta duplicados')
    rows = []
    for q in questions:
        for quoted in (True, False):
            proposition = f"«{q['question']}»" if quoted else q['question']
            for position in ('antes', 'depois'):
                template = f"{'aspas' if quoted else 'sem_aspas'}_{position}"
                for label, verb in [('favor', 'Concordo'), ('against', 'Discordo')]:
                    prefix = 'Concordo com a seguinte afirmação' if label == 'favor' else 'Discordo da seguinte afirmação'
                    suffix = 'Concordo com essa afirmação.' if label == 'favor' else 'Discordo dessa afirmação.'
                    text = (f'{prefix}: {proposition}' if position == 'antes'
                            else f'{proposition} {suffix}')
                    rows.append({'id': f"{q['id']}:{template}:{label}", 'family_id': str(q['id']),
                                 'question_id': q['id'], 'target': q['question'], 'text': text,
                                 'label': label, 'template': template, 'effect': q['effect'],
                                 'label_source': 'construcao_controlada', 'split': 'diagnostic'})
    return rows


def run(root, selected_run, output, format_ablation=False):
    """R3/R4/R5/R7: modelos congelados, CUDA, parâmetros fixos antes dos resultados."""
    import joblib
    import torch
    if output.exists():
        raise ValueError('Use uma pasta nova')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível; sem fallback silencioso')
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    qpath = root / 'content/questions.json'
    questions = json.loads(qpath.read_text(encoding='utf-8'))
    rows = format_cases(questions) if format_ablation else cases(questions)
    choice = json.loads((selected_run / 'frozen_selection.json').read_text(encoding='utf-8'))
    if choice['chosen_method'] != 'congelado':
        raise ValueError('Diagnóstico exige a cabeça congelada BRmoral')
    folder = selected_run / f"congelado_{choice['seed_for_application']}"
    config = json.loads((folder / 'encoder_config.json').read_text(encoding='utf-8'))
    protocol = {'source': 'construcao_controlada', 'manual_annotations': False,
                'training': False, 'head_threshold': .7, 'nli_threshold': .7, 'nli_margin': .2,
                'hypothesis': 'pergunta literal', 'n': len(rows), 'families': len(questions),
                'selection': choice, 'effect_usage': 'descriptive only; never stance labels',
                'no_intensity_scale': True, 'format_ablation': format_ablation,
                'literal_proposition_repeated': True,
                'head_sha256': hashlib.sha256((folder / 'head.joblib').read_bytes()).hexdigest()}
    write_json(output / 'protocol.json', protocol)
    write_json(output / 'cases.json', rows)
    encoder = E5(name=config['name'], revision=config['revision'], device='cuda', batch_size=1, low_vram=True)
    head = joblib.load(folder / 'head.joblib')
    probabilities = head.predict_proba(encoder.encode([conditioned(r) for r in rows]))
    positive = list(head.classes_).index('favor')
    predictions = []
    for row, p in zip(rows, probabilities):
        label = str(head.classes_[int(np.argmax(p))])
        state = ('favoravel' if label == 'favor' else 'contraria') if max(p) >= .7 else 'incerta'
        predictions.append({**row, 'method': 'brmoral_congelado', 'prediction': label,
                            'state': state, 'score': float(p[positive]),
                            'probabilities': dict(zip(head.classes_, map(float, p)))})
    nli = NLI(device='cuda', batch_size=1, low_vram=True)
    probs = nli.predict([(r['text'], r['target']) for r in rows])
    for row, p in zip(rows, probs):
        predictions.append({**row, 'method': 'nli_pergunta',
                            'prediction': 'favor' if p['entailment'] > p['contradiction'] else 'against',
                            'state': evidence_state([{**p, 'text': row['text']}]),
                            'score': p['entailment'] - p['contradiction'], 'probabilities': p})
    if format_ablation:
        # R7: hipótese sobre posição do autor; variante pré-especificada, não seleção.
        stance_probs = nli.predict([(r['text'], f"O autor concorda com a seguinte afirmação: {r['target']}") for r in rows])
        for row, p in zip(rows, stance_probs):
            predictions.append({**row, 'method': 'nli_posicao_autor',
                                'prediction': 'favor' if p['entailment'] > p['contradiction'] else 'against',
                                'state': evidence_state([{**p, 'text': row['text']}]),
                                'score': p['entailment'] - p['contradiction'], 'probabilities': p})
    metrics = summarize(predictions)
    write_json(output / 'predictions.json', predictions)
    write_json(output / 'metrics.json', metrics)
    write_json(output / 'manifest.json', manifest({**protocol, 'encoder': encoder.info, 'nli': nli.info},
               [qpath, selected_run / 'frozen_selection.json', folder / 'encoder_config.json'], started))
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--selected-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--format-ablation', action='store_true')
    args = parser.parse_args()
    run(args.root, args.selected_run, args.output, args.format_ablation)
