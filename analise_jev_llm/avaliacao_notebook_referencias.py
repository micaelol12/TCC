"""Reavalia offline a rodada salva no notebook; nunca executa suas células de APIs."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook

RUN = ROOT / "runs/benchmark_8values/20261029T175131246256Z"


def main():
    ns = carregar_pipeline_notebook()
    manifest = json.loads((RUN / "manifesto.json").read_text(encoding="utf-8"))
    questions = [ns["Question"].model_validate(q) for q in
                 json.loads((ROOT / "tcc/questions.json").read_text(encoding="utf-8"))]
    by_id = {q.id: q for q in questions}
    questions = [by_id[qid] for qid in manifest["ids_perguntas"]]
    question_hash = hashlib.sha256(json.dumps(
        [q.model_dump() for q in questions], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    assert question_hash == manifest["hash_perguntas"]
    wrappers = [json.loads(line) for line in (RUN / "benchmark.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(wrappers) == len(questions) == 70
    assert all(w["erro"] is None and w["chave"] == f"q{q.id}" for w, q in zip(wrappers, questions))
    records = [w["registro"] for w in wrappers]
    pipe = ns["CascataJevLLM2Polos"](
        jev_client=object(), llm=SimpleNamespace(model=manifest["pipeline"]["modelo_llm"]),
        axis_specs=ns["AXIS_SPECS"], **manifest["pipeline"]["cascata"])
    rubric_hash = hashlib.sha256(json.dumps(
        pipe.rubricas, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    assert rubric_hash == manifest["hash_rubricas"]
    assert all(r["config"] == manifest["config_efetiva"] and r["escala_hash"] == manifest["escala_hash"]
               for r in records)
    details, _ = ns["avaliar_registros"](questions, records)
    paired = details.pivot(index=["id", "eixo"], columns="etapa", values="acerto conjunto")
    changes = {"erro_para_acerto": int((~paired.eixos_jev & paired.eixos).sum()),
               "acerto_para_erro": int((paired.eixos_jev & ~paired.eixos).sum())}
    results = []
    for stage in ("eixos_jev", "eixos"):
        for axis in ("all", "economic", "diplomatic", "state", "society"):
            d = details[details.etapa == stage]
            if axis != "all":
                d = d[d.eixo == axis]
            relevant = d[d["relevância esperada"]]
            irrelevant = d[~d["relevância esperada"]]
            results.append({"etapa": stage, "eixo": axis, "pares": len(d),
                "acertos_conjuntos": int(d["acerto conjunto"].sum()),
                "acertos_direcao": int(relevant["direção correta"].sum()),
                "relevantes_referencia": len(relevant),
                "relevantes_detectados": int((relevant["relevância prevista"] == True).sum()),
                "irrelevantes_corretos": int((irrelevant["relevância prevista"] == False).sum()),
                "falsos_negativos_relevancia": int((relevant["relevância prevista"] == False).sum()),
                "abstencoes_relevancia": int(relevant["relevância prevista"].isna().sum()),
                "taxa_acerto_conjunta": float(d["acerto conjunto"].mean())})
    # Paired question bootstrap keeps the four axes of each question together.
    deltas = (paired.eixos.astype(int) - paired.eixos_jev.astype(int)).groupby(level="id").sum().to_numpy()
    rng = np.random.default_rng(42)
    draws = rng.choice(deltas, size=(10000, len(deltas)), replace=True).sum(axis=1) / len(paired)
    route_reasons = Counter(reason for r in records for reasons in r["motivos_fallback"].values() for reason in reasons)
    saved_config = manifest["pipeline"]["cascata"]
    false_negative_without_route = []
    for q, r in zip(questions, records):
        for effect, axis in ns["EFFECT_TO_AXIS"].items():
            if getattr(q.effect, effect) and r["eixos_jev"][axis]["relevante"] is False and axis not in r["eixos_encaminhados"]:
                false_negative_without_route.append({"question_id": q.id, "axis": axis})
    notebook = json.loads((ROOT / "Pipeline - Passo a Passo.ipynb").read_text(encoding="utf-8"))
    config_node = next(node for node in ast.parse("".join(notebook["cells"][2]["source"])).body
                       if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CONFIG_CHUNKS" for t in node.targets))
    initial_chunks = ast.literal_eval(config_node.value)
    playground_chunks = {**initial_chunks, "tokens_alvo": 600, "overlap_tokens": 0}
    try:
        ns["preparar_segmentacao"]("Uma proposta para analisar sem consultar provedores.", **playground_chunks)
        segmentation = {"error": None}
    except ValueError as exc:
        segmentation = {"error": str(exc), "initial_config": initial_chunks,
                        "playground_merged_config": playground_chunks}
    output = {"run_id": manifest["run_id"], "scope": "Reavaliação dos registros existentes; não houve nova inferência.",
              "notebook_sha256": hashlib.sha256((ROOT / "Pipeline - Passo a Passo.ipynb").read_bytes()).hexdigest(),
              "rubric_hash_matches_current_notebook": True, "question_hash_matches": True,
              "record_configs_match_manifest": True,
              "config": {k: v for k, v in saved_config.items() if k != "escala"},
              "scale": manifest["escala"]["id"], "metrics": results, "paired_changes": changes,
              "joint_delta": float(deltas.sum() / len(paired)),
              "joint_delta_ci95_question_bootstrap": np.percentile(draws, [2.5, 97.5]).tolist(),
              "llm_logical_calls": sum(r["chamadas_llm"] for r in records),
              "llm_observed_attempts": sum(r["chamadas_llm_efetivas"] for r in records),
              "routed_axis_cases": sum(len(r["eixos_encaminhados"]) for r in records),
              "routing_reasons": dict(route_reasons),
              "false_negatives_without_routing": false_negative_without_route,
              "playground_clean_config_check": segmentation}
    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
