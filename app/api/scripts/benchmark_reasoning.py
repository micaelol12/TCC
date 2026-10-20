"""Benchmark JEV/LLM. Gera apenas results.jsonl, summary.csv e report.md.

Plano: python app/api/scripts/benchmark_reasoning.py
Executar: python app/api/scripts/benchmark_reasoning.py --live --repeats 2
Recalcular sem API: python app/api/scripts/benchmark_reasoning.py --summarize PASTA
"""
import argparse
import asyncio
from collections import defaultdict
from contextvars import ContextVar
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter

API = Path(__file__).resolve().parents[1]
ROOT = API.parents[1]
sys.path.insert(0, str(API))

from app.experiment_config import PIPELINE_VERSION
from app.pipeline.rubrics import AXIS_SPECS
from app.pipeline.strategies import classify_chunk, empty, jev_decisions

TRACE = ContextVar("benchmark_trace")


def arms_for(config, thresholds):
    arms = [("atual_baixo", "low", config), ("atual_medio", "medium", config),
            ("atual_alto", "high", config)]
    for threshold in sorted(set(thresholds)):
        if threshold != config.level_confidence_min:
            arms.append((f"cascata_{threshold:.4f}".rstrip("0").rstrip("."), "medium",
                         config.model_copy(update={"level_confidence_min": threshold})))
    return arms


def split_questions(questions, seed):
    """Split by question, stratified by its largest absolute reference effect."""
    groups = defaultdict(list)
    for q in questions:
        primary = max(q["effect"], key=lambda axis: abs(q["effect"][axis]))
        groups[primary].append(q["id"])
    rng = random.Random(seed)
    test = set()
    for ids in groups.values():
        rng.shuffle(ids)
        test.update(ids[:max(1, round(len(ids) * .3))])
    return {q["id"]: "test" if q["id"] in test else "calibration" for q in questions}


def score_decisions(decisions, effects):
    rows = []
    for axis, spec in AXIS_SPECS.items():
        d = decisions[axis]
        effect = effects[spec["effect"]]
        level = d.get("nivel")
        predicted = (1 if level > 0 else -1 if level < 0 else 0) if (
            d.get("relevante") is True and level is not None) else None
        target = 1 if effect > 0 else -1 if effect < 0 else None
        rows.append({"axis": axis, "effect": effect, "target": target,
                     "predicted": predicted, "correct": int(predicted == target) if target else None,
                     "covered": int(predicted in (-1, 1)), "decision": d})
    return rows


def percentile(values, fraction):
    values = sorted(values)
    offset = (len(values) - 1) * fraction
    lo = int(offset)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (offset - lo)


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["arm"], row["split"])].append(row)
        groups[(row["arm"], "all")].append(row)
    result = []
    for (arm, split), records in sorted(groups.items()):
        labeled = [a for r in records for a in r["axes"] if a["target"] is not None]
        by_axis = defaultdict(list)
        for a in labeled:
            by_axis[a["axis"]].append(a["correct"])
        correct = sum(a["correct"] for a in labeled)
        covered = sum(a["covered"] for a in labeled)
        seconds = [r["seconds"] for r in records]
        zero = [a for r in records for a in r["axes"] if a["target"] is None]
        all_axes = labeled + zero
        joint_correct = correct + sum(a["decision"]["relevante"] is False for a in zero)
        relevance_correct = sum(a["decision"]["relevante"] is (a["target"] is not None) for a in all_axes)
        result.append({"arm": arm, "split": split, "questions": len({r["question_id"] for r in records}),
            "executions": len(records), "targets": len(labeled), "correct": correct,
            "accuracy": correct / len(labeled) if labeled else None,
            "total_axis_cases": len(all_axes), "joint_correct": joint_correct,
            "joint_accuracy": joint_correct / len(all_axes),
            "relevance_accuracy": relevance_correct / len(all_axes),
            "macro_axis_accuracy": statistics.mean(statistics.mean(v) for v in by_axis.values()) if by_axis else None,
            "coverage": covered / len(labeled) if labeled else None,
            "selective_accuracy": correct / covered if covered else None,
            "zero_effect_directional_rate": sum(a["covered"] for a in zero) / len(zero) if zero else None,
            "seconds_mean": statistics.mean(seconds), "seconds_p50": percentile(seconds, .5),
            "seconds_p95": percentile(seconds, .95),
            "jev_logical": sum(r["logical_calls"]["jev"] for r in records),
            "llm_logical": sum(r["logical_calls"]["llm"] for r in records),
            "jev_http_attempts": sum(r["http_attempts"]["jev"] for r in records),
            "llm_http_attempts": sum(r["http_attempts"]["llm"] for r in records),
            "llm_rate": statistics.mean(r["logical_calls"]["llm"] > 0 for r in records),
            "llm_axes": sum(a["decision"].get("method") == "llm" for r in records for a in r["axes"]),
            "provider_failure_executions": sum(any(reason.startswith("falha_") for a in r["axes"]
                for reason in a["decision"].get("reason", [])) or r["timed_out"] for r in records),
            "invalid_evidence_axes": sum("evidencia_nao_verificada" in a["decision"].get("reason", [])
                                          for r in records for a in r["axes"])})
    return result


