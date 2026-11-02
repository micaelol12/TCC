"""File-backed defaults. No political definitions are maintained in Python."""
from copy import deepcopy
import json
from pathlib import Path
from .polarity import validar_escala

API_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = API_ROOT / 'analysis-config.json'


def read_algorithm_data(path=None):
    source = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not source.is_absolute():
        source = API_ROOT / source
    try:
        data = json.loads(source.read_text(encoding='utf-8-sig'))
        if not isinstance(data, dict):
            raise ValueError('Expected configuration object')
        return data
    except (OSError, UnicodeError, ValueError):
        raise ValueError('Arquivo ALGORITHM_CONFIG_PATH ausente ou inválido; use o contrato de analysis-config.json.') from None


def default_value(name):
    try:
        return deepcopy(read_algorithm_data()[name])
    except KeyError:
        raise ValueError('analysis-config.json deve conter todas as definições do algoritmo.') from None


def five_level_scale(scale):
    """Project the configured nine-level rubric; no alternative anchors are stored."""
    data = scale.model_dump(mode='json')
    if len(scale.niveis) != 9:
        return scale
    indices = (0, 2, 4, 6, 8)
    keys = ('polo_B_forte', 'polo_B_moderado', 'sem_posicao', 'polo_A_moderado', 'polo_A_forte')
    original = data['niveis']
    data['id'] = 'ordinal_5_v1' if scale.id == 'ordinal_9_v1' else scale.id + '_5'
    data['niveis'] = [{**original[index], 'chave': key, 'codigo': code,
                       'rotulo': key.replace('_', ' '), 'valor': offset / 4}
                      for offset, (index, key, code) in enumerate(zip(indices, keys, range(-2, 3)))]
    data['rubricas_por_eixo'] = {axis: {key: rubrics[original[index]['chave']] for index, key in zip(indices, keys)}
                                for axis, rubrics in data['rubricas_por_eixo'].items()}
    return validar_escala(data)


def configured_scales(scale):
    projected = five_level_scale(scale)
    return [projected, scale] if projected.hash != scale.hash else [scale]


# Compatibility names are values loaded or projected from the JSON, never copies
# of political definitions. Requests use their own validated configuration.
CONTEXTO_POSICAO_POLITICA = default_value('contexto_posicao_politica')
ESCALA_ATUAL = validar_escala(default_value('escala'))
ESCALA_9_NIVEIS = ESCALA_ATUAL
ESCALA_5_NIVEIS = five_level_scale(ESCALA_ATUAL)
AXIS_SPECS = default_value('axis_specs')
NIVEIS_POLARIDADE = {n.chave: n.codigo for n in ESCALA_ATUAL.niveis}
