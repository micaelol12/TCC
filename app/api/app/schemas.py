from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer
from .experiment_config import ExperimentOverrides, ExperimentConfig, CONFIG_VERSION, PIPELINE_VERSION, config_hash
from .polarity import EscalaOrdinal

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
    minus4: int = 0
    minus3: int = 0
    minus2: int = 0
    minus1: int = 0
    zero: int = 0
    plus1: int = 0
    plus2: int = 0
    plus3: int = 0
    plus4: int = 0


class EvidenceAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    chunk_index: int = Field(ge=0)
    kind: Literal["search", "semantic"]
    status: Literal["found", "not_selected", "not_literal", "sustenta", "contradiz", "insuficiente", "uncertain", "failed", "invalid"]
    level: int = Field(strict=True)
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
    level_counts_by_key: dict[str, int] | None = None
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
        if self.level_counts_by_key is None:
            result.pop("level_counts_by_key", None)
        return result


class Chunk(BaseModel):
    index: int
    text: str


class LogicalCalls(BaseModel):
    jev: int
    llm: int


class AnalysisResponse(BaseModel):
    schema_version: str = "3"
    escala: EscalaOrdinal | None = None
    escala_hash: str | None = None
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
        if self.schema_version not in ("1", "2", "3"):
            raise ValueError("Versão de resposta desconhecida.")
        if self.schema_version in ("1", "2"):
            if self.escala is not None or self.escala_hash is not None:
                raise ValueError("Resultados históricos usam a escala da versão original.")
            maximum = 2 if self.schema_version == "1" else 4
            if any(abs(a.level) > maximum for axis in self.axes for a in axis.evidence_audit):
                raise ValueError("Auditoria incompatível com a escala histórica.")
        if self.schema_version == "3":
            if self.escala is None or self.escala_hash != self.escala.hash:
                raise ValueError("Snapshot de escala ausente ou hash inválido.")
            if self.effective_config is not None and self.effective_config.escala.hash != self.escala.hash:
                raise ValueError("Escala difere da configuração efetiva.")
            for axis in self.axes:
                counts = axis.level_counts_by_key
                if counts is None or set(counts) != set(self.escala.por_chave) or any(type(c) is not int or c < 0 for c in counts.values()) or sum(counts.values()) != axis.valid_chunks:
                    raise ValueError("Contagens incompatíveis com a escala.")
                if any(a.level not in self.escala.por_codigo for a in axis.evidence_audit):
                    raise ValueError("Auditoria incompatível com a escala.")
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
        for name in ("effective_config", "config_version", "config_hash", "environment", "lab_execution_id", "escala", "escala_hash"):
            if result.get(name) is None:
                result.pop(name, None)
        if self.schema_version in ("1", "2") and self.effective_config is not None and "escala" not in self.effective_config.model_fields_set:
            result["effective_config"].pop("escala", None)
        if self.schema_version == "1":
            for axis in result["axes"]:
                for key in ("minus4", "minus3", "plus3", "plus4"):
                    axis["level_counts"].pop(key, None)
        return result
