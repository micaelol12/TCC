"""Diagnósticos locais da revisão bibliográfica, sem clientes nem chamadas remotas.

Execute na raiz: .venv/Scripts/python.exe analise_jev_llm/diagnostico_revisao_artigos.py
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app/api"))

from app.experiment_config import ExperimentConfig
from app.pipeline.aggregation import aggregate
from app.pipeline.domain import _normalizar_polaridade_ordinal
from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


def decision(level):
    return {"relevante": level is not None, "nivel": level, "method": "jev",
            "methods": ["jev"], "reason": [], "quote": None}


def api_summary(levels, config):
    rows = [{axis: decision(level) for axis in ("economic", "diplomatic", "state", "society")}
            for level in levels]
    axis = aggregate(rows, len(rows), config)[0]
    return axis.model_dump(mode="json", include={"pole_a", "ci95", "coverage", "valid_chunks",
                                                "sufficient_evidence", "level_counts_by_key"})


def main():
    config = ExperimentConfig()
    ns = carregar_pipeline_notebook()
    scale = config.escala
    output = {
        "scope": "Entradas sintéticas; verifica comportamento do código, não acurácia semântica.",
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "Pipeline - Passo a Passo.ipynb", "app/api/app/pipeline/aggregation.py",
            "app/api/app/pipeline/domain.py", "app/api/analysis-config.json")},
        "api_defaults": config.model_dump(mode="json", exclude={"escala"}),
    }
    output["same_mean_different_content"] = {
        "all_center": api_summary([0, 0], config),
        "opposed_extremes": api_summary([-4, 4], config),
        "sixteen_repeated_center": api_summary([0] * 16, config),
    }
    probabilities = {n.chave: .14 if n.polo == "A" else .05 if n.polo == "B" else .24
                     for n in scale.niveis}
    # Confidence is only a placeholder required by the normalizer. No routing
    # or calibration conclusion is derived from this synthetic field.
    raw = {"probabilities": probabilities, "confidence": .2}
    output["decision_rule_illustration"] = {
        rule: _normalizar_polaridade_ordinal(raw, True, primitiva="choice", escala=scale,
                                           regra_decisao=rule)
        for rule in ("nivel", "polo_primeiro")
    }
    levels = [-4] * 10 + [None] * 3 + [4] * 10
    decisions = [{**ns["decisao_vazia"]("economic"), **decision(level), "metodo": "jev_ordinal"}
                 for level in levels]
    notebook = ns["resumir_eixo_ordinal"](decisions, n_bootstrap=2000, semente=42,
                                       escala=ns["validar_escala"](scale.model_dump(mode="json")))
    output["bootstrap_comparison"] = {
        "input_levels": levels,
        "api": api_summary(levels, config),
        "notebook": {k: notebook[k] for k in ("índice A", "cobertura", "chunks com nível",
                                             "IC95 inferior", "IC95 superior")},
    }
    nb = json.loads((ROOT / "Pipeline - Passo a Passo.ipynb").read_text(encoding="utf-8"))
    configs = []
    for index, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        try:
            tree = ast.parse("".join(cell["source"]))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CONFIG_CHUNKS"
                                                    for t in node.targets):
                configs.append({"cell_index_zero_based": index, "value": ast.literal_eval(node.value)})
    output["notebook_chunk_config_assignments"] = configs
    output["schwartz_duplicate_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "tcc").glob("*.pdf") if "schwartz" in p.name.lower() or "ABORDAGEM" in p.name}
    destination = Path(__file__).with_name("diagnostico_revisao_artigos.json")
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(destination), "bootstrap": output["bootstrap_comparison"],
                      "chunk_configs": configs}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
