import asyncio
from contextlib import suppress
from collections import deque
from datetime import date
from time import monotonic
from fastapi import APIRouter, HTTPException, Request
from ..schemas import AnalyzeRequest, AnalysisResponse, Chunk, LogicalCalls
from ..settings import settings
from ..pipeline.segmentation import split_text
from ..pipeline.clients import jev_client, jev_questions, llm_client
from ..pipeline.strategies import classify_chunk
from ..pipeline.aggregation import aggregate

router = APIRouter(prefix="/api")
slots = asyncio.Semaphore(settings.concurrent_requests)
recent_requests: deque[float] = deque()
daily = {"date": date.today(), "calls": 0}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/capabilities")
def capabilities():
    jev = bool(settings.typesafe_key)
    llm = bool(settings.maritaca_key)
    return {"max_chars": settings.max_chars, "max_tokens": settings.max_tokens, "max_chunks": settings.max_chunks,
            "modes": {"low": jev, "medium": jev and llm, "high": llm}, "timeout_seconds": settings.timeout_seconds}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalyzeRequest, request: Request):
    mode = payload.processing_level
    if len(payload.text) > settings.max_chars:
        raise HTTPException(413, "Texto acima do limite de caracteres.")
    if (mode in ("low", "medium") and not settings.typesafe_key) or (mode in ("medium", "high") and not settings.maritaca_key):
        raise HTTPException(503, "Modo indisponível: configure os provedores necessários.")
    try:
        chunks, _ = split_text(payload.text, max_tokens=settings.max_tokens)
    except ValueError:
        raise HTTPException(413, "Texto acima do limite de tokens.") from None
    if len(chunks) > settings.max_chunks:
        raise HTTPException(413, "Texto acima do limite de trechos.")
    now = monotonic()
    while recent_requests and recent_requests[0] < now - 3600:
        recent_requests.popleft()
    if len(recent_requests) >= settings.hourly_requests:
        raise HTTPException(429, "Limite temporário de análises atingido.")
    if daily["date"] != date.today():
        daily.update(date=date.today(), calls=0)
    maximum_calls = len(chunks) * (2 if mode == "medium" else 1)
    if daily["calls"] + maximum_calls > settings.daily_calls:
        raise HTTPException(429, "Orçamento diário de análises atingido.")
    recent_requests.append(now)
    daily["calls"] += maximum_calls
    jev = jev_client(settings.typesafe_key, settings.jev_model) if mode != "high" else None
    questions = jev_questions() if jev else None
    llm = llm_client(settings.maritaca_key, settings.timeout_seconds) if mode != "low" else None
    semaphore = asyncio.Semaphore(settings.concurrent_chunks)

    async def run_one(text: str):
        async with semaphore:
            if await request.is_disconnected():
                raise asyncio.CancelledError()
            return await classify_chunk(text, mode, jev, questions, llm, settings)

    async def stop_on_disconnect(work):
        while not work.done():
            if await request.is_disconnected():
                work.cancel()
                return
            await asyncio.sleep(0.25)

    async with slots:
        work = asyncio.gather(*(run_one(chunk) for chunk in chunks))
        watcher = asyncio.create_task(stop_on_disconnect(work))
        try:
            async with asyncio.timeout(settings.timeout_seconds):
                result = await work
        except TimeoutError:
            raise HTTPException(504, "O prazo da análise foi excedido.") from None
        finally:
            watcher.cancel()
            with suppress(asyncio.CancelledError):
                await watcher
            if llm:
                await llm.close()
            if jev:
                await jev.aclose()
    axes = aggregate([item[0] for item in result], len(chunks))
    calls = LogicalCalls(jev=sum(x[1]["jev"] for x in result), llm=sum(x[1]["llm"] for x in result))
    models = list(dict.fromkeys(model for x in result for model in x[2] if model))
    warnings = list(dict.fromkeys(reason for axis in axes for reason in axis.reason_codes if reason in {"falha_jev", "falha_llm", "resposta_jev_invalida", "evidencia_nao_verificada"}))
    return AnalysisResponse(processing_level=mode, models_used=models, axes=axes,
                            chunks=[Chunk(index=i, text=text) for i, text in enumerate(chunks)],
                            logical_calls=calls, warnings=warnings)
