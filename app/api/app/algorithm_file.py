"""Read the server's public algorithm parameters using the Lab contract."""
from pathlib import Path
from .experiment_config import ExperimentConfig
from .analysis_defaults import API_ROOT, DEFAULT_CONFIG_PATH, read_algorithm_data

def load_algorithm_file(path: str | Path) -> ExperimentConfig:
    source = Path(path)
    if not source.is_absolute():
        source = API_ROOT / source
    try:
        # utf-8-sig also accepts JSON saved with a BOM by Windows editors.
        data = read_algorithm_data(source)
        if set(data) != set(ExperimentConfig.model_fields):
            raise ValueError('Arquivo incompleto ou com campos desconhecidos.')
        return ExperimentConfig.model_validate(data)
    except (OSError, UnicodeError, ValueError):
        # Never echo file contents, including accidentally pasted credentials.
        raise ValueError("Arquivo ALGORITHM_CONFIG_PATH ausente ou inválido; use o contrato de analysis-config.json.") from None
