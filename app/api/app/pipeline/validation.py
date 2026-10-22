"""Provider output validation. No provider response is trusted as UI evidence."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator
from .domain import _score_evidencia_confere


class LlmAxis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eixo: Literal["economic", "diplomatic", "state", "society"]
    relevante: bool | None
    nivel: Literal[-2, -1, 0, 1, 2] | None
    evidencia: str

    @model_validator(mode="after")
    def validate_position(self):
        if self.relevante is not True and self.nivel is not None:
            raise ValueError("Nível exige relevância confirmada.")
        return self


class LlmAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eixos: list[LlmAxis]


def validate_answer(raw, requested: list[str], text: str) -> dict:
    answer = LlmAnswer.model_validate(raw.model_dump() if isinstance(raw, BaseModel) else raw)
    if sorted(x.eixo for x in answer.eixos) != sorted(requested):
        raise ValueError("Eixos ausentes, repetidos ou extras.")
    result = {}
    for item in answer.eixos:
        if item.relevante is True and not _score_evidencia_confere(text, item.evidencia):
            result[item.eixo] = {"relevante": None, "nivel": None, "method": "llm", "reason": ["evidencia_nao_verificada"], "quote": None}
        else:
            result[item.eixo] = {"relevante": item.relevante, "nivel": item.nivel, "method": "llm", "reason": [], "quote": item.evidencia if item.relevante is True and item.nivel is not None else None}
    return result
