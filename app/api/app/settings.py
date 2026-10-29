"""Validated server configuration; credentials never belong to analysis requests."""
from dataclasses import dataclass, field
from pathlib import Path
import os
from .environment import load_environment
from .experiment_config import ExperimentConfig
from .algorithm_file import DEFAULT_CONFIG_PATH, load_algorithm_file
from .polarity import EscalaOrdinal
from pydantic import ValidationError


load_environment(Path(__file__).resolve().parents[3])


def env(name, default=""):
    return field(default_factory=lambda: os.getenv(name, default))


def number(name, default, convert=int):
    def read():
        try:
            return convert(os.getenv(name, str(default)))
        except (ValueError, OverflowError):
            raise ValueError(f"Variável inválida: {name}.") from None
    return field(default_factory=read)


def boolean(name):
    def read():
        value = os.getenv(name, "false").lower()
        if value not in {"true", "false"}:
            raise ValueError(f"Variável inválida: {name}.")
        return value == "true"
    return field(default_factory=read)


def models(name):
    return field(default_factory=lambda: tuple(dict.fromkeys(
        value.strip() for value in os.environ[name].split(",") if value.strip())) if name in os.environ else None)


def algorithm_env(name, convert=str):
    """An absent environment override leaves the JSON value in effect."""
    def read():
        if name not in os.environ:
            return None
        try:
            return convert(os.environ[name])
        except (ValueError, OverflowError):
            raise ValueError(f"Variável inválida: {name}.") from None
    return field(default_factory=read)


def parse_bool(value):
    if value.lower() not in {"true", "false"}:
        raise ValueError("Booleano inválido.")
    return value.lower() == "true"


