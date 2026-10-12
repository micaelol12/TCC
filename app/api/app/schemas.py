from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Axis = Literal["economic", "diplomatic", "state", "society"]
Level = Literal["low", "medium", "high"]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    processing_level: Level

    @model_validator(mode="after")
    def nonblank(self):
        if not self.text.strip():
            raise ValueError("O texto não pode estar vazio.")
        return self


class Evidence(BaseModel):
    chunk_index: int
    quote: str
    verified: Literal[True] = True


class LevelCounts(BaseModel):
    minus2: int = 0
    minus1: int = 0
    zero: int = 0
    plus1: int = 0
    plus2: int = 0


class AxisResult(BaseModel):
    axis: Axis
    pole_a: float | None
    pole_b: float | None
    status: Literal["estimated", "no_evidence", "abstained"]
    coverage: float
    valid_chunks: int
    total_chunks: int
    sufficient_evidence: bool
    level_counts: LevelCounts
    ci95: tuple[float, float] | None
    methods_used: list[Literal["jev", "llm"]]
    reason_codes: list[str]
    evidence: list[Evidence]


class Chunk(BaseModel):
    index: int
    text: str


class LogicalCalls(BaseModel):
    jev: int
    llm: int


class AnalysisResponse(BaseModel):
    schema_version: str = "1"
    pipeline_version: str = "jev-2-polos-mvp-1"
    processing_level: Level
    models_used: list[str]
    axes: list[AxisResult]
    chunks: list[Chunk]
    logical_calls: LogicalCalls
    warnings: list[str]
