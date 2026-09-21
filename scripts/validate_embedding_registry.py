"""Executa as células matriciais do registro de embeddings e valida a cobertura.

Fundamentação:
    Parschan e Jakob (2025), *Computational Measurement of Political
    Positions*, `artigos/Computational Measurement of Political Positions.pdf`,
    p. 16 e 30-31. A execução compara escolhas de embedding mantendo dados,
    protótipos, métricas, bootstrap e semente constantes.
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

from compare_embedding_models import (
    NOTEBOOK_PATH,
    ROOT,
    execute_notebook_cell,
    load_notebook_definitions,
)


def find_code_cell(marker: str) -> int:
    """Localiza uma célula de código por conteúdo estável, sem depender da posição."""
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    matches = [
        index
        for index, cell in enumerate(notebook["cells"])
        if cell.get("cell_type") == "code"
        and marker in "".join(cell.get("source", []))
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Marcador {marker!r}: esperava 1 célula, encontrei {matches}.")
    return matches[0]


def main() -> None:
    load_dotenv(ROOT / ".env")
    namespace = load_notebook_definitions()
    namespace["display"] = lambda _value: None

    markers = (
        "EMBEDDING_MODELS = {",
        "def build_embedding_experiments(",
        "embedding_experiments, embedding_initialization =",
        "# Validação de engenharia de todas as condições registradas.",
        "embedding_benchmark_frames = {}",
        "embedding_sensitivity_frames = {}",
    )
    for marker in markers:
        execute_notebook_cell(find_code_cell(marker), namespace)

    models = namespace["EMBEDDING_MODELS"]
    prototypes = namespace["EMBEDDING_PROTOTYPES"]
    expected_conditions = len(models) * len(prototypes)
    benchmark_frames = namespace["embedding_benchmark_frames"]
    sensitivity_frames = namespace["embedding_sensitivity_frames"]
    benchmark_summary = namespace["embedding_benchmark_summary"]

    assert len(benchmark_frames) == expected_conditions
    assert len(sensitivity_frames) == expected_conditions
    assert len(namespace["embedding_engineering_validation"]) == expected_conditions
    assert set(benchmark_summary["model_key"]) == set(models)
    assert set(benchmark_summary["prototype_set"]) == set(prototypes)

    overall = benchmark_summary.loc[
        benchmark_summary["axis"] == "overall",
        [
            "model_key",
            "prototype_set",
            "accuracy",
            "balanced_accuracy",
            "mcc",
            "majority_baseline",
            "evaluation_seconds",
        ],
    ]
    payload = {
        "models": list(models),
        "prototype_sets": list(prototypes),
        "conditions": expected_conditions,
        "pipeline_model": namespace["PIPELINE_EMBEDDING_MODEL"],
        "pipeline_prototypes": namespace["PIPELINE_PROTOTYPE_SET"],
        "overall": overall.to_dict(orient="records"),
    }
    output_path = ROOT / "content" / "validacao_registro_embeddings.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
