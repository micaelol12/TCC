"""Provider output validation. No provider response is trusted as UI evidence."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator, create_model, field_validator
from .domain import _score_evidencia_confere
from ..polarity import PolarityLevel
from ..polarity import ESCALA_ATUAL, validar_escala


class LlmAxis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eixo: Literal["economic", "diplomatic", "state", "society"]
    relevante: bool | None
    nivel: PolarityLevel | None
    evidencia: str

    @field_validator("nivel", mode="before")
    @classmethod
    def integer_level(cls, value):
        if value is not None and type(value) is not int:
            raise ValueError("Nível deve ser um inteiro ou null.")
        return value

    @model_validator(mode="after")
    def validate_position(self):
        if self.relevante is not True and self.nivel is not None:
            raise ValueError("Nível exige relevância confirmada.")
        return self


class LlmAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eixos: list[LlmAxis]


def schema_for(axes, escala=None):
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)
    item = create_model("EixoSolicitado", __base__=LlmAxis, eixo=(Literal[tuple(axes)], ...),
        nivel=(Literal[tuple(n.codigo for n in escala.niveis)] | None, ...))
    return create_model("RespostaSolicitada", __base__=LlmAnswer, eixos=(list[item], ...))


def validate_answer(raw, requested: list[str], text: str, escala=None) -> dict:
    answer = schema_for(requested, escala).model_validate(raw.model_dump() if isinstance(raw, BaseModel) else raw)
    if sorted(x.eixo for x in answer.eixos) != sorted(requested):
        raise ValueError("Eixos ausentes, repetidos ou extras.")
    result = {}
    for item in answer.eixos:
        if item.relevante is True and not _score_evidencia_confere(text, item.evidencia):
            result[item.eixo] = {"relevante": None, "nivel": None, "method": "llm", "reason": ["evidencia_nao_verificada"], "quote": None}
        else:
            result[item.eixo] = {"relevante": item.relevante, "nivel": item.nivel, "method": "llm", "reason": [], "quote": item.evidencia if item.relevante is True and item.nivel is not None else None}
    return result
