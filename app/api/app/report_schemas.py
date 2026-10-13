"""Reports preserve a client-submitted snapshot, not a verified server result."""
import math
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .schemas import AnalysisResponse
from .pipeline.domain import _score_evidencia_confere

MAX_REPORT_BYTES = 2_000_000


class ReportAnalysis(AnalysisResponse):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal["1"] = "1"
    pipeline_version: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def consistent_snapshot(self):
        if len(self.axes) != 4 or {axis.axis for axis in self.axes} != {"economic", "diplomatic", "state", "society"}:
            raise ValueError("Os quatro eixos devem estar presentes uma única vez.")
        if not self.chunks or [chunk.index for chunk in self.chunks] != list(range(len(self.chunks))):
            raise ValueError("Trechos inválidos.")
        chunks = {chunk.index: chunk.text for chunk in self.chunks}
        for axis in self.axes:
            if not math.isfinite(axis.coverage) or not 0 <= axis.coverage <= 1:
                raise ValueError("Cobertura inválida.")
            if not 0 <= axis.valid_chunks <= axis.total_chunks == len(self.chunks):
                raise ValueError("Contagem de trechos inválida.")
            counts = axis.level_counts.model_dump().values()
            if any(count < 0 for count in counts) or sum(counts) != axis.valid_chunks:
                raise ValueError("Distribuição inválida.")
            if axis.status == "estimated":
                if any(value is None or not math.isfinite(value) or not 0 <= value <= 100 for value in (axis.pole_a, axis.pole_b)):
                    raise ValueError("Estimativa inválida.")
                if abs(axis.pole_a + axis.pole_b - 100) > 0.01:
                    raise ValueError("Polos inválidos.")
            elif axis.pole_a is not None or axis.pole_b is not None:
                raise ValueError("Estimativa ausente inválida.")
            if axis.ci95 is not None and not (all(math.isfinite(value) and 0 <= value <= 100 for value in axis.ci95) and axis.ci95[0] <= axis.ci95[1]):
                raise ValueError("Intervalo inválido.")
            if any(ev.chunk_index not in chunks or not _score_evidencia_confere(chunks[ev.chunk_index], ev.quote) for ev in axis.evidence):
                raise ValueError("Evidência inválida.")
        if self.logical_calls.jev < 0 or self.logical_calls.llm < 0:
            raise ValueError("Contagem de chamadas inválida.")
        return self


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submission_id: UUID
    text: str = Field(min_length=1)
    analysis: ReportAnalysis
    comment: str = Field(default="", max_length=2000)
    client: Literal["web", "extension"]
    storage_consent: Literal[True]
    notice_version: Literal["1"]

    @field_validator("storage_consent", mode="before")
    @classmethod
    def explicit_consent(cls, value):
        if value is not True:
            raise ValueError("Confirmação de armazenamento obrigatória.")
        return value

    @model_validator(mode="after")
    def original_text(self):
        if not self.text.strip() or "".join(chunk.text for chunk in self.analysis.chunks) != self.text:
            raise ValueError("O texto deve corresponder aos trechos da análise.")
        return self


class ReportResponse(BaseModel):
    report_id: UUID
    received_at: str
    status: Literal["pending"] = "pending"
