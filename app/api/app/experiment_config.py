"""Public algorithm configuration; provider secrets are never part of this contract."""
import hashlib
import json
from typing import Annotated, Literal
from types import MappingProxyType
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_serializer, model_validator
from .analysis_defaults import default_value
from .polarity import DefinicaoEixo, EIXOS_ESCALA
from .analysis_defaults import CONTEXTO_POSICAO_POLITICA
from .polarity import EscalaOrdinal, validar_escala

CONFIG_VERSION = "1"
PIPELINE_VERSION = "jev-escalas-ordinal-13"
Probability = Annotated[float, Field(strict=True, ge=0, le=1, allow_inf_nan=False)]
ChunkSize = Annotated[int, Field(strict=True, ge=100, le=2000)]
Positive = Annotated[int, Field(strict=True, ge=1)]
Samples = Annotated[int, Field(strict=True, ge=200, le=10000)]
Seed = Annotated[int, Field(strict=True, ge=0, le=2**32 - 1)]
ModelName = Annotated[str, Field(strict=True, min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:/-]+$")]
PoliticalContext = Annotated[str, Field(strict=True, min_length=1, max_length=20000, pattern=r"\S")]


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    escala: EscalaOrdinal = Field(default_factory=lambda: validar_escala(default_value('escala')))
    contexto_posicao_politica: PoliticalContext = Field(default_factory=lambda: default_value('contexto_posicao_politica'), validate_default=True)
    axis_specs: dict[str, DefinicaoEixo] = Field(default_factory=lambda: default_value('axis_specs'), validate_default=True)
    primitiva_polaridade: Literal["score", "choice"] = "score"
    regra_decisao: Literal["nivel", "polo_primeiro"] = "nivel"
    chunk_tokens: ChunkSize = 600
    chunk_strategy: Literal["sentencas", "tokens"] = "tokens"
    relevance_margin_min: Probability = 0.60
    level_confidence_min: Probability = 0.50
    direction_margin_min: Probability = 0.20
    min_valid_chunks: Positive = 16
    bootstrap_samples: Samples = 2000
    bootstrap_seed: Seed = 42
    jev_model: ModelName = "jev-1.13.0"
    llm_model: ModelName = "sabia-4"
    semantic_evidence_check: StrictBool = False
    jev_evidence_search: StrictBool = False
    evidence_existence_min: Probability = 0.70

    @model_validator(mode='after')
    def complete_axes(self):
        if set(self.axis_specs) != set(EIXOS_ESCALA):
            raise ValueError('As definições devem cobrir exatamente os quatro eixos.')
        object.__setattr__(self, 'axis_specs', MappingProxyType(dict(self.axis_specs)))
        return self

    @field_serializer('axis_specs')
    def serialize_axes(self, value):
        return {axis: spec.model_dump(mode='json') for axis, spec in value.items()}

    def jev_config(self):
        return {"escala": self.escala.model_dump(mode="json"), "tipo_relevancia": "choice", "primitiva_polaridade": self.primitiva_polaridade,
                "regra_decisao": self.regra_decisao,
                "margem_relevancia_minima": self.relevance_margin_min,
                "confianca_nivel_minima": self.level_confidence_min,
                "margem_direcao_minima": self.direction_margin_min}


class ExperimentOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    escala: EscalaOrdinal | None = None
    contexto_posicao_politica: PoliticalContext | None = None
    axis_specs: dict[str, DefinicaoEixo] | None = None
    primitiva_polaridade: Literal["score", "choice"] | None = None
    regra_decisao: Literal["nivel", "polo_primeiro"] | None = None
    chunk_tokens: ChunkSize | None = None
    chunk_strategy: Literal["sentencas", "tokens"] | None = None
    relevance_margin_min: Probability | None = None
    level_confidence_min: Probability | None = None
    direction_margin_min: Probability | None = None
    min_valid_chunks: Positive | None = None
    bootstrap_samples: Samples | None = None
    bootstrap_seed: Seed | None = None
    jev_model: ModelName | None = None
    llm_model: ModelName | None = None
    semantic_evidence_check: StrictBool | None = None
    jev_evidence_search: StrictBool | None = None
    evidence_existence_min: Probability | None = None


def config_hash(config: ExperimentConfig, pipeline_version: str = PIPELINE_VERSION) -> str:
    effective = config.model_dump()
    if pipeline_version != PIPELINE_VERSION:
        effective.pop('axis_specs', None)
    if pipeline_version not in ('jev-escalas-ordinal-12', PIPELINE_VERSION):
        if config.contexto_posicao_politica != CONTEXTO_POSICAO_POLITICA:
            raise ValueError("Versão histórica da API não suporta contexto configurável.")
        effective.pop("contexto_posicao_politica", None)
    if pipeline_version not in ("jev-escalas-ordinal-7", "jev-escalas-ordinal-8", "jev-escalas-ordinal-9", "jev-escalas-ordinal-10", "jev-escalas-ordinal-11", 'jev-escalas-ordinal-12', PIPELINE_VERSION):
        if config.chunk_strategy != "tokens":
            raise ValueError("Versão histórica da API não suporta segmentação por sentenças.")
        effective.pop("chunk_strategy", None)
    if pipeline_version not in ("jev-escalas-ordinal-6", "jev-escalas-ordinal-7", "jev-escalas-ordinal-8", "jev-escalas-ordinal-9", "jev-escalas-ordinal-10", "jev-escalas-ordinal-11", 'jev-escalas-ordinal-12', PIPELINE_VERSION):
        if config.regra_decisao != "nivel":
            raise ValueError("Versão histórica da API não suporta polo_primeiro.")
        effective.pop("regra_decisao", None)
    if pipeline_version not in ("jev-escalas-ordinal-5", "jev-escalas-ordinal-6", "jev-escalas-ordinal-7", "jev-escalas-ordinal-8", "jev-escalas-ordinal-9", "jev-escalas-ordinal-10", "jev-escalas-ordinal-11", 'jev-escalas-ordinal-12', PIPELINE_VERSION):
        if config.primitiva_polaridade != "score":
            raise ValueError("Versão histórica da API não suporta polaridade Choice.")
        effective.pop("primitiva_polaridade", None)
    if pipeline_version not in ("jev-escalas-ordinal-4", "jev-escalas-ordinal-5", "jev-escalas-ordinal-6", "jev-escalas-ordinal-7", "jev-escalas-ordinal-8", "jev-escalas-ordinal-9", "jev-escalas-ordinal-10", "jev-escalas-ordinal-11", 'jev-escalas-ordinal-12', PIPELINE_VERSION):
        effective.pop("escala", None)
    # Preserve hashes of saved analyses from before the optional evidence fields.
    if pipeline_version == "jev-2-polos-mvp-1":
        for name in ("semantic_evidence_check", "jev_evidence_search", "evidence_existence_min"):
            effective.pop(name)
    public = {"config_version": CONFIG_VERSION, "pipeline_version": pipeline_version,
              "effective_config": effective}
    canonical = json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def config_ranges(max_tokens: int, max_chunks: int) -> dict:
    return {"chunk_tokens": {"min": 100, "max": min(2000, max_tokens), "step": 1},
            **{name: {"min": 0, "max": 1, "step": 0.01} for name in
               ("relevance_margin_min", "level_confidence_min", "direction_margin_min")},
            "min_valid_chunks": {"min": 1, "max": max_chunks, "step": 1},
            "bootstrap_samples": {"min": 200, "max": 10000, "step": 1},
            "bootstrap_seed": {"min": 0, "max": 2**32 - 1, "step": 1}}


def resolve_config(settings, overrides: ExperimentOverrides | None) -> ExperimentConfig:
    from .lab_credentials import model_catalog
    config = ExperimentConfig.model_validate({**settings.algorithm_defaults().model_dump(),
        **(overrides.model_dump(exclude_unset=True) if overrides is not None else {})})
    if config.chunk_tokens > settings.max_tokens or config.min_valid_chunks > settings.max_chunks:
        raise ValueError("Parâmetros incompatíveis com os limites da API.")
    if config.jev_model not in settings.allowed_jev_models or config.llm_model not in model_catalog(settings):
        raise ValueError("Modelo não permitido nesta API.")
    return config
