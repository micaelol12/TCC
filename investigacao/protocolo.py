"""Núcleo independente de modelos; referências completas em METODOLOGIA.md.

As identificações R1–R7 nas docstrings vinculam cada unidade às fontes e às
adaptações do projeto. Nenhum resultado controlado constitui acurácia documental.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

AXES = {"econ": "economic", "dipl": "diplomatic", "govt": "state", "scty": "society"}
LABELS = ("against", "favor")
STATES = {"sem_evidencia", "favoravel", "contraria", "neutralidade_explicita", "conflito", "incerta"}


def normalize(text):
    """R5: invariância a espaços; preserva palavras, negação e pontuação."""
    return " ".join(text.split())


def digest(value):
    """R4: identificação reproduzível de dados/configuração, SHA-256 canônico."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def write_json(path, value):
    """R4: persistência explícita; rejeita NaN para não disfarçar falhas numéricas."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def notebook_assets(path):
    """R1/R2: reutiliza literalmente âncoras e B3; nunca executa células antigas."""
    notebook = json.loads(Path(path).read_text(encoding="utf-8"))
    wanted = {"TEXTOS_EIXOS_2", "AXES", "PAIRED_ANCHORS", "MINIMAL_PAIRS", "INDEPENDENT_MINIMAL_PAIRS"}
    values, locations = {}, {}
    for i, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        try:
            tree = ast.parse("".join(cell["source"]))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in wanted:
                        values[target.id] = ast.literal_eval(node.value)
                        locations[target.id] = i
    if wanted - values.keys():
        raise ValueError(f"Constantes ausentes: {wanted - values.keys()}")
    return {"values": values, "cells": locations, "sha256": digest(notebook)}


def unit(vectors):
    """R2: normalização euclidiana; direção nula é inválida, não neutralidade."""
    x = np.asarray(vectors, dtype=float)
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    if not np.isfinite(x).all() or np.any(norm < 1e-12):
        raise ValueError("Vetores não finitos ou de norma nula")
    return x / norm


def direction_scores(texts, positive, negative):
    """R1/R2: B0 e margem; B2 é a mediana das projeções pareadas.

    Polos unitários tornam o centro ortogonal à direção. A margem é proporcional
    ao B0, conforme dedução do plano §2.1; não é um método independente.
    """
    x, p, n = unit(texts), unit(positive), unit(negative)
    return x @ unit(p - n).T, x @ (p - n).T


def classification_metrics(truth, prediction, labels=LABELS):
    """R3/R4: macro-F1, BA, MCC e matriz; classes ausentes ficam explícitas."""
    if len(truth) == 0 or len(truth) != len(prediction):
        raise ValueError("Avaliação vazia ou comprimentos diferentes")
    index = {v: i for i, v in enumerate(labels)}
    if (set(truth) | set(prediction)) - index.keys():
        raise ValueError("Rótulos incompatíveis com esta tarefa")
    cm = np.zeros((len(labels), len(labels)), dtype=int)
    for y, p in zip(truth, prediction):
        cm[index[y], index[p]] += 1
    support, predicted = cm.sum(1), cm.sum(0)
    diagonal = np.diag(cm)
    recall = np.divide(diagonal, support, out=np.zeros(len(labels)), where=support > 0)
    f1 = np.divide(2 * diagonal, support + predicted, out=np.zeros(len(labels)), where=(support + predicted) > 0)
    total = cm.sum()
    denom = np.sqrt(float((total**2 - predicted @ predicted) * (total**2 - support @ support)))
    return {"n": int(total), "labels": list(labels), "confusion": cm.tolist(),
            "macro_f1": float(f1.mean()), "balanced_accuracy": float(recall[support > 0].mean()),
            "mcc": float((diagonal.sum() * total - support @ predicted) / denom) if denom else 0.,
            "missing_classes": [labels[i] for i in range(len(labels)) if support[i] == 0]}


def calibrate(scores, truth):
    """R4: otimiza BA apenas no desenvolvimento; empate favorece limiar perto de zero."""
    scores = np.asarray(scores, dtype=float)
    if set(truth) != set(LABELS) or not np.isfinite(scores).all():
        raise ValueError("Calibração exige as duas classes e escores finitos")
    unique = np.unique(scores)
    candidates = np.r_[np.nextafter(unique[0], -np.inf), unique, 0.]
    best = max(candidates, key=lambda t: (
        classification_metrics(truth, np.where(scores > t, "favor", "against").tolist())["balanced_accuracy"],
        -abs(t), -t))
    return float(best)


def pair_diagnostic(scores):
    """R1/R4: B3 + B4 leave-one-pair-out; lados nunca atravessam folds."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 2 or scores.shape[1] != 2 or len(scores) < 2:
        raise ValueError("Esperados pelo menos dois pares (+,-)")
    y = list(LABELS[::-1]) * len(scores)
    out, thresholds = [], []
    for i, row in enumerate(scores):
        train = np.delete(scores, i, axis=0).ravel()
        t = calibrate(train, list(LABELS[::-1]) * (len(scores) - 1))
        out.extend(np.where(row > t, "favor", "against").tolist())
        thresholds.append(t)
    return {"ordering_accuracy": float(np.mean(scores[:, 0] > scores[:, 1])),
            "ties": int(np.sum(scores[:, 0] == scores[:, 1])),
            "mean_separation": float(np.mean(scores[:, 0] - scores[:, 1])),
            "raw": classification_metrics(y, np.where(scores.ravel() > 0, "favor", "against").tolist()),
            "leave_one_pair_out": classification_metrics(y, out), "thresholds": thresholds,
            "transfer_threshold": calibrate(scores.ravel(), y)}


