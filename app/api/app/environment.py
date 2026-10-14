"""Load local configuration without replacing the process environment."""
from pathlib import Path
import os
from dotenv import load_dotenv, dotenv_values


def load_environment(project_root: Path) -> None:
    # Precedence: terminal/service > API-specific .env > project-wide .env.
    # Explicit paths make startup independent of the current working directory.
    api = project_root / "app" / "api"
    variant = os.getenv("APP_ENV") or dotenv_values(api / ".env").get("APP_ENV") or dotenv_values(project_root / ".env").get("APP_ENV")
    if variant == "lab":
        # Lab inherits configuration, never provider credentials.
        for path in (api / ".env.lab", api / ".env", project_root / ".env"):
            for name, value in dotenv_values(path).items():
                if name not in {"TYPESAFE_API_KEY", "MARITACA_API_KEY", "GEMINI_API_KEY"} and value is not None:
                    os.environ.setdefault(name, value)
        return
    load_dotenv(api / ".env", override=False)
    load_dotenv(project_root / ".env", override=False)
