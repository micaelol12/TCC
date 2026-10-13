"""Configuration comes from the environment and local .env files, never requests."""
from dataclasses import dataclass
from pathlib import Path
import os
from .environment import load_environment


load_environment(Path(__file__).resolve().parents[3])


@dataclass(frozen=True)
class Settings:
    typesafe_key: str = os.getenv("TYPESAFE_API_KEY", "")
    maritaca_key: str = os.getenv("MARITACA_API_KEY", "")
    jev_model: str = os.getenv("JEV_MODEL", "jev-1.13.0")
    llm_model: str = os.getenv("LLM_MODEL", "sabia-4")
    max_chars: int = int(os.getenv("MAX_CHARS", "60000"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "12000"))
    max_chunks: int = int(os.getenv("MAX_CHUNKS", "20"))
    timeout_seconds: int = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "120"))
    concurrent_chunks: int = int(os.getenv("CONCURRENT_CHUNKS", "2"))
    concurrent_requests: int = int(os.getenv("CONCURRENT_REQUESTS", "3"))
    hourly_requests: int = int(os.getenv("HOURLY_REQUESTS", "30"))
    daily_calls: int = int(os.getenv("DAILY_PROVIDER_CALLS", "1000"))
    reports_db_path: str = os.getenv("REPORTS_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "reports.sqlite3"))
    reports_hourly_requests: int = int(os.getenv("REPORTS_HOURLY_REQUESTS", "60"))


settings = Settings()