def validate_corpus(rows, metadata):
    """R3/R4: contrato de posição textual e auditoria de vazamento transitivo.

    Um autor, duplicata normalizada ou família deve pertencer a uma só partição.
    Ausência de autoria exige declaração explícita e limita a generalização.
    """
    for field in ("name", "version", "source", "license", "label_definition", "split_policy"):
        if not metadata.get(field):
            raise ValueError(f"Metadado obrigatório: {field}")
    if metadata.get("annotation_unit") != "text_target":
        raise ValueError("Exigidos rótulos texto-alvo; ideologia do autor não é stance")
    if not rows:
        raise ValueError("Corpus vazio")
    seen, groups = set(), defaultdict(set)
    for row in rows:
        for field in ("id", "text", "target", "label", "split", "label_source"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"Campo obrigatório inválido: {field}")
        if row["id"] in seen:
            raise ValueError("IDs duplicados")
        seen.add(row["id"])
        if row["label"] not in LABELS or row["split"] not in {"train", "dev", "test"}:
            raise ValueError("Rótulo/partição inválido; não converter neutral em against")
        if row["label_source"] != "corpus_publico":
            raise ValueError("Avaliação externa exige corpus_publico")
        groups[("text", normalize(row["text"]).casefold())].add(row["split"])
        for field in ("author_id", "family_id"):
            if row.get(field):
                groups[(field, str(row[field]))].add(row["split"])
        if not row.get("author_id") and not metadata.get("author_ids_unavailable"):
            raise ValueError("Autoria ausente sem limitação declarada")
    if any(len(v) > 1 for v in groups.values()):
        raise ValueError("Vazamento: autor, duplicata ou família cruza partições")
    for split in ("train", "dev", "test"):
        if {r["label"] for r in rows if r["split"] == split} != set(LABELS):
            raise ValueError(f"Partição {split} exige ambas as classes")
    return {"n": len(rows), "sha256": digest(rows), "authors_unavailable": bool(metadata.get("author_ids_unavailable")),
            "counts": {s: sum(r["split"] == s for r in rows) for s in ("train", "dev", "test")}}


