import asyncio
import json
from copy import deepcopy
from .domain import decidir_jev, motivos_fallback, criar_questoes_eixo, criar_rubrica_polaridade_ordinal
from .rubrics import AXIS_SPECS
from .validation import validate_answer
from .clients import jev_client, jev_questions, llm_client
from .evidence import audit_evidence
from .domain import _score_evidencia_confere
from ..polarity import ESCALA_ATUAL, instrucoes_escala
from .validation import schema_for

JEV_CONFIG = {
    "tipo_relevancia": "choice", "primitiva_polaridade": "score",
    "margem_relevancia_minima": 0.60, "confianca_nivel_minima": 0.50,
    "margem_direcao_minima": 0.20,
}

INSTRUCTIONS = instrucoes_escala(ESCALA_ATUAL)


def empty(reason: str, method: str | None = None) -> dict:
    return {"relevante": None, "nivel": None, "method": method, "methods": [method] if method else [], "reason": [reason], "quote": None}


def authentication_failure(error):
    status = getattr(error, "status_code", None) or getattr(getattr(error, "response", None), "status_code", None)
    return status in (401, 403)


def jev_decisions(response, config=None) -> tuple[dict, str | None]:
    config = config if config is not None else JEV_CONFIG
    answers = response["answers"] if isinstance(response, dict) else response.answers
    model = response.get("model") if isinstance(response, dict) else getattr(response, "model", None)
    decisions = {}
    for axis in AXIS_SPECS:
        try:
            original = decidir_jev(axis, answers, config)
            reasons = motivos_fallback(original, config)
            decisions[axis] = {
                "relevante": original["relevante"], "nivel": original["nivel"],
                "method": "jev", "methods": ["jev"], "reason": reasons, "quote": None,
                "jev_diagnostic": {name: original[name] for name in (
                    "regra_decisao", "relevante", "nivel_jev_bruto", "nivel", "grupo_mais_provavel",
                    "probabilities_nivel", "probabilities_abc", "margem_grupo",
                    "probabilidade_nivel_condicional", "confianca_nivel")},
            }
        except (ValueError, KeyError, TypeError, AttributeError):
            original = None
            decisions[axis] = empty("resposta_jev_invalida", "jev")
        decisions[axis]["original"] = original
    return decisions, model


async def ask_llm(client, model: str, text: str, axes: list[str], escala=None):
    escala = ESCALA_ATUAL if escala is None else escala
    rubrics = {axis: {"relevancia": criar_questoes_eixo(axis), "polaridade": criar_rubrica_polaridade_ordinal(axis, escala=escala)} for axis in axes}
    prompt = json.dumps({"rubricas": rubrics, "texto": text}, ensure_ascii=False)
    schema = schema_for(axes, escala)
    for attempt in range(2):
        try:
            response = await client.responses.parse(model=model, input=prompt, instructions=instrucoes_escala(escala), text_format=schema)
            if response.output_parsed is None:
                raise ValueError("Saída estruturada ausente")
            return validate_answer(response.output_parsed, axes, text, escala), getattr(response, "model", model)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            if authentication_failure(error):
                return {axis: empty("falha_autenticacao_llm", "llm") for axis in axes}, model
            if attempt == 0:
                await asyncio.sleep(0.25)
    return {axis: empty("falha_llm", "llm") for axis in axes}, model


async def classify_chunk(text: str, mode: str, jev, questions, llm, settings, config=None):
    decisions, calls, models = await _classify_chunk(text, mode, jev, questions, llm, settings, config)
    if config and (config.semantic_evidence_check or config.jev_evidence_search):
        decisions, extra_calls, extra_models = await audit_evidence(
            text, decisions, jev, {axis: criar_rubrica_polaridade_ordinal(axis, escala=config.escala) for axis in AXIS_SPECS},
            _score_evidencia_confere, semantic_check=config.semantic_evidence_check,
            quote_search=config.jev_evidence_search, existence_min=config.evidence_existence_min)
        calls["jev"] += extra_calls
        models.extend(extra_models)
    return decisions, calls, models


async def _classify_chunk(text: str, mode: str, jev, questions, llm, settings, config=None):
    calls = {"jev": 0, "llm": 0}
    models = []
    if mode == "high":
        calls["llm"] = 1
        result, model = await ask_llm(llm, config.llm_model if config else settings.llm_model, text, list(AXIS_SPECS), config.escala if config else None)
        for decision in result.values():
            decision["methods"] = ["llm"]
        models.append(model)
        return result, calls, models
    try:
        calls["jev"] = 1
        response = await jev.system_one(state=text, questions=questions)
        decisions, model = jev_decisions(response, config.jev_config() if config else None)
        if model:
            models.append(model)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        reason = "falha_autenticacao_jev" if authentication_failure(error) else "falha_jev"
        decisions = {axis: empty(reason, "jev") for axis in AXIS_SPECS}
    if mode == "medium":
        requested = [axis for axis, d in decisions.items() if d["reason"]]
        if requested:
            calls["llm"] = 1
            reviewed, model = await ask_llm(llm, config.llm_model if config else settings.llm_model, text, requested, config.escala if config else None)
            models.append(model)
            for axis in requested:
                if "jev_diagnostic" in decisions[axis]:
                    reviewed[axis]["jev_diagnostic"] = decisions[axis]["jev_diagnostic"]
                reviewed[axis]["reason"] = list(dict.fromkeys(decisions[axis]["reason"] + reviewed[axis]["reason"]))
                reviewed[axis]["methods"] = ["jev", "llm"]
                decisions[axis] = reviewed[axis]
    for decision in decisions.values():
        decision.pop("original", None)
    return decisions, calls, models
