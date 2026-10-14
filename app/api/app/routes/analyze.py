import asyncio
from contextlib import suppress
from collections import deque
from datetime import date
from time import monotonic
from fastapi import APIRouter, HTTPException, Request
from ..schemas import AnalyzeRequest, AnalysisResponse, Chunk, LogicalCalls
from ..settings import settings
from ..pipeline.segmentation import split_text
from ..pipeline.clients import jev_client, jev_questions, llm_client, gemini_client
from ..lab_credentials import effective_keys, model_catalog
from ..pipeline.strategies import classify_chunk
from ..pipeline.aggregation import aggregate
from ..experiment_config import resolve_config, config_ranges, config_hash, CONFIG_VERSION

router = APIRouter(prefix="/api")
slots = asyncio.Semaphore(settings.concurrent_requests)
recent_requests: deque[float] = deque()
daily = {"date": date.today(), "calls": 0}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/capabilities")
def capabilities(request: Request):
    keys = effective_keys(settings, request)
    jev = bool(keys['typesafe'])
    llm = bool(keys['maritaca'] or keys['gemini'])
    result = {"max_chars": settings.max_chars, "max_tokens": settings.max_tokens, "max_chunks": settings.max_chunks,
              "modes": {"low": jev, "medium": jev and llm, "high": llm}, "timeout_seconds": settings.timeout_seconds,
              "environment": settings.app_env, "experimental": {"enabled": settings.experimental_config_enabled}}
    if settings.experimental_config_enabled:
        catalog = model_catalog(settings)
        defaults = settings.algorithm_defaults().model_dump()
        if not keys[catalog[defaults['llm_model']]]:
            defaults['llm_model'] = next((model for model, provider in catalog.items() if keys[provider]), defaults['llm_model'])
        result["experimental"].update(config_version=CONFIG_VERSION, defaults=defaults,
            ranges=config_ranges(settings.max_tokens, settings.max_chunks),
            allowed_models={"jev": list(settings.allowed_jev_models), "llm": list(catalog)}, model_providers=catalog,
            providers={provider: bool(key) for provider, key in keys.items()}, execution_storage=True)
    return result


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalyzeRequest, request: Request):
    mode = payload.processing_level
    keys = effective_keys(settings, request)
    if payload.experiment_config is not None and not settings.experimental_config_enabled:
        raise HTTPException(403, "Configuração experimental disponível somente na API Lab.")
    try:
        config = resolve_config(settings, payload.experiment_config)
    except ValueError:
        raise HTTPException(422, "Configuração incompatível com os limites ou modelos permitidos da API.") from None
    if len(payload.text) > settings.max_chars:
        raise HTTPException(413, "Texto acima do limite de caracteres.")
    provider = model_catalog(settings)[config.llm_model]
    if (mode in ("low", "medium") and not keys['typesafe']) or (mode in ("medium", "high") and not keys[provider]):
        if settings.app_env == 'lab':
            raise HTTPException(503, "Cadastre suas chaves na aba API keys para usar este modo e modelo.")
        raise HTTPException(503, "Modo indisponível: configure os provedores necessários.")
    try:
        chunks, _ = split_text(payload.text, max_tokens=settings.max_tokens, chunk_tokens=config.chunk_tokens)
    except ValueError:
        raise HTTPException(413, "Texto acima do limite de tokens.") from None
    if len(chunks) > settings.max_chunks:
        raise HTTPException(413, "Texto acima do limite de trechos; aumente os tokens por trecho ou reduza o texto.")
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
    jev = jev_client(keys['typesafe'], config.jev_model) if mode != "high" else None
    questions = jev_questions() if jev else None
    llm = (gemini_client if provider == 'gemini' else llm_client)(keys[provider], settings.timeout_seconds) if mode != "low" else None
    semaphore = asyncio.Semaphore(settings.concurrent_chunks)

    async def run_one(text: str):
        async with semaphore:
            if await request.is_disconnected():
                raise asyncio.CancelledError()
            return await classify_chunk(text, mode, jev, questions, llm, settings, config)

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
        except asyncio.CancelledError:
            raise HTTPException(499, 'Execução cancelada.') from None
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
    axes = aggregate([item[0] for item in result], len(chunks), config)
    calls = LogicalCalls(jev=sum(x[1]["jev"] for x in result), llm=sum(x[1]["llm"] for x in result))
    models = list(dict.fromkeys(model for x in result for model in x[2] if model))
    warnings = list(dict.fromkeys(reason for axis in axes for reason in axis.reason_codes if reason in {"falha_jev", "falha_llm", "falha_autenticacao_jev", "falha_autenticacao_llm", "resposta_jev_invalida", "evidencia_nao_verificada"}))
    return AnalysisResponse(processing_level=mode, models_used=models, axes=axes,
                            chunks=[Chunk(index=i, text=text) for i, text in enumerate(chunks)],
                            logical_calls=calls, warnings=warnings, effective_config=config,
                            config_version=CONFIG_VERSION, config_hash=config_hash(config), environment=settings.app_env)