def contrastive_pairs(rows, seed=42, per_example=2):
    """R6: SetFit adaptado: pares só de treino e mesmo alvo; opostos são negativos.

    Evita negativos entre temas distintos e o autopar trivial. Não reproduz a
    loss SimCSE; usa a loss cosseno de pares do SetFit, explicitada no treinador.
    """
    if any(r["split"] != "train" for r in rows):
        raise ValueError("Pares contrastivos só podem usar treino")
    rng = np.random.default_rng(seed)
    buckets = defaultdict(list)
    for i, r in enumerate(rows):
        buckets[(r["target"], r["label"])].append(i)
    pairs = set()
    for i, row in enumerate(rows):
        for label in LABELS:
            candidates = [j for j in buckets[(row["target"], label)]
                          if normalize(rows[j]["text"]) != normalize(row["text"])]
            for j in rng.choice(candidates, size=min(per_example, len(candidates)), replace=False):
                pairs.add((min(i, int(j)), max(i, int(j)), int(label == row["label"])))
    if not pairs or {p[2] for p in pairs} != {0, 1}:
        raise ValueError("Treino não contém pares positivos e negativos no mesmo alvo")
    return sorted(pairs)


def segments(text, window=100, overlap=20):
    """R5/§6: janela de palavras reproduzível com offsets exatos e deduplicação.

    Política do projeto, não uma segmentação validada na literatura. Normaliza
    somente a entrada do modelo; texto e offsets referem-se sempre ao original.
    """
    if not 0 <= overlap < window:
        raise ValueError("Exigido 0 <= overlap < window")
    words = list(re.finditer(r"\S+", text))
    found, out = {}, []
    for i in range(0, len(words), window - overlap):
        start, end = words[i].start(), words[min(i + window, len(words)) - 1].end()
        raw = text[start:end]
        key = normalize(raw)
        if key in found:
            out[found[key]]["occurrences"].append([start, end])
        else:
            found[key] = len(out)
            out.append({"id": digest(key), "text": raw, "start": start, "end": end, "occurrences": [[start, end]]})
        if i + window >= len(words):
            break
    return out


def evidence_state(evidence, threshold=.7, margin=.2):
    """R3/R7: E/C/N não são intensidade/centro político; conflito fica separado.

    Limiares são política exploratória, não garantia calibrada. Deduplicação por
    conteúdo antes de agregar; recusa inferir neutralidade explícita do NLI.
    """
    if not 0 <= threshold <= 1 or not 0 <= margin <= 1:
        raise ValueError("Limiar/margem fora de [0,1]")
    unique = {normalize(e["text"]): e for e in evidence}
    if not unique:
        return "sem_evidencia"
    signs = set()
    for e in unique.values():
        p = np.asarray([e["entailment"], e["contradiction"], e["neutral"]])
        if not np.isfinite(p).all() or np.any(p < 0) or not np.isclose(p.sum(), 1):
            raise ValueError(f"Probabilidades NLI inválidas: {p.tolist()}")
        if max(p[:2]) >= threshold and abs(p[0] - p[1]) >= margin:
            signs.add("favoravel" if p[0] > p[1] else "contraria")
    return "conflito" if len(signs) > 1 else next(iter(signs), "incerta")


def quiz_summary(questions, responses):
    """R2 + plano §7: cobertura e intervalo algébrico, nunca IC estatístico.

    responses mapeia ID para m em [-1,1] ou None. Direção binária não autoriza
    passar +/-1 como intensidade; o chamador precisa justificar a escala.
    """
    ids = [str(q["id"]) for q in questions]
    if len(ids) != len(set(ids)) or set(responses) - set(ids):
        raise ValueError("IDs repetidos ou respostas sem pergunta")
    out = {}
    for axis in AXES:
        k, missing, total = 0., 0., 0.
        for q in questions:
            w = float(q["effect"][axis])
            m = responses.get(str(q["id"]))
            if not np.isfinite(w) or (m is not None and (not np.isfinite(m) or m not in {-1, -.5, 0, .5, 1})):
                raise ValueError("Peso/resposta inválidos")
            total += abs(w)
            if m is None:
                missing += abs(w)
            else:
                k += w * m
        observed = total - missing
        out[axis] = {"coverage": observed / total if total else None,
                     "zero_imputed_score": 50 + 50 * k / total if total else None,
                     "conditional_score": 50 + 50 * k / observed if observed else None,
                     "identification_interval": [50 + 50 * (k - missing) / total, 50 + 50 * (k + missing) / total] if total else None}
    return out


