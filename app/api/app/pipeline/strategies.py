"""Estratégias de classificação direta, revisão seletiva e auditoria de evidências."""
import asyncio
import json

from ..analysis_defaults import CONTEXTO_POSICAO_POLITICA, ESCALA_ATUAL
from ..prompting import instrucoes_escala
from .domain import decidir_jev, motivos_fallback
from .evidence import audit_evidence
from .quotes import evidencia_literal_confere
from .rubrics import AXIS_SPECS, criar_questoes_eixo, criar_rubrica_polaridade_ordinal
from .validation import schema_for, validate_answer

# Valores padrão para chamadas sem configuração explícita.
JEV_CONFIG = {
    "tipo_relevancia": "choice", "primitiva_polaridade": "score",
    "margem_relevancia_minima": 0.60, "confianca_nivel_minima": 0.50,
    "margem_direcao_minima": 0.20,
}
INSTRUCTIONS = instrucoes_escala(ESCALA_ATUAL)
JEV_DIAGNOSTIC_FIELDS = (
    "regra_decisao", "relevante", "nivel_jev_bruto", "nivel", "grupo_mais_provavel",
    "probabilities_nivel", "probabilities_abc", "margem_grupo",
    "probabilidade_nivel_condicional", "confianca_nivel", "desempate_intensidade",
)


def abstained_decision(reason: str, method: str | None = None) -> dict:
    """Representa falha ou incerteza sem atribuir uma posição central ao eixo."""
    # Falha ou incerteza não deve virar uma posição central na escala.
    return {
        "relevante": None, "nivel": None, "method": method,
        "methods": [method] if method else [], "reason": [reason], "quote": None,
    }


def abstained_decisions(axes, reason, method):
    """Cria uma abstenção independente para cada eixo afetado por uma falha."""
    return {axis: abstained_decision(reason, method) for axis in axes}


def is_authentication_error(error):
    """Reconhece recusas de autenticação nos formatos de erro dos clientes HTTP."""
    status_code = getattr(error, "status_code", None) or getattr(getattr(error, "response", None), "status_code", None)

    return status_code in (401, 403)


def jev_decisions(response, config=None) -> tuple[dict, str | None]:
    """Converte as respostas JEV por eixo e transforma respostas inválidas em abstenções."""
    effective_config = config if config is not None else JEV_CONFIG
    answers = response["answers"] if isinstance(response, dict) else response.answers
    model = response.get("model") if isinstance(response, dict) else getattr(response, "model", None)
    axes = list(AXIS_SPECS)
    decisions = {axis: jev_axis_decision(axis, answers, effective_config) for axis in axes}

    return decisions, model


def jev_axis_decision(axis, answers, config):
    """Converte um eixo JEV e guarda o diagnóstico; dados inválidos geram abstenção."""

    try:
        original_decision = decidir_jev(axis, answers, config)
        decision = {
            "relevante": original_decision["relevante"], "nivel": original_decision["nivel"],
            "method": "jev", "methods": ["jev"],
            "reason": motivos_fallback(original_decision, config), "quote": None,
            "jev_diagnostic": {name: original_decision[name] for name in JEV_DIAGNOSTIC_FIELDS},
        }
    except (ValueError, KeyError, TypeError, AttributeError):
        original_decision = None
        decision = abstained_decision("resposta_jev_invalida", "jev")

    decision["original"] = original_decision

    return decision


def build_axis_rubrics(axes, escala, contexto_posicao_politica, axis_specs):
    """Monta rubricas de relevância e polaridade somente para os eixos solicitados."""
    return {
        axis: {
            "relevancia": criar_questoes_eixo(
                axis, axis_specs=axis_specs, contexto_posicao_politica=contexto_posicao_politica,
            ),
            "polaridade": criar_rubrica_polaridade_ordinal(
                axis, axis_specs=axis_specs, escala=escala, contexto_posicao_politica=contexto_posicao_politica,
            ),
        }
        for axis in axes
    }


def build_llm_request(model, text, axes, escala, contexto_posicao_politica, axis_specs):
    """Prepara o prompt, as instruções e o contrato de saída antes das tentativas."""
    rubrics = build_axis_rubrics(axes, escala, contexto_posicao_politica, axis_specs)
    prompt = json.dumps({"rubricas": rubrics, "texto": text}, ensure_ascii=False)
    response_schema = schema_for(axes, escala)
    instructions = instrucoes_escala(escala, contexto_posicao_politica)

    return {
        "model": model, "input": prompt, "instructions": instructions,
        "text_format": response_schema,
    }


def parse_llm_response(response, axes, text, escala, requested_model):
    """Exige uma saída estruturada e valida as decisões e suas evidências literais."""

    if response.output_parsed is None:
        raise ValueError("Saída estruturada ausente")

    decisions = validate_answer(response.output_parsed, axes, text, escala)
    model = getattr(response, "model", requested_model)

    return decisions, model


async def ask_llm(client, model: str, text: str, axes: list[str], escala=None,
                  contexto_posicao_politica=CONTEXTO_POSICAO_POLITICA, axis_specs=AXIS_SPECS):
    """Executa a chamada LLM com uma nova tentativa em falhas gerais."""
    effective_scale = ESCALA_ATUAL if escala is None else escala
    request_options = build_llm_request(model, text, axes, effective_scale, contexto_posicao_politica, axis_specs)
    attempts = range(2)

    # Uma nova tentativa em falhas gerais; autenticação e cancelamento encerram a chamada.
    for attempt in attempts:
        try:
            response = await client.responses.parse(**request_options)

            return parse_llm_response(response, axes, text, effective_scale, model)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            if is_authentication_error(error):
                return abstained_decisions(axes, "falha_autenticacao_llm", "llm"), model

            if attempt == 0:
                await asyncio.sleep(0.25)

    return abstained_decisions(axes, "falha_llm", "llm"), model