def paired_intervals(rows, seed, samples=2000):
    """Bootstrap paired questions; axes/repetitions of a question stay together."""
    grouped = defaultdict(dict)
    for r in rows:
        labeled = [a for a in r["axes"] if a["target"] is not None]
        grouped[(r["arm"], r["split"])][(r["question_id"], r["repeat"])] = (
            sum(a["correct"] for a in labeled), len(labeled))
    output = []
    for (arm, split), values in sorted(grouped.items()):
        for baseline in ("atual_medio", "atual_alto"):
            if arm == baseline:
                continue
            other = grouped.get((baseline, split), {})
            shared = sorted(values.keys() & other.keys())
            question_groups = defaultdict(list)
            for key in shared:
                question_groups[key[0]].append(key)
            ids = sorted(question_groups)
            if not ids:
                continue
            def delta(sample):
                keys = [key for q in sample for key in question_groups[q]]
                count = sum(values[k][1] for k in keys)
                return sum(values[k][0] - other[k][0] for k in keys) / count
            rng = random.Random(seed)
            draws = [delta(rng.choices(ids, k=len(ids))) for _ in range(samples)]
            output.append({"arm": arm, "baseline": baseline, "split": split,
                           "paired_questions": len(ids), "delta_accuracy": delta(ids),
                           "ci95_low": percentile(draws, .025), "ci95_high": percentile(draws, .975)})
    return output


def write_csv(path, records):
    if records:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)


def balanced_rows(rows, manifest):
    expected = {(str(qid), arm["name"]) for qid in manifest["split"] for arm in manifest["arms"]}
    complete = []
    for repeat in range(manifest["repeats"]):
        current = [r for r in rows if r["repeat"] == repeat]
        keys = {(str(r["question_id"]), r["arm"]) for r in current}
        if len(current) != len(expected) or keys != expected:
            break
        complete.append(repeat)
    return ([r for r in rows if r["repeat"] in complete], complete) if complete else (rows, [])