@dataclass(frozen=True)
class Settings:
    app_env: str = env("APP_ENV", "development")
    experimental_config_enabled: bool = boolean("EXPERIMENTAL_CONFIG_ENABLED")
    typesafe_key: str = field(default_factory=lambda: os.getenv("TYPESAFE_API_KEY", ""), repr=False)
    maritaca_key: str = field(default_factory=lambda: os.getenv("MARITACA_API_KEY", ""), repr=False)
    gemini_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""), repr=False)
    allowed_gemini_models: tuple[str, ...] = field(default_factory=lambda: tuple(value.strip() for value in os.getenv('ALLOWED_GEMINI_MODELS', 'gemini-3.1-flash-lite,gemini-3.7-flash').split(',') if value.strip()))
    algorithm_config_path: str = env("ALGORITHM_CONFIG_PATH")
    # None means no constructor/environment override. __post_init__ fills every
    # field from the validated JSON (or the independent Lab defaults).
    escala: EscalaOrdinal | None = None
    jev_model: str | None = algorithm_env("JEV_MODEL")
    primitiva_polaridade: str | None = algorithm_env("JEV_POLARITY_PRIMITIVE")
    regra_decisao: str | None = algorithm_env("JEV_DECISION_RULE")
    llm_model: str | None = algorithm_env("LLM_MODEL")
    allowed_jev_models: tuple[str, ...] | None = models("ALLOWED_JEV_MODELS")
    allowed_llm_models: tuple[str, ...] | None = models("ALLOWED_LLM_MODELS")
    chunk_tokens: int | None = algorithm_env("CHUNK_TOKENS", int)
    chunk_strategy: str | None = algorithm_env("CHUNK_STRATEGY")
    relevance_margin_min: float | None = algorithm_env("JEV_RELEVANCE_MARGIN_MIN", float)
    level_confidence_min: float | None = algorithm_env("JEV_LEVEL_CONFIDENCE_MIN", float)
    direction_margin_min: float | None = algorithm_env("JEV_DIRECTION_MARGIN_MIN", float)
    min_valid_chunks: int | None = algorithm_env("MIN_VALID_CHUNKS", int)
    bootstrap_samples: int | None = algorithm_env("BOOTSTRAP_SAMPLES", int)
    bootstrap_seed: int | None = algorithm_env("BOOTSTRAP_SEED", int)
    semantic_evidence_check: bool | None = algorithm_env("SEMANTIC_EVIDENCE_CHECK", parse_bool)
    jev_evidence_search: bool | None = algorithm_env("JEV_EVIDENCE_SEARCH", parse_bool)
    evidence_existence_min: float | None = algorithm_env("EVIDENCE_EXISTENCE_MIN", float)
    max_chars: int = number("MAX_CHARS", 60000)
    max_tokens: int = number("MAX_TOKENS", 12000)
    max_chunks: int = number("MAX_CHUNKS", 20)
    timeout_seconds: int = number("ANALYSIS_TIMEOUT_SECONDS", 120)
    concurrent_chunks: int = number("CONCURRENT_CHUNKS", 2)
    concurrent_requests: int = number("CONCURRENT_REQUESTS", 3)
    hourly_requests: int = number("HOURLY_REQUESTS", 30)
    daily_calls: int = number("DAILY_PROVIDER_CALLS", 1000)
    reports_db_path: str = field(default_factory=lambda: os.getenv(
        "LAB_REPORTS_DB_PATH" if os.getenv("APP_ENV") == "lab" else "REPORTS_DB_PATH", str(
            Path(__file__).resolve().parents[1] / "data" /
            ("reports-lab.sqlite3" if os.getenv("APP_ENV") == "lab" else "reports.sqlite3"))))
    reports_hourly_requests: int = number("REPORTS_HOURLY_REQUESTS", 60)

    def algorithm_defaults(self):
        return ExperimentConfig(**{name: getattr(self, name) for name in ExperimentConfig.model_fields})

    def __post_init__(self):
        if self.app_env == "lab":
            for name in ("typesafe_key", "maritaca_key", "gemini_key"):
                object.__setattr__(self, name, "")
        if self.app_env not in {"development", "lab", "production"}:
            raise ValueError("Variável inválida: APP_ENV.")
        if self.experimental_config_enabled and self.app_env != "lab":
            raise ValueError("EXPERIMENTAL_CONFIG_ENABLED exige APP_ENV=lab.")
        path = self.algorithm_config_path or (str(DEFAULT_CONFIG_PATH) if self.app_env != "lab" else "")
        base = load_algorithm_file(path) if path else ExperimentConfig(chunk_strategy="sentencas")
        values = {**base.model_dump(), **{name: getattr(self, name) for name in ExperimentConfig.model_fields
                                         if getattr(self, name) is not None}}
        for name in ("max_chars", "max_tokens", "max_chunks", "timeout_seconds", "concurrent_chunks",
                     "concurrent_requests", "hourly_requests", "daily_calls", "reports_hourly_requests"):
            if getattr(self, name) <= 0:
                variable = {"timeout_seconds": "ANALYSIS_TIMEOUT_SECONDS", "daily_calls": "DAILY_PROVIDER_CALLS"}.get(name, name.upper())
                raise ValueError(f"Limite inválido: {variable}.")
        try:
            defaults = ExperimentConfig.model_validate(values)
        except ValidationError as error:
            names = {"regra_decisao": "JEV_DECISION_RULE", "primitiva_polaridade": "JEV_POLARITY_PRIMITIVE", "relevance_margin_min": "JEV_RELEVANCE_MARGIN_MIN", "level_confidence_min": "JEV_LEVEL_CONFIDENCE_MIN", "direction_margin_min": "JEV_DIRECTION_MARGIN_MIN"}
            invalid = ", ".join(names.get(str(item["loc"][0]), str(item["loc"][0]).upper()) for item in error.errors())
            raise ValueError(f"Variáveis inválidas: {invalid}.") from None
        for name in ExperimentConfig.model_fields:
            object.__setattr__(self, name, getattr(defaults, name))
        if self.allowed_jev_models is None:
            object.__setattr__(self, "allowed_jev_models", (self.jev_model,))
        if self.allowed_llm_models is None:
            object.__setattr__(self, "allowed_llm_models", ("sabia-4",) if self.llm_model in self.allowed_gemini_models else (self.llm_model,))
        if defaults.chunk_tokens > self.max_tokens or defaults.min_valid_chunks > self.max_chunks:
            raise ValueError("CHUNK_TOKENS/MIN_VALID_CHUNKS excedem MAX_TOKENS/MAX_CHUNKS.")
        from .lab_credentials import model_catalog
        if self.jev_model not in self.allowed_jev_models or self.llm_model not in model_catalog(self):
            raise ValueError("JEV_MODEL/LLM_MODEL devem constar nos modelos permitidos da API.")
        if set(self.allowed_gemini_models) & (set(self.allowed_llm_models) | {'sabia-4', 'sabiazinho-4'}):
            raise ValueError('ALLOWED_GEMINI_MODELS conflita com os modelos Maritaca.')
        for name, allowed in (("jev_model", self.allowed_jev_models), ("llm_model", self.allowed_llm_models), ('llm_model', self.allowed_gemini_models)):
            for value in allowed:
                try:
                    ExperimentConfig(**{name: value})
                except ValueError:
                    raise ValueError("Lista ALLOWED_JEV_MODELS/ALLOWED_LLM_MODELS inválida.") from None


settings = Settings()