def inserted_context(source, distractors, at=1):
    """R5: passagem rotulada inserida com offsets; distratores não têm gabarito."""
    if not 0 <= at <= len(distractors):
        raise ValueError("Posição de inserção inválida")
    pieces = [r["text"] for r in distractors]
    pieces.insert(at, source["text"])
    start = sum(len(p) + 2 for p in pieces[:at])
    return {"text": "\n\n".join(pieces), "start": start, "end": start + len(source["text"]),
            "source_id": source["id"], "target": source["target"], "label": source["label"],
            "family_id": source.get("family_id", source["id"]), "split": source["split"],
            "label_source": "construcao_controlada", "template": "passagem_inserida_v1",
            "generator": "deterministico", "distractor_ids": [r["id"] for r in distractors]}


def retrieval_metrics(chunks, scores, start, end, ks=(1, 3, 5)):
    """R5: rank/recall apenas da passagem inserida, exigindo contenção completa."""
    order = sorted(range(len(chunks)), key=lambda i: (-scores[i], chunks[i]["id"]))
    hits = [rank + 1 for rank, i in enumerate(order)
            if any(a <= start and b >= end for a, b in chunks[i]["occurrences"])]
    rank = min(hits) if hits else None
    return {"rank": rank, "reciprocal_rank": 1 / rank if rank else 0.,
            "recall_inserted": {str(k): int(rank is not None and rank <= k) for k in ks},
            "contained_by_segmentation": rank is not None}


def connected_groups(rows):
    """R4/R8: componentes transitivos por autor, duplicata e família para reamostragem."""
    parent = list(range(len(rows)))

    def find(i):
        """R4: representante do componente de dependência; compressão de caminho."""
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen = {}
    for i, row in enumerate(rows):
        keys = [("text", normalize(row["text"]).casefold())]
        keys += [(f, str(row[f])) for f in ("author_id", "family_id") if row.get(f)]
        for key in keys:
            if key in seen:
                parent[find(i)] = find(seen[key])
            seen[key] = i
    return [str(find(i)) for i in range(len(rows))]


def grouped_bootstrap(truth, left, right, groups, seed=42, repeats=1000):
    """R8: IC percentil da diferença macro-F1 por grupos, adaptação do protocolo.

    Não é teste de independência dos grupos; poucos grupos geram intervalos
    frágeis. O mesmo sorteio é usado nas duas configurações comparadas.
    """
    if not len(truth) == len(left) == len(right) == len(groups) or not truth or repeats < 1:
        raise ValueError("Dados de comparação incompatíveis")
    ids = sorted(set(groups))
    if len(ids) < 2:
        raise ValueError("São necessários ao menos dois grupos")
    indices = {g: [i for i, x in enumerate(groups) if x == g] for g in ids}
    rng = np.random.default_rng(seed)
    delta = []
    for _ in range(repeats):
        selected = [i for g in rng.choice(ids, len(ids), replace=True) for i in indices[g]]
        y = [truth[i] for i in selected]
        delta.append(classification_metrics(y, [left[i] for i in selected])["macro_f1"] -
                     classification_metrics(y, [right[i] for i in selected])["macro_f1"])
    return {"delta_macro_f1": classification_metrics(truth, left)["macro_f1"] - classification_metrics(truth, right)["macro_f1"],
            "percentile_interval_95": np.quantile(delta, [.025, .975]).tolist(),
            "groups": len(ids), "repeats": repeats, "seed": seed, "method": "paired_cluster_percentile_bootstrap"}