def llm_request_options(settings, config):
    """Seleciona modelo, escala e contexto efetivos para a chamada ao LLM."""
    return {
        "model": config.llm_model if config else settings.llm_model,
        "escala": config.escala if config else None,
        "contexto_posicao_politica": config.contexto_posicao_politica if config else CONTEXTO_POSICAO_POLITICA,
        "axis_specs": config.axis_specs if config else AXIS_SPECS,
    }


async def classify_with_jev(text, jev, questions, config):
    """Classifica o trecho pelo JEV e converte falhas do provedor em decisões de abstenção."""

    try:
        response = await jev.system_one(state=text, questions=questions)

        return jev_decisions(response, config.jev_config() if config else None)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        reason = "falha_autenticacao_jev" if is_authentication_error(error) else "falha_jev"
        axes = list(AXIS_SPECS)

        return abstained_decisions(axes, reason, "jev"), None


def merge_reviewed_decision(original_decision, reviewed_decision):
    """Incorpora a revisão LLM preservando os motivos e o diagnóstico inicial do JEV."""

    if "jev_diagnostic" in original_decision:
        reviewed_decision["jev_diagnostic"] = original_decision["jev_diagnostic"]

    reviewed_decision["reason"] = list(dict.fromkeys(original_decision["reason"] + reviewed_decision["reason"]))
    reviewed_decision["methods"] = ["jev", "llm"]

    return reviewed_decision


async def classify_with_llm(text, axes, llm, settings, config):
    """Classifica os eixos solicitados pelo LLM e registra o método em cada decisão."""
    request_options = llm_request_options(settings, config)
    decisions, model = await ask_llm(llm, text=text, axes=axes, **request_options)
    axis_decisions = list(decisions.values())

    for decision in axis_decisions:
        decision["methods"] = ["llm"]

    return decisions, model


def axes_requiring_review(decisions):
    """Seleciona somente eixos que tenham motivos de revisão ou falha do JEV."""
    axis_decisions = list(decisions.items())

    return [axis for axis, decision in axis_decisions if decision["reason"]]


async def review_jev_decisions(text, decisions, axes, llm, settings, config):
    """Substitui os eixos revisados, preservando os motivos e o diagnóstico JEV."""
    reviewed_decisions, model = await classify_with_llm(text, axes, llm, settings, config)

    for axis in axes:
        decisions[axis] = merge_reviewed_decision(decisions[axis], reviewed_decisions[axis])

    return model


def remove_internal_decisions(decisions):
    """Remove os dados temporários usados na decisão, mantendo o diagnóstico público."""
    axis_decisions = list(decisions.values())

    for decision in axis_decisions:
        decision.pop("original", None)


async def classify_jev_chunk(text, mode, jev, questions, llm, settings, config):
    """Executa o JEV e, no modo medium, revisa apenas os eixos que precisam."""
    logical_calls = {"jev": 1, "llm": 0}
    decisions, model = await classify_with_jev(text, jev, questions, config)
    models_used = [model] if model else []

    axes_to_review = axes_requiring_review(decisions) if mode == "medium" else []

    if axes_to_review:
        model = await review_jev_decisions(text, decisions, axes_to_review, llm, settings, config)
        logical_calls["llm"] = 1
        models_used.append(model)

    remove_internal_decisions(decisions)

    return decisions, logical_calls, models_used


async def _classify_chunk(text: str, mode: str, jev, questions, llm, settings, config=None):
    """Escolhe entre classificação direta pelo LLM e classificação inicial pelo JEV."""

    if mode == "high":
        axes = list(AXIS_SPECS)
        decisions, model = await classify_with_llm(text, axes, llm, settings, config)

        return decisions, {"jev": 0, "llm": 1}, [model]

    return await classify_jev_chunk(text, mode, jev, questions, llm, settings, config)


def build_evidence_rubrics(config):
    """Prepara as rubricas de polaridade utilizadas na auditoria de evidências."""
    axes = list(AXIS_SPECS)

    return {
        axis: criar_rubrica_polaridade_ordinal(
            axis, axis_specs=config.axis_specs, escala=config.escala,
            contexto_posicao_politica=config.contexto_posicao_politica,
        ) for axis in axes
    }


async def audit_chunk_evidence(text, decisions, jev, config):
    """Executa as verificações de evidência habilitadas na configuração do trecho."""
    evidence_rubrics = build_evidence_rubrics(config)

    return await audit_evidence(
        text, decisions, jev, evidence_rubrics, evidencia_literal_confere,
        semantic_check=config.semantic_evidence_check, quote_search=config.jev_evidence_search,
        existence_min=config.evidence_existence_min, contexto_posicao_politica=config.contexto_posicao_politica,
    )


async def classify_chunk(text: str, mode: str, jev, questions, llm, settings, config=None):
    """Executa a classificação e, quando habilitada, a auditoria observacional de evidências."""
    decisions, logical_calls, models_used = await _classify_chunk(text, mode, jev, questions, llm, settings, config)

    if config and (config.semantic_evidence_check or config.jev_evidence_search):
        decisions, evidence_calls, evidence_models = await audit_chunk_evidence(text, decisions, jev, config)
        logical_calls["jev"] += evidence_calls
        models_used.extend(evidence_models)

    return decisions, logical_calls, models_used
