"""Replica apenas regras puras do notebook. Definições e escalas do app vêm de analysis-config.json."""
import ast
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
nb = json.loads((root / 'Pipeline - Passo a Passo.ipynb').read_text(encoding='utf-8'))
sources = [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']
def get(name):
    for source in sources:
        for node in ast.parse(source).body:
            if getattr(node, 'name', None) == name:
                segment = ast.get_source_segment(source, node)
                if name in ('criar_questoes_eixo', 'criar_rubrica_polaridade_ordinal'):
                    segment = segment.replace('    spec = axis_specs[axis]\n', "    spec = axis_specs[axis]\n    if isinstance(spec, DefinicaoEixo):\n        spec = spec.model_dump(mode='json')\n")
                return segment + '\n\n'
    raise ValueError(name)

domain_names = ['criar_questoes_eixo', 'criar_rubrica_polaridade_ordinal', '_score_campo', '_score_probabilidade',
    '_score_distribuicao', '_score_margem', '_score_classe', '_normalizar_relevancia_noul_2_polos',
    '_normalizar_polaridade_ordinal', 'decidir_jev', 'motivos_fallback', '_score_normalizar_citacao',
    '_sem_markdown', '_score_evidencia_confere', 'decisao_vazia', 'decidir_llm']
header = '''"""Réplica das regras puras validadas no notebook autoritativo."""
import math
import re
import unicodedata
from collections.abc import Mapping
from copy import deepcopy
from .rubrics import AXIS_SPECS
from ..analysis_defaults import CONTEXTO_POSICAO_POLITICA, ESCALA_ATUAL, NIVEIS_POLARIDADE
from ..polarity import DefinicaoEixo, validar_escala, valor_nivel, classe_nivel
CHAVES_NIVEIS = tuple(NIVEIS_POLARIDADE)
MIN_PALAVRAS_EVIDENCIA = 4
MOTIVOS_POLARIDADE = {"empate_nivel", "baixa_confianca_nivel", "direcao_ambigua", "intensidade_ambigua"}
'''
for source in sources:
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'_MARCACAO_MD','_RETICENCIAS'} for t in node.targets):
            header += ast.get_source_segment(source, node) + '\n'
(root / 'app/api/app/pipeline/domain.py').write_text((header + '\n' + ''.join(get(n) for n in domain_names)).rstrip() + '\n', encoding='utf-8')
evidence = next(s for s in sources if 'async def audit_evidence(' in s)
evidence = evidence[:evidence.index('async def enriquecer_evidencias')]
evidence = evidence.replace('from tcc_lib.segmentacao import intervalos_sentencas',
                            'from .sentences import intervalos_sentencas')
evidence = evidence.replace('RELATIONS = {', 'from ..analysis_defaults import CONTEXTO_POSICAO_POLITICA\n\nRELATIONS = {', 1)
(root / 'app/api/app/pipeline/evidence.py').write_text(evidence.rstrip() + '\n', encoding='utf-8')


(root / 'app/api/app/prompting.py').write_text(
    '"""Provider output instructions; political definitions come from the JSON."""\n'
    'from .analysis_defaults import CONTEXTO_POSICAO_POLITICA\n\n\n' + get('instrucoes_escala').rstrip() + '\n', encoding='utf-8')
