from collections import Counter
from statistics import mean
import random
from ..schemas import AxisResult, Evidence, LevelCounts

AXES = ("economic", "diplomatic", "state", "society")
COUNT_KEYS = {-2: "minus2", -1: "minus1", 0: "zero", 1: "plus1", 2: "plus2"}


def aggregate(results: list[dict], total_chunks: int) -> list[AxisResult]:
    output = []
    for axis in AXES:
        decisions = [chunk[axis] for chunk in results]
        values = [50 + 25 * d["nivel"] for d in decisions if d["relevante"] is True and d["nivel"] is not None]
        count = Counter(d["nivel"] for d in decisions if d["relevante"] is True and d["nivel"] is not None)
        score = mean(values) if values else None
        ci = None
        if len(values) >= 2:
            rng = random.Random(42)
            samples = sorted(mean(rng.choices(values, k=len(values))) for _ in range(2000))
            ci = (samples[49], samples[1949])
        reasons = list(dict.fromkeys(r for d in decisions for r in d["reason"]))
        if values and len(values) < 16:
            reasons.append("evidencia_limitada")
        status = "estimated" if values else "no_evidence" if all(d["relevante"] is False for d in decisions) else "abstained"
        output.append(AxisResult(
            axis=axis, pole_a=score, pole_b=None if score is None else 100 - score,
            status=status, coverage=len(values) / total_chunks, valid_chunks=len(values), total_chunks=total_chunks,
            sufficient_evidence=len(values) >= 16,
            level_counts=LevelCounts(**{name: count.get(level, 0) for level, name in COUNT_KEYS.items()}),
            ci95=ci, methods_used=list(dict.fromkeys(method for d in decisions for method in d.get("methods", [d["method"]] if d["method"] else []))),
            reason_codes=reasons,
            evidence=[Evidence(chunk_index=i, quote=d["quote"]) for i, d in enumerate(decisions) if d["quote"]],
        ))
    return output
