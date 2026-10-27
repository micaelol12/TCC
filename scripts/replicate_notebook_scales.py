"""Replica regras validadas do notebook. A API nunca carrega/executa notebooks."""
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
                return ast.get_source_segment(source, node) + '\n\n'
    raise ValueError(name)

const = next(s for s in sources if s.startswith('SITUACAO_SEM_POSICAO ='))
scale = next(s for s in sources if s.startswith('AXIS_SPECS_5 ='))
scale = scale[:scale.index('def tabela_escala')]
scale = scale.replace('ESCALA_ATUAL = ESCALA_5_NIVEIS', 'ESCALA_ATUAL = ESCALA_9_NIVEIS')
scale = scale.replace('# Histórico do notebook: cinco níveis. Selecione outro objeto aqui.', '# Padrão da API preservado: nove níveis.')
scale = scale.replace('AXIS_SPECS = AXIS_SPECS_5', 'AXIS_SPECS = AXIS_SPECS_9')
scale += '''
# Compatibilidade de consumidores anteriores: nove níveis explícitos por padrão da API.
PolarityLevel = Literal[-4, -3, -2, -1, 0, 1, 2, 3, 4]
COUNT_KEYS = {-4: "minus4", -3: "minus3", -2: "minus2", -1: "minus1", 0: "zero",
              1: "plus1", 2: "plus2", 3: "plus3", 4: "plus4"}
def level_score(level, escala=None):
    return valor_nivel(level, validar_escala(ESCALA_ATUAL if escala is None else escala))
'''
(root / 'app/api/app/polarity.py').write_text('"""Réplica das definições autoritativas do notebook passo a passo."""\n' + const + '\n' + scale, encoding='utf-8')
(root / 'app/api/app/pipeline/rubrics.py').write_text(
    '"""Metadados dos eixos, replicados do notebook autoritativo em polarity.py."""\n'
    'from ..polarity import AXIS_SPECS_9 as AXIS_SPECS, SITUACAO_SEM_POSICAO\n', encoding='utf-8')
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
from ..polarity import ESCALA_ATUAL, validar_escala, valor_nivel, classe_nivel, NIVEIS_POLARIDADE
CHAVES_NIVEIS = tuple(NIVEIS_POLARIDADE)
MIN_PALAVRAS_EVIDENCIA = 4
MOTIVOS_POLARIDADE = {"empate_nivel", "baixa_confianca_nivel", "direcao_ambigua"}
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
(root / 'app/api/app/pipeline/evidence.py').write_text(evidence.rstrip() + '\n', encoding='utf-8')

# Snapshots usados pelos testes do contrato compartilhado; nunca substituem a fonte autoritativa.
ns = {}
exec(const + '\n' + scale, ns)
fixtures = [ns[name].model_dump(mode='json') for name in ('ESCALA_5_NIVEIS', 'ESCALA_9_NIVEIS')]
(root / 'app/shared/src/testing/scaleFixtures.ts').write_text(
    "import type { OrdinalScale } from '../domain/ordinalScale'\n"
    "// Réplica gerada do notebook; execute scripts/replicate_notebook_scales.py para atualizar.\n"
    'export const scaleFixtures: OrdinalScale[] = ' + json.dumps(fixtures, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
