"""Comparação numérica CPU/GPU, infraestrutura de reprodução R4.

Referências e limites em METODOLOGIA.md. O runtime e o batch também mudam;
diferenças de duração não isolam um efeito causal do hardware.
"""
import argparse
import json
from pathlib import Path

from .protocolo import write_json


def compare(root, suffix="20260916"):
    """R4: alinha IDs, confere entradas/modelos e compara decisões persistidas."""
    root = Path(root)

    def load(run, filename):
        """R4: lê somente artefatos identificados da execução, sem recalcular modelos."""
        return json.loads((root / run / filename).read_text(encoding="utf-8"))

    pairs = [("diagnostico", f"diagnostico_e5_{suffix}", f"diagnostico_e5_gpu_{suffix}"),
             ("documento", f"documento_6x1_{suffix}", f"documento_6x1_gpu_{suffix}"),
             ("controlados", f"controlados_{suffix}", f"controlados_gpu_{suffix}")]
    result = {"limitations": ["Mudam hardware, Python/PyTorch e tamanho dos lotes",
                              "Tempos incluem carregamento, exceto o diagnóstico",
                              "Concordância CPU/GPU não valida acurácia documental"]}
    for name, cpu, gpu in pairs:
        left, right = load(cpu, "manifest.json"), load(gpu, "manifest.json")
        entry = {"cpu_run": cpu, "gpu_run": gpu, "same_input_hashes": left["input_hashes"] == right["input_hashes"],
                 "cpu_seconds": left["elapsed_seconds"], "gpu_seconds": right["elapsed_seconds"],
                 "gpu": right.get("gpu"), "model_revisions_equal": {}}
        for key in ("encoder", "nli"):
            if key in left["config"] and key in right["config"]:
                entry["model_revisions_equal"][key] = left["config"][key]["revision"] == right["config"][key]["revision"]
        if name == "diagnostico":
            a, b = load(cpu, "diagnostico_previsoes.json"), load(gpu, "diagnostico_previsoes.json")
            columns = ("question_id", "axis", "method", "calibration")
            index = {tuple(r[k] for k in columns): r for r in b}
            if set(index) != {tuple(r[k] for k in columns) for r in a}:
                raise ValueError("Diagnósticos têm unidades diferentes")
            aligned = [(r, index[tuple(r[k] for k in columns)]) for r in a]
            entry.update({"n_predictions": len(aligned),
                          "same_predictions": sum(x["prediction"] == y["prediction"] for x, y in aligned),
                          "max_abs_score_difference": max(abs(x["score"] - y["score"]) for x, y in aligned)})
        elif name == "documento":
            a, b = load(cpu, "documento.json"), load(gpu, "documento.json")
            for segmentation in ("base", "alternate"):
                index = {str(r["question_id"]): r for r in b[segmentation]["items"]}
                if set(index) != {str(r["question_id"]) for r in a[segmentation]["items"]}:
                    raise ValueError("Documentos têm perguntas diferentes")
                aligned = [(r, index[str(r["question_id"])]) for r in a[segmentation]["items"]]
                changes, errors, same_retrieval = [], [], 0
                for x, y in aligned:
                    if x["state"] != y["state"]:
                        changes.append({"question_id": x["question_id"], "cpu": x["state"], "gpu": y["state"]})
                    evidence = {r["id"]: r for r in y["evidence"]}
                    same_retrieval += {r["id"] for r in x["evidence"]} == set(evidence)
                    for e in x["evidence"]:
                        if e["id"] in evidence:
                            errors.extend(abs(e[k] - evidence[e["id"]][k]) for k in ("entailment", "neutral", "contradiction"))
                entry[segmentation] = {"n": len(aligned), "same_states": len(aligned) - len(changes),
                                       "same_retrieved_sets": same_retrieval, "changes": changes,
                                       "max_abs_probability_difference_shared_evidence": max(errors, default=None)}
        else:
            a, b = load(cpu, "templates_nli.json"), load(gpu, "templates_nli.json")
            index = {r["id"]: r for r in b}
            if set(index) != {r["id"] for r in a}:
                raise ValueError("Templates diferentes")
            entry.update({"n": len(a), "same_predictions": sum(r["predicted"] == index[r["id"]]["predicted"] for r in a),
                          "gpu_satisfied": sum(r["satisfied"] for r in b)})
        result[name] = entry
    write_json(root / f"comparacao_cpu_gpu_{suffix}.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("analises/execucoes"))
    args = parser.parse_args()
    print(json.dumps(compare(args.root), ensure_ascii=False, indent=2))
