"""Validated server configuration; credentials never belong to analysis requests."""
from dataclasses import dataclass, field
from pathlib import Path
import os
from .environment import load_environment
from .experiment_config import ExperimentConfig
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


def models(name, default_name, default):
    return field(default_factory=lambda: tuple(dict.fromkeys(
        value.strip() for value in os.getenv(name, os.getenv(default_name, default)).split(",") if value.strip())))


@dataclass(frozen=True)
class Settings:
    app_env: str = env("APP_ENV", "development")
    experimental_config_enabled: bool = boolean("EXPERIMENTAL_CONFIG_ENABLED")
    typesafe_key: str = field(default_factory=lambda: os.getenv("TYPESAFE_API_KEY", ""), repr=False)
    maritaca_key: str = field(default_factory=lambda: os.getenv("MARITACA_API_KEY", ""), repr=False)
    gemini_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""), repr=False)
    allowed_gemini_models: tuple[str, ...] = field(default_factory=lambda: tuple(value.strip() for value in os.getenv('ALLOWED_GEMINI_MODELS', 'gemini-3.1-flash-lite,gemini-3.7-flash').split(',') if value.strip()))
    jev_model: str = env("JEV_MODEL", "jev-1.13.0")
    llm_model: str = env("LLM_MODEL", "sabia-4")
    allowed_jev_models: tuple[str, ...] = models("ALLOWED_JEV_MODELS", "JEV_MODEL", "jev-1.13.0")
    allowed_llm_models: tuple[str, ...] = models("ALLOWED_LLM_MODELS", "LLM_MODEL", "sabia-4")
    chunk_tokens: int = number("CHUNK_TOKENS", 600)
    relevance_margin_min: float = number("JEV_RELEVANCE_MARGIN_MIN", 0.60, float)
    level_confidence_min: float = number("JEV_LEVEL_CONFIDENCE_MIN", 0.50, float)
    direction_margin_min: float = number("JEV_DIRECTION_MARGIN_MIN", 0.20, float)
    min_valid_chunks: int = number("MIN_VALID_CHUNKS", 16)
    bootstrap_samples: int = number("BOOTSTRAP_SAMPLES", 2000)
    bootstrap_seed: int = number("BOOTSTRAP_SEED", 42)
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
        return ExperimentConfig(**{name: getattr(self, name) for name in ExperimentConfig.model_fields if hasattr(self, name)})

    def __post_init__(self):
        if self.app_env == "lab":
            for name in ("typesafe_key", "maritaca_key", "gemini_key"):
                object.__setattr__(self, name, "")
        if self.app_env not in {"development", "lab", "production"}:
            raise ValueError("Variável inválida: APP_ENV.")
        if self.experimental_config_enabled and self.app_env != "lab":
            raise ValueError("EXPERIMENTAL_CONFIG_ENABLED exige APP_ENV=lab.")
        for name in ("max_chars", "max_tokens", "max_chunks", "timeout_seconds", "concurrent_chunks",
                     "concurrent_requests", "hourly_requests", "daily_calls", "reports_hourly_requests"):
            if getattr(self, name) <= 0:
                variable = {"timeout_seconds": "ANALYSIS_TIMEOUT_SECONDS", "daily_calls": "DAILY_PROVIDER_CALLS"}.get(name, name.upper())
                raise ValueError(f"Limite inválido: {variable}.")
        try:
            defaults = self.algorithm_defaults()
        except ValidationError as error:
            names = {"relevance_margin_min": "JEV_RELEVANCE_MARGIN_MIN", "level_confidence_min": "JEV_LEVEL_CONFIDENCE_MIN", "direction_margin_min": "JEV_DIRECTION_MARGIN_MIN"}
            invalid = ", ".join(names.get(str(item["loc"][0]), str(item["loc"][0]).upper()) for item in error.errors())
            raise ValueError(f"Variáveis inválidas: {invalid}.") from None
        if defaults.chunk_tokens > self.max_tokens or defaults.min_valid_chunks > self.max_chunks:
            raise ValueError("CHUNK_TOKENS/MIN_VALID_CHUNKS excedem MAX_TOKENS/MAX_CHUNKS.")
        if self.jev_model not in self.allowed_jev_models or self.llm_model not in self.allowed_llm_models:
            raise ValueError("JEV_MODEL/LLM_MODEL devem constar em ALLOWED_JEV_MODELS/ALLOWED_LLM_MODELS.")
        if set(self.allowed_gemini_models) & (set(self.allowed_llm_models) | {'sabia-4', 'sabiazinho-4'}):
            raise ValueError('ALLOWED_GEMINI_MODELS conflita com os modelos Maritaca.')
        for name, allowed in (("jev_model", self.allowed_jev_models), ("llm_model", self.allowed_llm_models), ('llm_model', self.allowed_gemini_models)):
            for value in allowed:
                try:
                    ExperimentConfig(**{name: value})
                except ValueError:
                    raise ValueError("Lista ALLOWED_JEV_MODELS/ALLOWED_LLM_MODELS inválida.") from None


settings = Settings()
