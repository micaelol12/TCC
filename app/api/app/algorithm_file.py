"""Read the server's public algorithm parameters using the Lab contract."""
import json
from pathlib import Path
from .experiment_config import ExperimentConfig

API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = API_ROOT / "analysis-config.json"


def load_algorithm_file(path: str | Path) -> ExperimentConfig:
    source = Path(path)
    if not source.is_absolute():
        source = API_ROOT / source
    try:
        # utf-8-sig also accepts JSON saved with a BOM by Windows editors.
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        return ExperimentConfig.model_validate(data)
    except (OSError, UnicodeError, ValueError):
        # Never echo file contents, including accidentally pasted credentials.
        raise ValueError("Arquivo ALGORITHM_CONFIG_PATH ausente ou inválido; use o contrato de analysis-config.json.") from None
