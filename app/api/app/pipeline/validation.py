"""Provider output validation. No provider response is trusted as UI evidence."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator, create_model, field_validator

from .quotes import evidencia_literal_confere
from ..polarity import PolarityLevel
from ..analysis_defaults import ESCALA_ATUAL
from ..polarity import validar_escala


class LlmAxis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eixo: Literal["economic", "diplomatic", "state", "society"]

    relevante: bool | None
    nivel: PolarityLevel | None

    evidencia: str

    @field_validator("nivel", mode="before")
    @classmethod
    def integer_level(cls, value):
        """Rejeita níveis que não sejam inteiros ou None antes da conversão do modelo."""

        if value is not None and type(value) is not int:
            raise ValueError("Nível deve ser um inteiro ou null.")

        return value

    @model_validator(mode="after")
    def validate_position(self):
        """Impede atribuir um nível quando a relevância não foi confirmada."""

        # Um nível só tem sentido quando a relevância foi confirmada.
        if self.relevante is not True and self.nivel is not None:
            raise ValueError("Nível exige relevância confirmada.")

        return self


class LlmAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eixos: list[LlmAxis]


def schema_for(axes, escala=None):
    """Restringe o contrato de saída aos eixos pedidos e aos códigos da escala utilizada."""
    # Restringe a saída aos eixos pedidos e aos códigos da escala desta execução.
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)
    levels = escala.niveis
    level_codes = tuple(level.codigo for level in levels)

    axis_schema = create_model(
        "EixoSolicitado", __base__=LlmAxis, eixo=(Literal[tuple(axes)], ...),
        nivel=(Literal[level_codes] | None, ...),
    )

    return create_model("RespostaSolicitada", __base__=LlmAnswer, eixos=(list[axis_schema], ...))


def decision_from_llm_axis(axis_answer: LlmAxis, text: str) -> dict:
    """Converte um eixo LLM e se abstém quando a evidência de uma resposta relevante não confere."""

    # Uma citação ausente torna o eixo indeterminado, em vez de estimar sem evidência.
    if axis_answer.relevante is True and not evidencia_literal_confere(text, axis_answer.evidencia):
        return {
            "relevante": None, "nivel": None, "method": "llm",
            "reason": ["evidencia_nao_verificada"], "quote": None,
        }

    has_position = axis_answer.relevante is True and axis_answer.nivel is not None

    return {
        "relevante": axis_answer.relevante, "nivel": axis_answer.nivel,
        "method": "llm", "reason": [], "quote": axis_answer.evidencia if has_position else None,
    }


def validate_requested_axes(axis_answers, requested):
    """Exige que a resposta contenha cada eixo solicitado exatamente uma vez."""
    answered_axes = sorted(axis_answer.eixo for axis_answer in axis_answers)

    if answered_axes != sorted(requested):
        raise ValueError("Eixos ausentes, repetidos ou extras.")


def validate_answer(raw, requested: list[str], text: str, escala=None) -> dict:
    """Valida o contrato, a lista de eixos e as evidências da resposta LLM."""
    response_data = raw.model_dump() if isinstance(raw, BaseModel) else raw
    response_schema = schema_for(requested, escala)
    answer = response_schema.model_validate(response_data)
    axis_answers = answer.eixos
    validate_requested_axes(axis_answers, requested)

    return {axis_answer.eixo: decision_from_llm_axis(axis_answer, text) for axis_answer in axis_answers}
