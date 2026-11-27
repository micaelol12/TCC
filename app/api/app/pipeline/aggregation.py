"""Agregação dos trechos válidos e dos diagnósticos de cada eixo."""
from collections import Counter
from math import ceil
import random
from statistics import mean

from ..experiment_config import ExperimentConfig
from ..polarity import COUNT_KEYS, level_score
from ..schemas import AxisResult, Evidence, EvidenceAudit, JevDiagnostic, LevelCounts

AXES = ("economic", "diplomatic", "state", "society")


def bootstrap_confidence_interval(values: list[float], config: ExperimentConfig):
    """Estima o intervalo de 95% por reamostragem com semente fixa; exige duas notas."""
    if len(values) < 2:
        return None
    random_generator = random.Random(config.bootstrap_seed)
    sample_means = sorted(
        mean(random_generator.choices(values, k=len(values)))
        for _ in range(config.bootstrap_samples)
    )
    # O posto mais próximo mantém os índices 49/1949 em 2.000 amostras.
    lower_index = ceil(0.025 * len(sample_means)) - 1
    upper_index = ceil(0.975 * len(sample_means)) - 1
    return sample_means[lower_index], sample_means[upper_index]


def axis_estimation_status(decisions: list[dict], valid_scores: list[float]) -> str:
    """Distingue um eixo estimado de ausência de evidência ou abstenção."""
    if valid_scores:
        return "estimated"
    return "no_evidence" if all(decision["relevante"] is False for decision in decisions) else "abstained"


def collect_axis_reasons(decisions: list[dict], valid_count: int, minimum_valid_count: int) -> list[str]:
    """Reúne motivos sem repetição e sinaliza quantidade insuficiente de trechos válidos."""
    reasons = list(dict.fromkeys(reason for decision in decisions for reason in decision["reason"]))
    if 0 < valid_count < minimum_valid_count:
        reasons.append("evidencia_limitada")
    return reasons


def collect_axis_methods(decisions: list[dict]) -> list[str]:
    """Reúne os métodos usados no eixo, preservando a ordem e os formatos anteriores."""
    return list(dict.fromkeys(
        method for decision in decisions
        for method in decision.get("methods", [decision["method"]] if decision["method"] else [])
    ))


def aggregate_axis(axis: str, decisions: list[dict], total_chunks: int, config: ExperimentConfig) -> AxisResult:
    """Calcula a média dos trechos válidos e reúne cobertura, incerteza e evidências do eixo."""
    # O centro é válido; ausência de evidência não equivale a uma posição 50.
    valid_decisions = [
        decision for decision in decisions
        if decision["relevante"] is True and decision["nivel"] is not None
    ]
    level_counts = Counter(decision["nivel"] for decision in valid_decisions)
    valid_scores = [level_score(decision["nivel"], config.escala) for decision in valid_decisions]
    # Todos os trechos válidos têm o mesmo peso, independentemente do tamanho.
    pole_a_score = mean(valid_scores) if valid_scores else None
    valid_count = len(valid_scores)
    return AxisResult(
        axis=axis,
        pole_a=pole_a_score,
        pole_b=None if pole_a_score is None else 100 - pole_a_score,
        status=axis_estimation_status(decisions, valid_scores),
        coverage=valid_count / total_chunks,
        valid_chunks=valid_count,
        total_chunks=total_chunks,
        sufficient_evidence=valid_count >= config.min_valid_chunks,
        level_counts=LevelCounts(**{name: level_counts.get(level, 0) for level, name in COUNT_KEYS.items()}),
        level_counts_by_key={level.chave: level_counts.get(level.codigo, 0) for level in config.escala.niveis},
        ci95=bootstrap_confidence_interval(valid_scores, config),
        methods_used=collect_axis_methods(decisions),
        reason_codes=collect_axis_reasons(decisions, valid_count, config.min_valid_chunks),
        evidence=[
            Evidence(chunk_index=index, quote=decision["quote"])
            for index, decision in enumerate(decisions) if decision["quote"]
        ],
        evidence_audit=[
            EvidenceAudit(chunk_index=index, **audit)
            for index, decision in enumerate(decisions) for audit in decision.get("evidence_audit", [])
        ],
        jev_diagnostics=[
            JevDiagnostic(chunk_index=index, **decision["jev_diagnostic"])
            for index, decision in enumerate(decisions) if decision.get("jev_diagnostic")
        ],
    )


def aggregate(results: list[dict], total_chunks: int, config: ExperimentConfig | None = None) -> list[AxisResult]:
    """Agrupa as decisões dos trechos e produz o resultado dos quatro eixos."""
    effective_config = config or ExperimentConfig()
    return [
        aggregate_axis(axis, [chunk[axis] for chunk in results], total_chunks, effective_config)
        for axis in AXES
    ]
