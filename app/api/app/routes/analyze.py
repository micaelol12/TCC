import asyncio
from contextlib import suppress

from fastapi import APIRouter, HTTPException, Request

from ..schemas import AnalyzeRequest, AnalysisResponse, Chunk, Level, LogicalCalls
from ..settings import settings
from ..pipeline.segmentation import split_text
from ..pipeline.clients import jev_client, jev_questions, llm_client, gemini_client
from ..lab_credentials import effective_keys, model_catalog
from ..pipeline.strategies import classify_chunk
from ..pipeline.aggregation import aggregate
from ..experiment_config import ExperimentConfig, resolve_config, config_hash, CONFIG_VERSION
from ..capabilities import build_capabilities

router = APIRouter(prefix="/api")

# Limita as análises simultâneas neste processo.
slots = asyncio.Semaphore(settings.concurrent_requests)

ANALYSIS_WARNING_CODES = {
    "falha_jev", "falha_llm", "falha_autenticacao_jev", "falha_autenticacao_llm",
    "resposta_jev_invalida", "evidencia_nao_verificada",
}


@router.get("/health")
def health():
    """Sinaliza que a API está respondendo sem consultar serviços externos."""
    return {"status": "ok"}


@router.get("/capabilities")
def capabilities(request: Request):
    """Retorna os modos e limites disponíveis para as credenciais efetivas da requisição."""
    return build_capabilities(settings, effective_keys(settings, request))


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalyzeRequest, request: Request):
    """Valida a entrada e coordena a análise até a agregação final."""
    provider_keys = effective_keys(settings, request)
    config = resolve_analysis_config(payload)
    llm_provider = model_catalog(settings)[config.llm_model]
    validate_provider_keys(payload.processing_level, config, provider_keys, llm_provider)
    chunks = split_analysis_text(payload.text, config)
    chunk_results = await classify_analysis_chunks(
        chunks, payload.processing_level, config, provider_keys, llm_provider, request
    )

    return build_analysis_response(chunks, chunk_results, payload.processing_level, config)


def resolve_analysis_config(payload: AnalyzeRequest) -> ExperimentConfig:
    """Valida o uso de parâmetros Lab, a configuração efetiva e o tamanho em caracteres."""

    if payload.experiment_config is not None and not settings.experimental_config_enabled:
        raise HTTPException(403, "Configuração experimental disponível somente na API Lab.")

    try:
        config = resolve_config(settings, payload.experiment_config)
    except ValueError:
        raise HTTPException(422, "Configuração incompatível com os limites ou modelos permitidos da API.") from None

    if len(payload.text) > settings.max_chars:
        raise HTTPException(413, "Texto acima do limite de caracteres.")

    return config


def requires_jev(mode: Level, config: ExperimentConfig) -> bool:
    """Indica se o modo ou a checagem semântica requer um cliente JEV."""
    return mode != "high" or config.semantic_evidence_check


def validate_provider_keys(
    mode: Level, config: ExperimentConfig, provider_keys: dict[str, str], llm_provider: str
) -> None:
    """Rejeita modos cujos provedores necessários não tenham chave disponível."""
    missing_jev = requires_jev(mode, config) and not provider_keys['typesafe']
    missing_llm = mode in ("medium", "high") and not provider_keys[llm_provider]

    if missing_jev or missing_llm:
        if settings.app_env == 'lab':
            raise HTTPException(503, "Cadastre suas chaves na aba API keys para usar este modo e modelo.")

        raise HTTPException(503, "Modo indisponível: configure os provedores necessários.")


def split_analysis_text(text: str, config: ExperimentConfig) -> list[str]:
    """Segmenta o texto e converte excesso de tokens ou trechos em erro HTTP 413."""

    try:
        chunks, _ = split_text(text, max_tokens=settings.max_tokens,
                               chunk_tokens=config.chunk_tokens, strategy=config.chunk_strategy)
    except ValueError:
        raise HTTPException(413, "Texto acima do limite de tokens.") from None

    if len(chunks) > settings.max_chunks:
        raise HTTPException(413, "Texto acima do limite de trechos; aumente os tokens por trecho ou reduza o texto.")

    return chunks


async def classify_analysis_chunks(
    chunks: list[str], mode: Level, config: ExperimentConfig,
    provider_keys: dict[str, str], llm_provider: str, request: Request,
):
    """Executa trechos com concorrência limitada e encerra clientes ao finalizar a análise."""
    jev = jev_client(provider_keys['typesafe'], config.jev_model) if requires_jev(mode, config) else None
    questions = (
        jev_questions(config.escala, config.primitiva_polaridade, config.contexto_posicao_politica, config.axis_specs)
        if mode != "high" else None
    )
    create_llm_client = gemini_client if llm_provider == 'gemini' else llm_client
    llm = create_llm_client(provider_keys[llm_provider], settings.timeout_seconds) if mode != "low" else None

    # Limita trechos simultâneos dentro desta análise; slots limita análises.
    chunk_slots = asyncio.Semaphore(settings.concurrent_chunks)

    async def classify_with_chunk_limit(text: str):
        """Adquire uma vaga de trecho e verifica desconexão antes de chamar os classificadores."""

        async with chunk_slots:
            if await request.is_disconnected():
                raise asyncio.CancelledError()

            return await classify_chunk(text, mode, jev, questions, llm, settings, config)

    async def cancel_on_disconnect(classification_task):
        """Observa a conexão e cancela o conjunto de tarefas quando o cliente sai."""

        # Interrompe o processamento quando o cliente encerra a requisição.
        while not classification_task.done():
            if await request.is_disconnected():
                classification_task.cancel()

                return

            await asyncio.sleep(0.25)

    async with slots:
        classification_task = asyncio.gather(*(classify_with_chunk_limit(chunk) for chunk in chunks))

        disconnect_watcher = asyncio.create_task(cancel_on_disconnect(classification_task))

        try:
            async with asyncio.timeout(settings.timeout_seconds):
                chunk_results = await classification_task
        except asyncio.CancelledError:
            raise HTTPException(499, 'Execução cancelada.') from None
        except TimeoutError:
            raise HTTPException(504, "O prazo da análise foi excedido.") from None
        finally:
            disconnect_watcher.cancel()

            with suppress(asyncio.CancelledError):
                await disconnect_watcher

            if llm:
                await llm.close()

            if jev:
                await jev.aclose()

    return chunk_results


def build_analysis_response(
    chunks: list[str], chunk_results: list, mode: Level, config: ExperimentConfig
) -> AnalysisResponse:
    """Agrega decisões e inclui chamadas, modelos, avisos e o snapshot da configuração."""
    axes = aggregate([decisions for decisions, _, _ in chunk_results], len(chunks), config)

    logical_calls = LogicalCalls(
        jev=sum(calls["jev"] for _, calls, _ in chunk_results),
        llm=sum(calls["llm"] for _, calls, _ in chunk_results),
    )
    models_used = list(dict.fromkeys(
        model for _, _, chunk_models in chunk_results for model in chunk_models if model
    ))
    warnings = list(dict.fromkeys(
        reason for axis in axes for reason in axis.reason_codes if reason in ANALYSIS_WARNING_CODES
    ))

    # O snapshot e os hashes identificam a configuração usada nesta execução.
    return AnalysisResponse(
        processing_level=mode, models_used=models_used, axes=axes,
        escala=config.escala, escala_hash=config.escala.hash,
        chunks=[Chunk(index=index, text=text) for index, text in enumerate(chunks)],
        logical_calls=logical_calls, warnings=warnings, effective_config=config,
        config_version=CONFIG_VERSION, config_hash=config_hash(config), environment=settings.app_env,
    )
