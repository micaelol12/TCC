"""Load local configuration without replacing the process environment."""
from pathlib import Path
from dotenv import load_dotenv


def load_environment(project_root: Path) -> None:
    # Precedence: terminal/service > API-specific .env > project-wide .env.
    # Explicit paths make startup independent of the current working directory.
    load_dotenv(project_root / "app" / "api" / ".env", override=False)
    load_dotenv(project_root / ".env", override=False)
