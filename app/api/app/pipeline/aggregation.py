from collections import Counter
from statistics import mean
import random
from math import ceil
from ..experiment_config import ExperimentConfig
from ..schemas import AxisResult, Evidence, EvidenceAudit, LevelCounts
from ..polarity import COUNT_KEYS, level_score

AXES = ("economic", "diplomatic", "state", "society")


def aggregate(results: list[dict], total_chunks: int, config: ExperimentConfig | None = None) -> list[AxisResult]:
    config = config or ExperimentConfig()
    output = []
    for axis in AXES:
        decisions = [chunk[axis] for chunk in results]
        values = [level_score(d["nivel"], config.escala) for d in decisions if d["relevante"] is True and d["nivel"] is not None]
        count = Counter(d["nivel"] for d in decisions if d["relevante"] is True and d["nivel"] is not None)
        score = mean(values) if values else None
        ci = None
        if len(values) >= 2:
            rng = random.Random(config.bootstrap_seed)
            samples = sorted(mean(rng.choices(values, k=len(values))) for _ in range(config.bootstrap_samples))
            # Nearest rank preserves the original indices 49/1949 for 2,000 draws.
            ci = (samples[ceil(0.025 * len(samples)) - 1], samples[ceil(0.975 * len(samples)) - 1])
        reasons = list(dict.fromkeys(r for d in decisions for r in d["reason"]))
        if values and len(values) < config.min_valid_chunks:
            reasons.append("evidencia_limitada")
        status = "estimated" if values else "no_evidence" if all(d["relevante"] is False for d in decisions) else "abstained"
        output.append(AxisResult(
            axis=axis, pole_a=score, pole_b=None if score is None else 100 - score,
            status=status, coverage=len(values) / total_chunks, valid_chunks=len(values), total_chunks=total_chunks,
            sufficient_evidence=len(values) >= config.min_valid_chunks,
            level_counts=LevelCounts(**{name: count.get(level, 0) for level, name in COUNT_KEYS.items()}),
            level_counts_by_key={n.chave: count.get(n.codigo, 0) for n in config.escala.niveis},
            ci95=ci, methods_used=list(dict.fromkeys(method for d in decisions for method in d.get("methods", [d["method"]] if d["method"] else []))),
            reason_codes=reasons,
            evidence=[Evidence(chunk_index=i, quote=d["quote"]) for i, d in enumerate(decisions) if d["quote"]],
            evidence_audit=[EvidenceAudit(chunk_index=i, **audit) for i, d in enumerate(decisions) for audit in d.get("evidence_audit", [])],
        ))
    return output
