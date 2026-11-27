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


def is_authentication_error(error):
    """Reconhece recusas de autenticação nos formatos de erro dos clientes HTTP."""
    status_code = getattr(error, "status_code", None) or getattr(getattr(error, "response", None), "status_code", None)
    return status_code in (401, 403)


def jev_decisions(response, config=None) -> tuple[dict, str | None]:
    """Converte as respostas JEV por eixo e transforma respostas inválidas em abstenções."""
    effective_config = config if config is not None else JEV_CONFIG
    answers = response["answers"] if isinstance(response, dict) else response.answers
    model = response.get("model") if isinstance(response, dict) else getattr(response, "model", None)
    decisions = {}
    for axis in AXIS_SPECS:
        try:
            original_decision = decidir_jev(axis, answers, effective_config)
            decisions[axis] = {
                "relevante": original_decision["relevante"], "nivel": original_decision["nivel"],
                "method": "jev", "methods": ["jev"],
                "reason": motivos_fallback(original_decision, effective_config), "quote": None,
                "jev_diagnostic": {name: original_decision[name] for name in JEV_DIAGNOSTIC_FIELDS},
            }
        except (ValueError, KeyError, TypeError, AttributeError):
            original_decision = None
            decisions[axis] = abstained_decision("resposta_jev_invalida", "jev")
        decisions[axis]["original"] = original_decision
    return decisions, model


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


async def ask_llm(client, model: str, text: str, axes: list[str], escala=None,
                  contexto_posicao_politica=CONTEXTO_POSICAO_POLITICA, axis_specs=AXIS_SPECS):
    """Solicita e valida a classificação estruturada, com uma nova tentativa em falhas gerais."""
    effective_scale = ESCALA_ATUAL if escala is None else escala
    rubrics = build_axis_rubrics(axes, effective_scale, contexto_posicao_politica, axis_specs)
    prompt = json.dumps({"rubricas": rubrics, "texto": text}, ensure_ascii=False)
    response_schema = schema_for(axes, effective_scale)
    # Uma nova tentativa em falhas gerais; autenticação e cancelamento encerram a chamada.
    for attempt in range(2):
        try:
            response = await client.responses.parse(
                model=model, input=prompt,
                instructions=instrucoes_escala(effective_scale, contexto_posicao_politica),
                text_format=response_schema,
            )
            if response.output_parsed is None:
                raise ValueError("Saída estruturada ausente")
            return validate_answer(response.output_parsed, axes, text, effective_scale), getattr(response, "model", model)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            if is_authentication_error(error):
                return {axis: abstained_decision("falha_autenticacao_llm", "llm") for axis in axes}, model
            if attempt == 0:
                await asyncio.sleep(0.25)
    return {axis: abstained_decision("falha_llm", "llm") for axis in axes}, model


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
        return {axis: abstained_decision(reason, "jev") for axis in AXIS_SPECS}, None


def merge_reviewed_decision(original_decision, reviewed_decision):
    """Incorpora a revisão LLM preservando os motivos e o diagnóstico inicial do JEV."""
    if "jev_diagnostic" in original_decision:
        reviewed_decision["jev_diagnostic"] = original_decision["jev_diagnostic"]
    reviewed_decision["reason"] = list(dict.fromkeys(original_decision["reason"] + reviewed_decision["reason"]))
    reviewed_decision["methods"] = ["jev", "llm"]
    return reviewed_decision


async def _classify_chunk(text: str, mode: str, jev, questions, llm, settings, config=None):
    """Coordena os modos direto, com revisão seletiva e LLM, contabilizando chamadas e modelos."""
    logical_calls = {"jev": 0, "llm": 0}
    models_used = []
    # High classifica todos os eixos diretamente; os demais modos começam no JEV.
    if mode == "high":
        logical_calls["llm"] = 1
        decisions, model = await ask_llm(llm, text=text, axes=list(AXIS_SPECS), **llm_request_options(settings, config))
        for decision in decisions.values():
            decision["methods"] = ["llm"]
        models_used.append(model)
        return decisions, logical_calls, models_used

    logical_calls["jev"] = 1
    decisions, model = await classify_with_jev(text, jev, questions, config)
    if model:
        models_used.append(model)

    # Medium revisa apenas os eixos com motivos de fallback.
    axes_to_review = [axis for axis, decision in decisions.items() if decision["reason"]] if mode == "medium" else []
    if axes_to_review:
        logical_calls["llm"] = 1
        reviewed_decisions, model = await ask_llm(llm, text=text, axes=axes_to_review, **llm_request_options(settings, config))
        models_used.append(model)
        for axis in axes_to_review:
            decisions[axis] = merge_reviewed_decision(decisions[axis], reviewed_decisions[axis])

    for decision in decisions.values():
        decision.pop("original", None)
    return decisions, logical_calls, models_used


async def classify_chunk(text: str, mode: str, jev, questions, llm, settings, config=None):
    """Executa a classificação e, quando habilitada, a auditoria observacional de evidências."""
    decisions, logical_calls, models_used = await _classify_chunk(text, mode, jev, questions, llm, settings, config)
    if config and (config.semantic_evidence_check or config.jev_evidence_search):
        evidence_rubrics = {
            axis: criar_rubrica_polaridade_ordinal(
                axis, axis_specs=config.axis_specs, escala=config.escala,
                contexto_posicao_politica=config.contexto_posicao_politica,
            ) for axis in AXIS_SPECS
        }
        decisions, evidence_calls, evidence_models = await audit_evidence(
            text, decisions, jev, evidence_rubrics, evidencia_literal_confere,
            semantic_check=config.semantic_evidence_check, quote_search=config.jev_evidence_search,
            existence_min=config.evidence_existence_min, contexto_posicao_politica=config.contexto_posicao_politica,
        )
        logical_calls["jev"] += evidence_calls
        models_used.extend(evidence_models)
    return decisions, logical_calls, models_used
