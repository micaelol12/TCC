from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer
from .experiment_config import ExperimentOverrides, ExperimentConfig, CONFIG_VERSION, PIPELINE_VERSION, config_hash

Axis = Literal["economic", "diplomatic", "state", "society"]
Level = Literal["low", "medium", "high"]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    processing_level: Level
    experiment_config: ExperimentOverrides | None = None

    @model_validator(mode="before")
    @classmethod
    def no_null_override(cls, value):
        if isinstance(value, dict) and "experiment_config" in value:
            config = value["experiment_config"]
            if not isinstance(config, dict) or any(item is None for item in config.values()):
                raise ValueError("Configuração experimental inválida.")
        return value

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


class EvidenceAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    chunk_index: int = Field(ge=0)
    kind: Literal["search", "semantic"]
    status: Literal["found", "not_selected", "not_literal", "sustenta", "contradiz", "insuficiente", "uncertain", "failed", "invalid"]
    level: Literal[-2, -1, 0, 1, 2]
    quote: str | None = None
    sentence_id: str | None = None
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    existence_probability: float | None = Field(default=None, ge=0, le=1)
    probabilities: dict[str, float] | None = None
    model: str | None = None


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
    evidence_audit: list[EvidenceAudit] = Field(default_factory=list)

    @model_serializer(mode="wrap")
    def serialize(self, handler):
        result = handler(self)
        if not self.evidence_audit:
            result.pop("evidence_audit", None)
        return result


class Chunk(BaseModel):
    index: int
    text: str


class LogicalCalls(BaseModel):
    jev: int
    llm: int


class AnalysisResponse(BaseModel):
    schema_version: str = "1"
    pipeline_version: str = PIPELINE_VERSION
    processing_level: Level
    models_used: list[str]
    axes: list[AxisResult]
    chunks: list[Chunk]
    logical_calls: LogicalCalls
    warnings: list[str]
    effective_config: ExperimentConfig | None = None
    config_version: Literal["1"] | None = None
    config_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    environment: Literal["development", "lab", "production"] | None = None
    lab_execution_id: str | None = Field(default=None, pattern=r'^[a-f0-9-]{36}$')

    @model_validator(mode="after")
    def config_metadata(self):
        metadata = (self.effective_config, self.config_version, self.config_hash, self.environment)
        if any(item is not None for item in metadata):
            if any(item is None for item in metadata) or self.config_version != CONFIG_VERSION:
                raise ValueError("Metadados de configuração incompletos.")
            if self.config_hash != config_hash(self.effective_config, self.pipeline_version):
                raise ValueError("Hash de configuração inválido.")
        return self

    @model_serializer(mode="wrap")
    def serialize(self, handler):
        result = handler(self)
        for name in ("effective_config", "config_version", "config_hash", "environment", "lab_execution_id"):
            if result.get(name) is None:
                result.pop(name, None)
        return result