def save_report(output, rows, manifest):
    selected, complete = balanced_rows(rows, manifest)
    summary = summarize(selected)
    pairs = paired_intervals(selected, manifest["seed"])
    write_csv(output / "summary.csv", summary)
    def pct(value):
        return f"{100 * value:.1f}%" if value is not None else "—"
    lines = ["# Comparação JEV/LLM — perguntas 8values", "",
        f"Execuções registradas: {len(rows)}/{manifest['expected_executions']}. Estado: {manifest['status']}.",
        f"Modelos solicitados: {manifest['config']['jev_model']} / {manifest['config']['llm_model']}.",
        f"Concorrência: {manifest['concurrency']}; repetições planejadas: {manifest['repeats']}.",
        f"Comparação principal: {len(selected)} análises; {len(complete)} repetições iniciais completas. "
        f"{len(rows)-len(selected)} análises de rodadas incompletas preservadas somente no JSONL.", "",
        "Se nenhuma rodada estiver completa, os números são parciais e não sustentam uma comparação balanceada.", "",
        "Acurácia conjunta: nos efeitos não nulos, exige relevância e polo corretos; "
        "nos efeitos zero, exige declarar irrelevância. É a convenção do benchmark anterior. "
        "Acurácia de relevância verifica apenas se o eixo é relevante, sem exigir polo correto.", "",
        "Acurácia direcional = acertos / todos os eixos com efeito diferente de zero. "
        "Ausência, posição intermediária, abstenção e falha contam como erro nesses alvos. "
        "Efeito zero não é rótulo de neutralidade nem prova de irrelevância; fica fora da acurácia. "
        "O sinal do efeito determina o polo A/B; a magnitude não é usada como rótulo ordinal.", "",
        "Latência real de classify_chunk, incluindo rede, validação e retries; sem fila, HTTP do app, "
        "segmentação ou agregação. Uma pergunta corresponde a um trecho. Nenhuma resposta é "
        "reaproveitada pelo script entre braços. O aquecimento fica no JSONL, fora das métricas.", "",
        "Chamadas HTTP são tentativas de envio observadas no cliente (inclusive retries), "
        "não uma confirmação de cobrança. O médio agrupa os eixos incertos numa chamada LLM.", ""]
    for split, title in (("all", "Todas as perguntas (descritivo)"), ("calibration", "Calibração"), ("test", "Teste reservado")):
        lines.extend([f"## {title}", "", "| Estratégia | Conjunta | Relevância | Direcional | LLM lógicas | LLM HTTP | JEV HTTP | Média s | P50 s | P95 s | Falhas* |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for s in summary:
            if s["split"] == split:
                lines.append(f"| {s['arm']} | {pct(s['joint_accuracy'])} | {pct(s['relevance_accuracy'])} | "
                    f"{pct(s['accuracy'])} | {s['llm_logical']} | {s['llm_http_attempts']} | "
                    f"{s['jev_http_attempts']} | {s['seconds_mean']:.2f} | {s['seconds_p50']:.2f} | "
                    f"{s['seconds_p95']:.2f} | {s['provider_failure_executions']} |")
        lines.append("")
    all_metrics = {s["arm"]: s for s in summary if s["split"] == "all"}
    if all(name in all_metrics for name in ("atual_baixo", "atual_medio", "atual_alto")):
        low, medium, high = (all_metrics[name] for name in ("atual_baixo", "atual_medio", "atual_alto"))
        lines.extend(["## Interpretação", "",
            f"A acurácia conjunta foi {pct(low['joint_accuracy'])} no baixo, "
            f"{pct(medium['joint_accuracy'])} no médio e {pct(high['joint_accuracy'])} no alto. "
            f"Os tempos médios foram {low['seconds_mean']:.2f} s, {medium['seconds_mean']:.2f} s "
            f"e {high['seconds_mean']:.2f} s, respectivamente.", "",
            f"No médio, a direção teve {medium['correct']}/{medium['targets']} acertos "
            f"({pct(medium['accuracy'])}). Incluindo acertos de irrelevância nos efeitos zero, "
            f"a conjunta teve {medium['joint_correct']}/{medium['total_axis_cases']} acertos "
            f"({pct(medium['joint_accuracy'])}). Esses percentuais têm denominadores diferentes; "
            "não representam uma queda entre duas execuções da mesma métrica.", ""])
        strict = all_metrics.get("cascata_0.9")
        if strict:
            lines.extend([f"A cascata 0,90 teve conjunta {pct(strict['joint_accuracy'])}, direcional "
                f"{pct(strict['accuracy'])}, {strict['llm_logical']} chamadas LLM e tempo médio "
                f"{strict['seconds_mean']:.2f} s. O médio teve {medium['llm_logical']} chamadas LLM. "
                "Comparar qualidade, chamadas e tempo em conjunto antes de atribuir níveis.", ""])
        if medium["joint_accuracy"] > high["joint_accuracy"]:
            lines.extend(["Neste recorte, o modo alto não superou o médio na acurácia conjunta. "
                "O baixo serve como opção rápida, o médio como referência híbrida e o alto "
                "permanece uma opção experimental de revisão por LLM. Os nomes não garantem "
                "uma ordem crescente de precisão.", ""])
    lines.extend(["## Diferenças de acurácia direcional", "",
        "Bootstrap pareado por pergunta, 2.000 amostras; eixos e repetições da mesma pergunta ficam juntos. "
        "Comparações exploratórias, sem correção por múltiplas comparações.", "",
        "| Estratégia | Referência | Partição | Diferença (p.p.) | IC95% (p.p.) |",
        "|---|---|---|---:|---:|"])
    for p in pairs:
        lines.append(f"| {p['arm']} | {p['baseline']} | {p['split']} | {100*p['delta_accuracy']:.1f} | "
                     f"[{100*p['ci95_low']:.1f}; {100*p['ci95_high']:.1f}] |")
    lines.extend(["*Falhas = execuções com motivo de falha de provedor (inclusive recuperada por fallback) ou timeout.", "",
        "## Limites de interpretação", "",
        "Os limiares alteram somente level_confidence_min. Relevância, margem de direção, modelos "
        "e rubricas permanecem fixos. Baixo e alto mantêm as estratégias atuais. O braço atual_medio "
        f"também representa a cascata no limiar {manifest['config']['level_confidence_min']:.2f}.", "",
        "Escolher limiares usando apenas calibração e conferir a escolha no teste reservado. "
        "A base é pequena, já usada no desenvolvimento das rubricas e não mede generalização para "
        "textos reais. Uma única repetição não demonstra estabilidade. Confiança JEV não é "
        "probabilidade empírica de acerto. Variações entre chamadas e condições de rede podem "
        "quebrar a monotonicidade observada. Limiares maiores não garantem maior acurácia.", "",
        "Não foi alterada a configuração de produção nem atribuídos novos níveis automaticamente.", "",
        "## Como repetir", "",
        "Na raiz do projeto, com o ambiente Python da API:", "", "```powershell",
        r".\app\api\.venv\Scripts\python.exe app/api/scripts/benchmark_reasoning.py",
        r".\app\api\.venv\Scripts\python.exe -u app/api/scripts/benchmark_reasoning.py --live --repeats 2",
        r".\app\api\.venv\Scripts\python.exe app/api/scripts/benchmark_reasoning.py --summarize PASTA_DA_EXECUCAO",
        "```", "",
        "Sem --live, o script só mostra o plano. --summarize recalcula o CSV e o relatório sem API. "
        "--live usa as credenciais locais JEV/Maritaca e consome chamadas. "
        "--thresholds, --limit, --max-http-calls e --output permitem limitar a execução.", "",
        "São gerados somente três arquivos por execução: results.jsonl (resultados, aquecimento e "
        "metadados), summary.csv e report.md. O JSONL preserva inclusive rodadas incompletas; "
        "o resumo usa somente rodadas iniciais completas quando disponíveis."])
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


class InstrumentedJev:
    def __init__(self, client):
        self.client = client

    async def system_one(self, **kwargs):
        result = await self.client.system_one(**kwargs)
        decisions, _ = jev_decisions(result)
        TRACE.get()["jev_original"] = {axis: d.get("original") for axis, d in decisions.items()}
        return result


async def execute_case(q, arm, repeat, split, jev, llm, questions, settings):
    name, mode, config = arm
    trace = {"http_attempts": {"jev": 0, "llm": 0}, "http_statuses": [], "jev_original": {}}
    token = TRACE.set(trace)
    start = perf_counter()
    timeout = False
    try:
        try:
            decisions, calls, models = await asyncio.wait_for(
                classify_chunk(q["question"], mode, jev, questions, llm, settings, config),
                timeout=settings.timeout_seconds)
        except asyncio.TimeoutError:
            timeout = True
            decisions = {axis: empty("falha_timeout") for axis in AXIS_SPECS}
            calls = {provider: int(count > 0) for provider, count in trace["http_attempts"].items()}
            models = []
        return {"type": "result", "question_id": q["id"], "text": q["question"], "arm": name, "mode": mode,
            "threshold": config.level_confidence_min, "repeat": repeat, "split": split,
            "seconds": perf_counter() - start, "timed_out": timeout, "logical_calls": calls,
            "models": models, "axes": score_decisions(decisions, q["effect"]), **trace}
    finally:
        TRACE.reset(token)


async def run(args):
    from app.settings import Settings
    from app.pipeline.clients import jev_questions
    from app.pipeline.segmentation import split_text
    from typesafe_sdk import AsyncTypeSafeClient
    from openai import AsyncOpenAI
    import httpx
    import httpx2

    settings = Settings()
    config = settings.algorithm_defaults()
    questions_path = ROOT / "tcc" / "questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    splits = split_questions(questions, args.seed)
    random.Random(args.seed).shuffle(questions)
    if args.limit:
        questions = questions[:args.limit]
    for q in questions:
        chunks, _ = split_text(q["question"], max_tokens=settings.max_tokens, chunk_tokens=config.chunk_tokens)
        if len(chunks) != 1:
            raise ValueError("Este benchmark exige perguntas de um único trecho.")
    arms = arms_for(config, args.thresholds)
    expected = len(questions) * len(arms) * args.repeats
    print(json.dumps({"questions": len(questions), "arms": [a[0] for a in arms],
        "executions": expected, "http_budget": args.max_http_calls, "live": args.live}, ensure_ascii=False), flush=True)
    if not args.live:
        return
    if not settings.typesafe_key or not settings.maritaca_key:
        raise ValueError("São necessárias TYPESAFE_API_KEY e MARITACA_API_KEY no ambiente de desenvolvimento.")
    output = args.output.resolve() if args.output else ROOT / "runs" / "reasoning" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    source_hash = hashlib.sha256()
    for path in sorted((API / "app" / "pipeline").glob("*.py")) + [Path(__file__), API / "app" / "experiment_config.py"]:
        source_hash.update(path.name.encode())
        source_hash.update(path.read_bytes())
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running",
        "pipeline_version": PIPELINE_VERSION, "source_sha256": source_hash.hexdigest(),
        "dataset_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
        "config": config.model_dump(), "seed": args.seed, "concurrency": args.concurrency,
        "repeats": args.repeats, "expected_executions": expected, "max_http_calls": args.max_http_calls,
        "arms": [{"name": name, "mode": mode, "threshold": c.level_confidence_min} for name, mode, c in arms],
        "split": {str(q["id"]): splits[q["id"]] for q in questions},
        "versions": {name: version(name) for name in ("typesafe-sdk", "openai", "pydantic")}}
    total_http = 0
    stopped = False
    def hooks(provider):
        async def request_hook(request):
            nonlocal total_http, stopped
            if total_http >= args.max_http_calls:
                stopped = True
                raise RuntimeError("benchmark_http_budget")
            total_http += 1
            TRACE.get()["http_attempts"][provider] += 1
        async def response_hook(response):
            nonlocal stopped
            TRACE.get()["http_statuses"].append({"provider": provider, "status": response.status_code})
            if response.status_code in (401, 402, 403, 429):
                stopped = True
        return {"request": [request_hook], "response": [response_hook]}
    jev_http = httpx2.AsyncClient(event_hooks=hooks("jev"))
    llm_http = httpx.AsyncClient(event_hooks=hooks("llm"))
    jev_client = AsyncTypeSafeClient(api_key=settings.typesafe_key, model=config.jev_model,
                                    http_client=jev_http, timeout=settings.timeout_seconds)
    llm = AsyncOpenAI(api_key=settings.maritaca_key, base_url="https://chat.maritaca.ai/api",
                     timeout=settings.timeout_seconds, max_retries=0, http_client=llm_http)
    jev = InstrumentedJev(jev_client)
    provider_questions = jev_questions()
    rows = []
    results_path = output / "results.jsonl"
    results_path.write_text(json.dumps({"type": "manifest", "stage": "start", **manifest}, ensure_ascii=False) + "\n", encoding="utf-8")
    save_report(output, rows, manifest)
    print(f"OUTPUT={output}", flush=True)
    try:
        warm_q = {"id": "warmup", "question": "Defendo a redução das desigualdades por impostos progressivos e serviços públicos universais.",
                  "effect": {"econ": 10, "dipl": 0, "govt": 0, "scty": 0}}
        warmups = []
        for arm in (arms[0], arms[2]):
            if stopped:
                break
            row = await execute_case(warm_q, arm, 0, "warmup", jev, llm, provider_questions, settings)
            warmups.append(row)
            if any(reason.startswith("falha_") for a in row["axes"] for reason in a["decision"].get("reason", [])):
                stopped = True
        with results_path.open("a", encoding="utf-8") as stream:
            for row in warmups:
                stream.write(json.dumps({**row, "type": "warmup"}, ensure_ascii=False) + "\n")
        jobs = []
        rng = random.Random(args.seed)
        for repeat in range(args.repeats):
            order = questions.copy()
            rng.shuffle(order)
            for q in order:
                shuffled = arms.copy()
                rng.shuffle(shuffled)
                jobs.extend((q, arm, repeat) for arm in shuffled)
        queue = asyncio.Queue()
        for job in jobs:
            queue.put_nowait(job)
        with results_path.open("a", encoding="utf-8") as stream:
            async def worker():
                nonlocal stopped
                while not stopped:
                    try:
                        q, arm, repeat = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    row = await execute_case(q, arm, repeat, splits[q["id"]], jev, llm, provider_questions, settings)
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
                    print(f"{len(rows)}/{expected} q={q['id']} {arm[0]} {row['seconds']:.2f}s "
                          f"llm={row['logical_calls']['llm']} http_total={total_http}", flush=True)
                    if len(rows) >= 3 and all(all(a["decision"].get("relevante") is None for a in r["axes"]) for r in rows[-3:]):
                        stopped = True
            await asyncio.gather(*(worker() for _ in range(args.concurrency)))
        manifest["status"] = "complete" if len(rows) == expected else "incomplete_provider_or_budget_stop"
    finally:
        manifest.update(finished_at=datetime.now(timezone.utc).isoformat(), total_http_attempts_including_warmup=total_http)
        if manifest["status"] == "running":
            manifest["status"] = "interrupted"
        with results_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"type": "manifest", "stage": "end", **manifest}, ensure_ascii=False) + "\n")
        save_report(output, rows, manifest)
        await jev_client.aclose()
        await llm.close()
        await jev_http.aclose()
        await llm_http.aclose()
    print(f"REPORT={output / 'report.md'}", flush=True)
    if manifest["status"] != "complete":
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Executa chamadas reais; sem isto, somente mostra o plano.")
    parser.add_argument("--thresholds", type=float, nargs="+", default=[.3, .5, .7, .9])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-http-calls", type=int, default=1000)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summarize", type=Path, help="Recalcula somente summary.csv e report.md a partir do JSONL, sem chamadas.")
    args = parser.parse_args()
    if args.summarize:
        records = [json.loads(line) for line in (args.summarize / "results.jsonl").read_text(encoding="utf-8").splitlines()]
        manifests = [r for r in records if r.get("type") == "manifest"]
        if not manifests:
            parser.error("O JSONL precisa conter um registro de metadados (type=manifest).")
        rows = [r for r in records if r.get("type", "result") == "result"]
        save_report(args.summarize, rows, manifests[-1])
        print(args.summarize / "report.md")
        return
    if any(not 0 <= t <= 1 for t in args.thresholds) or min(args.repeats, args.concurrency, args.max_http_calls) < 1:
        parser.error("Limiares devem estar entre 0 e 1 e contadores devem ser positivos.")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit deve ser positivo.")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
