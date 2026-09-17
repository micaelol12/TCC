"""Orquestração dos três experimentos; fontes R1–R7 em METODOLOGIA.md."""
from __future__ import annotations

import importlib.metadata
import json
import platform
import re
import time
from pathlib import Path

import numpy as np

from .modelos import E5, NLI, conditioned, finetune, fit_head, zero_shot
from .protocolo import (AXES, STATES, classification_metrics, connected_groups, grouped_bootstrap, digest, direction_scores, evidence_state,
                        inserted_context, normalize, notebook_assets, pair_diagnostic,
                        quiz_summary, retrieval_metrics, segments, validate_corpus, write_json)


def manifest(config, inputs, started):
    """R4: versões, hashes, configuração, tempo e RSS; nenhum segredo/API no log."""
    versions = {}
    for package in ("numpy", "torch", "transformers", "sentence-transformers", "scikit-learn"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    try:
        import psutil
        memory = psutil.Process().memory_info().rss
    except ImportError:
        memory = None
    gpu = None
    import sys
    torch = sys.modules.get("torch")
    if torch is not None and torch.cuda.is_initialized():
        torch.cuda.synchronize()
        gpu = {"name": torch.cuda.get_device_name(), "cuda_build": torch.version.cuda,
               "capability": list(torch.cuda.get_device_capability()),
               "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
               "peak_reserved_bytes": torch.cuda.max_memory_reserved()}
    return {"config": config, "input_hashes": {str(p): digest(Path(p).read_text(encoding="utf-8")) for p in inputs},
            "python": platform.python_version(), "versions": versions, "elapsed_seconds": time.perf_counter() - started,
            "rss_bytes_at_end": memory, "rss_is_peak": False, "gpu": gpu,
            "limitations": ["Diagnósticos conhecidos não são teste cego", "Acurácia documental não estimada"]}


def diagnostic(root, output, encoder):
    """R1/R2/R4: B0/B2/margem, B3a/B3b, B4 agrupado e transferência B5."""
    started = time.perf_counter()
    root, output = Path(root), Path(output)
    assets = notebook_assets(root / "TCC.ipynb")
    a = assets["values"]
    questions = json.loads((root / "content/questions.json").read_text(encoding="utf-8"))
    rows, metrics, pair_results = [], [], []
    for effect, axis in AXES.items():
        pos, neg = a["AXES"][axis]
        p, n = encoder.encode([a["TEXTOS_EIXOS_2"][axis][pos], a["TEXTOS_EIXOS_2"][axis][neg]])
        anchor_pairs = a["PAIRED_ANCHORS"][axis]
        pe = encoder.encode([r[0] for r in anchor_pairs])
        ne = encoder.encode([r[1] for r in anchor_pairs])
        axis_q = [q for q in questions if q["effect"][effect] != 0]
        anchors = {normalize(t) for t in [a["TEXTOS_EIXOS_2"][axis][pos], a["TEXTOS_EIXOS_2"][axis][neg]]}
        anchors.update(normalize(t) for pair in anchor_pairs for t in pair)
        if any(normalize(q["question"]) in anchors for q in axis_q):
            raise ValueError("Uma pergunta de avaliação está sendo usada como sua âncora")
        qx = encoder.encode([q["question"] for q in axis_q])
        b0, margin = direction_scores(qx, p, n)
        b2 = np.median(direction_scores(qx, pe, ne)[0], axis=1)
        scores = {"B0": b0, "margem_equivalente_B0": margin, "B2": b2}
        transfer = {}
        for source in ("MINIMAL_PAIRS", "INDEPENDENT_MINIMAL_PAIRS"):
            pairs = a[source][axis]
            x = encoder.encode([t for pair in pairs for t in pair])
            raw, m = direction_scores(x, p, n)
            paired = np.median(direction_scores(x, pe, ne)[0], axis=1)
            for method, s in (("B0", raw), ("margem_equivalente_B0", m), ("B2", paired)):
                result = pair_diagnostic(s.reshape(-1, 2))
                pair_results.append({"axis": axis, "method": method, "dataset": source,
                                     "label_source": "construcao_controlada", "known_development": True,
                                     "scores": s.reshape(-1, 2).tolist(), **result})
                if source == "INDEPENDENT_MINIMAL_PAIRS":
                    transfer[method] = result["transfer_threshold"]
        y = ["favor" if q["effect"][effect] > 0 else "against" for q in axis_q]
        for method, s in scores.items():
            for calibration, threshold in (("zero", 0.), ("B3b_transfer_B5", transfer[method])):
                pred = np.where(s > threshold, "favor", "against").tolist()
                metrics.append({"axis": axis, "method": method, "calibration": calibration,
                                "label_source": "instrumento", "known_development": True,
                                **classification_metrics(y, pred)})
                rows.extend({"question_id": q["id"], "axis": axis, "method": method,
                             "label_source": "instrumento", "family_id": str(q["id"]), "truth": truth,
                             "score": float(score), "prediction": prediction, "threshold": threshold,
                             "calibration": calibration}
                            for q, truth, score, prediction in zip(axis_q, y, s, pred))
    write_json(output / "diagnostico_metricas.json", metrics)
    write_json(output / "diagnostico_previsoes.json", rows)
    write_json(output / "pares_b3_b4.json", pair_results)
    write_json(output / "ancoras_origem.json", assets)
    write_json(output / "manifest.json", manifest({"experiment": "diagnostico", "encoder": encoder.info,
                                                   "seed": 42, "prefix": "query", "sources": ["instrumento", "construcao_controlada"]},
                                                  [root / "TCC.ipynb", root / "content/questions.json"], started))
    return metrics


def external(corpus, metadata, output, seeds=(13, 42, 77), device="cpu", local_only=True, include_nli=True,
             baselines_only=False, batch_size=None, low_vram=False):
    """R3/R4/R6: três configurações, seleção no dev, teste separado por semente.

    O contrato binário exige filtragem documentada anterior; não aceita converter
    rótulos de autor, intensidade ou 'other' em direção sem justificativa.
    R4/R6: baselines_only omite ajuste do encoder e registra comparação parcial;
    lote/offload afetam somente inferência, regressão logística roda na CPU.
    """
    import joblib
    started = time.perf_counter()
    output = Path(output)
    rows = [json.loads(line) for line in Path(corpus).read_text(encoding="utf-8").splitlines() if line.strip()]
    meta = json.loads(Path(metadata).read_text(encoding="utf-8"))
    audit = validate_corpus(rows, meta)
    write_json(output / "corpus_audit.json", {"metadata": meta, **audit})
    write_json(output / "partitions.json", [{k: r.get(k) for k in ("id", "split", "author_id", "family_id")} for r in rows])
    train, dev, test = [[r for r in rows if r["split"] == s] for s in ("train", "dev", "test")]
    predictions, metrics, infos = [], [], []
    methods = ("congelado",) if baselines_only else ("congelado", "contrastivo")
    base = E5(device=device, local_only=local_only, batch_size=batch_size, low_vram=low_vram)
    scores = zero_shot(base, test)
    pred = np.where(scores > 0, "favor", "against").tolist()
    metrics.append({"method": "sem_ajuste", "split": "test", **classification_metrics([r["label"] for r in test], pred)})
    predictions.extend({"id": r["id"], "target": r["target"], "truth": r["label"], "prediction": p,
                        "method": "sem_ajuste", "score": float(s), "label_source": "corpus_publico"}
                       for r, p, s in zip(test, pred, scores))
    dev_base = np.where(zero_shot(base, dev) > 0, "favor", "against").tolist()
    selections = [{"method": "sem_ajuste", "dev_macro_f1": classification_metrics([r["label"] for r in dev], dev_base)["macro_f1"]}]
    for seed in seeds:
        for method in methods:
            encoder = base if method == "congelado" else E5(device=device, local_only=local_only)
            if method == "contrastivo":
                training = finetune(encoder, train, seed=seed)
                write_json(output / f"pares_treino_{seed}.json", training)
            head, selection = fit_head(encoder, train, dev, seed)
            folder = output / f"{method}_{seed}"
            folder.mkdir(parents=True, exist_ok=True)
            joblib.dump(head, folder / "head.joblib")
            if method == "contrastivo":
                encoder.model.save(str(folder / "encoder"))
            write_json(folder / "selection.json", selection)
            write_json(folder / "encoder_config.json", encoder.info)
            selections.append({"method": method, "seed": seed, "dev_macro_f1": selection["dev"]["macro_f1"]})
            p = head.predict(encoder.encode([conditioned(r) for r in test])).tolist()
            metrics.append({"method": method, "seed": seed, "split": "test", **classification_metrics([r["label"] for r in test], p)})
            predictions.extend({"id": r["id"], "target": r["target"], "truth": r["label"], "prediction": v,
                                "method": method, "seed": seed, "label_source": "corpus_publico"} for r, v in zip(test, p))
            infos.append({"method": method, "seed": seed, **encoder.info})
            if method == "contrastivo":
                del encoder
    # Ranking das alternativas pela média no desenvolvimento; teste nunca escolhe vencedor.
    means = {m: float(np.mean([r["dev_macro_f1"] for r in selections if r["method"] == m]))
             for m in ("sem_ajuste", *methods)}
    write_json(output / "frozen_selection.json", {"chosen_method": max(means, key=means.get),
                                                  "dev_means": means, "runs": selections,
                                                  "comparison_complete": not baselines_only,
                                                  "seed_for_application": seeds[0], "no_intensity_scale": True})
    if include_nli:
        nli = NLI(device=device, local_only=local_only, batch_size=batch_size, low_vram=low_vram)
        probabilities = nli.predict([(r["text"], f"O autor é favorável a {r['target']}.") for r in test])
        p = ["favor" if r["entailment"] > r["contradiction"] else "against" for r in probabilities]
        metrics.append({"method": "nli_relacional", "split": "test", **classification_metrics([r["label"] for r in test], p)})
        predictions.extend({"id": r["id"], "target": r["target"], "truth": r["label"], "prediction": v,
                            "method": "nli_relacional", "label_source": "corpus_publico", **prob}
                           for r, v, prob in zip(test, p, probabilities))
        infos.append(nli.info)
    for method in sorted({r["method"] for r in predictions}):
        selected = [r for r in predictions if r["method"] == method]
        for seed in sorted({r.get("seed", -1) for r in selected}):
            for target in sorted({r["target"] for r in selected}):
                subset = [r for r in selected if r["target"] == target and r.get("seed", -1) == seed]
                metrics.append({"method": method, "seed": seed, "target": target, "split": "test",
                                **classification_metrics([r["truth"] for r in subset], [r["prediction"] for r in subset])})
    write_json(output / "metricas.json", metrics)
    write_json(output / "previsoes.json", predictions)
    intervals = []
    groups = connected_groups(test)
    if len(set(groups)) >= 2 and not baselines_only:
        for seed in seeds:
            left = {r["id"]: r["prediction"] for r in predictions if r["method"] == "contrastivo" and r.get("seed") == seed}
            right = {r["id"]: r["prediction"] for r in predictions if r["method"] == "congelado" and r.get("seed") == seed}
            intervals.append({"seed": seed, "comparison": "contrastivo_menos_congelado",
                              **grouped_bootstrap([r["label"] for r in test], [left[r["id"]] for r in test],
                                                  [right[r["id"]] for r in test], groups, seed)})
    write_json(output / "intervalos_agrupados.json", intervals)
    if baselines_only:
        left = {r['id']: r['prediction'] for r in predictions if r['method'] == 'congelado' and r.get('seed') == seeds[0]}
        right = {r['id']: r['prediction'] for r in predictions if r['method'] == 'sem_ajuste'}
        write_json(output / 'intervalo_baselines.json', {
            'comparison': 'congelado_menos_sem_ajuste', 'seed': seeds[0],
            **grouped_bootstrap([r['label'] for r in test], [left[r['id']] for r in test],
                                [right[r['id']] for r in test], groups, seeds[0])})
    write_json(output / "manifest.json", manifest({"experiment": "externo", "models": infos, "seeds": list(seeds),
                                                   "baselines_only": baselines_only,
                                                   "pending": ["contrastivo"] if baselines_only else []}, [corpus, metadata], started))
    return metrics


def document(text, questions, encoder, nli, window=100, overlap=20, top_k=3, threshold=.7, margin=.2):
    """R3/R5/R7: recuperação por pergunta e posição NLI; guarda offsets/escores.

    Top-k é recuperação relativa; não prova relevância absoluta. Nenhum NLI
    neutral recebe resposta zero. Direção não é intensidade: quiz fica ausente.
    """
    if top_k < 1:
        raise ValueError("top_k deve ser positivo")
    chunks = segments(text, window, overlap)
    qx = encoder.encode([q["question"] for q in questions])
    cx = encoder.encode([c["text"] for c in chunks], role="passage")
    similarities = qx @ cx.T
    items = []
    for q, scores in zip(questions, similarities):
        ranking = sorted(range(len(chunks)), key=lambda i: (-scores[i], chunks[i]["id"]))[:top_k]
        evidence = [{**chunks[i], "similarity": float(scores[i]), "rank": rank + 1}
                    for rank, i in enumerate(ranking)]
        probs = nli.predict([(e["text"], q["question"]) for e in evidence])
        evidence = [{**e, **p} for e, p in zip(evidence, probs)]
        items.append({"question_id": q["id"], "question": q["question"], "label_source": "sem_rotulo",
                      "state": evidence_state(evidence, threshold, margin), "response": None, "evidence": evidence})
    coverage = {}
    for axis in AXES:
        total = sum(abs(q["effect"][axis]) for q in questions)
        accepted = sum(abs(q["effect"][axis]) for q, item in zip(questions, items) if item["state"] in {"favoravel", "contraria"})
        coverage[axis] = accepted / total if total else None
    return {"items": items, "direction_coverage": coverage, "quiz": quiz_summary(questions, {}),
            "intensity_status": "adiada: direção não determina intensidade",
            "config": {"window": window, "overlap": overlap, "top_k": top_k, "threshold": threshold, "margin": margin},
            "document_sha256": digest(text), "chunks": len(chunks)}


def robustness(text, questions, encoder, nli, **kwargs):
    """R5: espaços, permutação da agregação, duplicação e duas segmentações.

    Permuta evidências independentes já recuperadas; não assume que reordenar
    um documento com anáforas preserva seu sentido.
    """
    base = document(text, questions, encoder, nli, **kwargs)
    spaced = document(re.sub(r"\s+", "  \n", text), questions, encoder, nli, **kwargs)
    alternate = document(text, questions, encoder, nli, **{**kwargs, "window": 160, "overlap": 32})
    comparisons = []
    for original, formatted, other in zip(base["items"], spaced["items"], alternate["items"]):
        evidence = original["evidence"]
        comparisons.append({"question_id": original["question_id"],
                            "spacing_invariant": original["state"] == formatted["state"],
                            "duplicate_invariant": original["state"] == evidence_state(evidence + evidence, kwargs.get("threshold", .7), kwargs.get("margin", .2)),
                            "aggregation_order_invariant": original["state"] == evidence_state(evidence[::-1], kwargs.get("threshold", .7), kwargs.get("margin", .2)),
                            "segmentation_same_state": original["state"] == other["state"]})
    return {"base": base, "alternate": alternate, "checks": comparisons,
            "interpretation": "estabilidade não comprova acerto"}


def controlled(rows, encoder, window=100, overlap=20):
    """R5: recupera passagens de origem conhecida em contextos artificiais."""
    out = []
    for i, source in enumerate(rows):
        distractors = [r for r in rows if r["id"] != source["id"] and r["target"] != source["target"] and r["split"] == source["split"]][:3]
        if not distractors:
            continue
        context = inserted_context(source, distractors, at=i % (len(distractors) + 1))
        chunks = segments(context["text"], window, overlap)
        x = encoder.encode([r["text"] for r in chunks], role="passage")
        q = encoder.encode([source["target"]])[0]
        out.append({**context, "retrieval": retrieval_metrics(chunks, x @ q, context["start"], context["end"])})
    return out


def sabia_agreement(items, reference, config):
    """R3/§6: concordância com Sabiá fixo, nunca gabarito; join por ID, não ordem."""
    for key in ("model", "prompt_sha256", "temperature"):
        if key not in config:
            raise ValueError(f"Comparador sem configuração fixa: {key}")
    ids = [str(r["question_id"]) for r in reference]
    if len(set(ids)) != len(ids):
        raise ValueError("IDs repetidos no comparador")
    if any(r["state"] not in STATES for r in [*items, *reference]):
        raise ValueError("Estado inválido no comparador")
    ref = {str(r["question_id"]): r["state"] for r in reference}
    compared = [{"question_id": r["question_id"], "system": r["state"], "sabia": ref[str(r["question_id"])]}
                for r in items if str(r["question_id"]) in ref]
    return {"n_compared": len(compared), "n_system": len(items), "config": config,
            "agreement": float(np.mean([r["system"] == r["sabia"] for r in compared])) if compared else None,
            "disagreements": [r for r in compared if r["system"] != r["sabia"]],
            "interpretation": "concordância, não acurácia"}


def nli_ablation(texts, questions, assets, nli):
    """R7/R1: mesmo mDeBERTa/textos; proposição específica versus âncoras amplas.

    Escores têm estimandos diferentes: não se calcula acurácia entre os dois.
    Neutral é mantido nos resultados; diferenças pequenas não viram confiança.
    """
    out = []
    for q in questions:
        for text_id, text in texts:
            specific = nli.predict([(text, q["question"])])[0]
            axes = {}
            for effect, axis in AXES.items():
                if not q["effect"][effect]:
                    continue
                anchors = assets["values"]["PAIRED_ANCHORS"][axis]
                p = nli.predict([(text, t) for pair in anchors for t in pair])
                differences = [p[i]["entailment"] - p[i + 1]["entailment"] for i in range(0, len(p), 2)]
                with_contradiction = [(p[i]["entailment"] - p[i]["contradiction"]) -
                                      (p[i + 1]["entailment"] - p[i + 1]["contradiction"]) for i in range(0, len(p), 2)]
                axes[axis] = {"median_entailment_difference": float(np.median(differences)),
                              "median_with_contradiction": float(np.median(with_contradiction)), "probabilities": p}
            out.append({"text_id": text_id, "question_id": q["id"], "specific": specific, "broad_anchors": axes,
                        "label_source": "sem_rotulo", "interpretation": "estimandos distintos; comparação de comportamento"})
    return out


def apply_frozen(items, run, device="cpu", threshold=.7, batch_size=None, low_vram=False):
    """R3/R6: transfere configuração escolhida só no dev para evidências já fixadas.

    A cabeça usa alvo=pergunta e o mesmo template do corpus público. Confiança e
    limiar não têm garantia de erro documental; intensidade permanece ausente.
    """
    import joblib
    run = Path(run)
    choice = json.loads((run / "frozen_selection.json").read_text(encoding="utf-8"))
    method, seed = choice["chosen_method"], choice["seed_for_application"]
    if method == "sem_ajuste":
        data = json.loads((run / f"congelado_{seed}" / "encoder_config.json").read_text(encoding="utf-8"))
        encoder = E5(name=data["name"], revision=data["revision"], device=device,
                     batch_size=batch_size, low_vram=low_vram)
        head = None
    else:
        folder = run / f"{method}_{seed}"
        data = json.loads((folder / "encoder_config.json").read_text(encoding="utf-8"))
        encoder = E5(name=str(folder / "encoder") if method == "contrastivo" else data["name"],
                     revision=None if method == "contrastivo" else data["revision"], device=device,
                     batch_size=batch_size, low_vram=low_vram)
        head = joblib.load(folder / "head.joblib")
    out = []
    for item in items:
        rows = [{"text": e["text"], "target": item["question"]} for e in item["evidence"]]
        signals = []
        if rows and head is None:
            signals = [{"state": "favoravel" if s > 0 else "contraria" if s < 0 else "incerta", "margin": float(s)} for s in zero_shot(encoder, rows)]
        elif rows:
            probabilities = head.predict_proba(encoder.encode([conditioned(r) for r in rows]))
            for p in probabilities:
                label = head.classes_[int(np.argmax(p))]
                signals.append({"state": ("favoravel" if label == "favor" else "contraria") if max(p) >= threshold else "incerta",
                                "probabilities": dict(zip(head.classes_, map(float, p)))})
        signs = {r["state"] for r in signals} & {"favoravel", "contraria"}
        state = "sem_evidencia" if not rows else "conflito" if len(signs) > 1 else next(iter(signs), "incerta")
        out.append({"question_id": item["question_id"], "state": state, "method": method,
                    "response": None, "label_source": "sem_rotulo",
                    "evidence": [{**e, "external_stance": s} for e, s in zip(item["evidence"], signals)]})
    return {"items": out, "selection": choice, "encoder": encoder.info, "transfer_exploratory": True}
