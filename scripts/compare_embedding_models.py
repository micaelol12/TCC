"""Compara provedores de embeddings no benchmark interno do TCC.

Fundamentacao metodologica:
    Parschan e Jakob (2025), *Computational Measurement of Political
    Positions*, `artigos/Computational Measurement of Political Positions.pdf`,
    pp. 16-17 e 30-31. A revisao recomenda padrao-ouro externo e verificacoes de
    robustez, incluindo bootstrap, para medidas politicas baseadas em embeddings.

    Duan et al. (2025), *Constructing Vec-tionaries to Extract Message Features
    from Texts*, `artigos/constructing-vec-tionaries-to-extract-message-features-
    from-texts-a-case-study-of-moral-content.pdf`, pp. 427-429. O artigo sustenta
    a representacao de conceitos por polos no mesmo espaco vetorial e a avaliacao
    contra anotacoes humanas.

Adaptacao e limite:
    As perguntas do 8values sao um benchmark interno, nao um padrao-ouro humano
    independente para planos de governo. O bootstrap pareado quantifica a
    incerteza amostral do benchmark, mas nao a validade externa do construto.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, TypeAdapter
from sentence_transformers import SentenceTransformer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    matthews_corrcoef,
)


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "TCC.ipynb"
QUESTIONS_PATH = ROOT / "content" / "questions.json"
OUTPUT_PATH = ROOT / "content" / "comparacao_embeddings.json"
BOOTSTRAP_REPLICATES = 2_000
BOOTSTRAP_SEED = 42


def notebook_cell_source(index: int) -> str:
    """Le o codigo canonico do notebook para evitar uma segunda implementacao."""
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cell = notebook["cells"][index]
    if cell["cell_type"] != "code":
        raise ValueError(f"A celula {index} nao e de codigo.")
    return "".join(cell["source"])


def execute_notebook_cell(index: int, namespace: dict) -> None:
    """Executa uma celula sem herdar flags ``__future__`` deste harness."""
    code = compile(
        notebook_cell_source(index),
        f"{NOTEBOOK_PATH.name}:cell-{index}",
        "exec",
        dont_inherit=True,
    )
    exec(code, namespace)


def load_notebook_definitions() -> dict:
    """Carrega tipos, prototipos, algoritmo e metricas diretamente do notebook."""
    namespace = globals().copy()
    execute_notebook_cell(5, namespace)

    questions_data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    namespace["QUESTIONS"] = TypeAdapter(list[namespace["Question"]]).validate_python(
        questions_data
    )

    for cell_index in (156, 157, 159, 161, 165):
        execute_notebook_cell(cell_index, namespace)
    return namespace


def paired_bootstrap_accuracy_delta(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    """Estima IC95% pareado, reamostrando perguntas como grupos indivisiveis."""
    keys = ["id", "axis", "effect"]
    merged = reference[keys + ["correct"]].merge(
        candidate[keys + ["correct"]],
        on=keys,
        how="inner",
        suffixes=("_reference", "_candidate"),
        validate="one_to_one",
    )
    if len(merged) != len(reference) or len(merged) != len(candidate):
        raise AssertionError("As predicoes nao formam pares completos.")

    merged["correct_delta"] = (
        merged["correct_candidate"].astype(float)
        - merged["correct_reference"].astype(float)
    )
    observed = float(merged["correct_delta"].mean())
    rng = np.random.default_rng(seed)
    question_ids = merged["id"].unique()
    estimates = np.empty(replicates, dtype=float)
    for index in range(replicates):
        sampled_ids = rng.choice(question_ids, size=len(question_ids), replace=True)
        sampled_groups = [
            merged.loc[merged["id"] == question_id, "correct_delta"].to_numpy()
            for question_id in sampled_ids
        ]
        estimates[index] = float(np.concatenate(sampled_groups).mean())
    lower, upper = np.quantile(estimates, [0.025, 0.975])
    reference_correct = merged["correct_reference"].to_numpy(dtype=float)
    candidate_correct = merged["correct_candidate"].to_numpy(dtype=float)
    return {
        "n": int(len(merged)),
        "question_groups": int(len(question_ids)),
        "accuracy_delta": observed,
        "ci_2.5%": float(lower),
        "ci_97.5%": float(upper),
        "candidate_wins": int(np.sum((candidate_correct == 1) & (reference_correct == 0))),
        "reference_wins": int(np.sum((candidate_correct == 0) & (reference_correct == 1))),
    }


def evaluate_condition(namespace: dict, model_name: str, prototype_name: str) -> dict:
    """Executa uma condicao completa e devolve metricas e predicoes pareadas."""
    if model_name == "multilingual-e5-base":
        started = time.perf_counter()
        embedding_model = namespace["SentenceTransformerEmbeddingModel"](
            "intfloat/multilingual-e5-base",
            query_prefix="query: ",
        )
        initialization_seconds = time.perf_counter() - started
    elif model_name == "text-embedding-3-large":
        started = time.perf_counter()
        embedding_model = namespace["OpenAIEmbeddingModel"](
            model_name="text-embedding-3-large",
            dimensions=None,
            client=OpenAI(api_key=os.environ["OPENAI_API_KEY"]),
        )
        initialization_seconds = time.perf_counter() - started
    else:
        raise ValueError(f"Modelo desconhecido: {model_name}")

    prototype_data = namespace[prototype_name]
    started = time.perf_counter()
    semantic = namespace["Semantic8Values"](
        prototype_data,
        embedding_model=embedding_model,
        embedding_cache={},
    )
    axis_initialization_seconds = time.perf_counter() - started

    started = time.perf_counter()
    predictions = namespace["test_semantic8values"](
        semantic,
        questions=namespace["QUESTIONS"],
        min_abs_effect=10,
    )
    evaluation_seconds = time.perf_counter() - started
    summary = namespace["resumo_testes"](
        predictions,
        n_bootstrap=BOOTSTRAP_REPLICATES,
        seed=BOOTSTRAP_SEED,
    ).reset_index()

    return {
        "model": model_name,
        "prototypes": prototype_name,
        "dimensions": int(next(iter(semantic.axis_embeddings.values()))["direction"].shape[0]),
        "initialization_seconds": initialization_seconds,
        "axis_initialization_seconds": axis_initialization_seconds,
        "evaluation_seconds": evaluation_seconds,
        "summary": summary.to_dict(orient="records"),
        "predictions": predictions,
    }


def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY ausente; a comparacao real nao pode ser executada.")

    namespace = load_notebook_definitions()
    results = {}
    raw_predictions = {}

    for prototype_name in ("TEXTOS_EIXOS_1", "TEXTOS_EIXOS_2"):
        for model_name in ("multilingual-e5-base", "text-embedding-3-large"):
            key = f"{model_name}::{prototype_name}"
            print(f"Executando {key}", flush=True)
            condition = evaluate_condition(namespace, model_name, prototype_name)
            raw_predictions[key] = condition.pop("predictions")
            results[key] = condition

    comparisons = {}
    for prototype_name in ("TEXTOS_EIXOS_1", "TEXTOS_EIXOS_2"):
        reference_key = f"multilingual-e5-base::{prototype_name}"
        candidate_key = f"text-embedding-3-large::{prototype_name}"
        comparisons[prototype_name] = paired_bootstrap_accuracy_delta(
            raw_predictions[reference_key],
            raw_predictions[candidate_key],
        )

    payload = {
        "experiment": {
            "benchmark": "70 perguntas do 8values; 91 associacoes com |effect| = 10",
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "openai_dimensions": "default (3072 segundo a documentacao oficial)",
            "limitation": (
                "Benchmark interno; nao demonstra validade externa em planos de governo."
            ),
        },
        "conditions": results,
        "paired_comparisons_openai_minus_e5": comparisons,
    }
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
