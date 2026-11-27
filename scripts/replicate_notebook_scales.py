"""Extrai regras do notebook para referência, sem sobrescrever o pipeline refatorado.

Execute com --output-dir para escolher o destino. Compare alterações com os testes
de paridade antes de incorporá-las aos módulos da API.
"""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "app/api/.runtime/notebook-reference"
DOMAIN_FUNCTIONS = (
    "criar_questoes_eixo", "criar_rubrica_polaridade_ordinal", "_score_campo", "_score_probabilidade",
    "_score_distribuicao", "_score_margem", "_score_classe", "_normalizar_relevancia_noul_2_polos",
    "_normalizar_polaridade_ordinal", "decidir_jev", "motivos_fallback", "_score_normalizar_citacao",
    "_sem_markdown", "_score_evidencia_confere", "decisao_vazia", "decidir_llm",
)
DOMAIN_HEADER = '''"""Referência das regras puras do notebook; não editar os módulos da API com este arquivo."""
import math
import re
import unicodedata
from collections.abc import Mapping
from copy import deepcopy
from app.pipeline.rubrics import AXIS_SPECS
from app.analysis_defaults import CONTEXTO_POSICAO_POLITICA, ESCALA_ATUAL, NIVEIS_POLARIDADE
from app.polarity import DefinicaoEixo, validar_escala, valor_nivel, classe_nivel
CHAVES_NIVEIS = tuple(NIVEIS_POLARIDADE)
MIN_PALAVRAS_EVIDENCIA = 4
MOTIVOS_POLARIDADE = {"empate_nivel", "baixa_confianca_nivel", "direcao_ambigua", "intensidade_ambigua"}
'''


def notebook_sources():
    notebook = json.loads((ROOT / "Pipeline.ipynb").read_text(encoding="utf-8"))
    return ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]


def extract_function(sources, name):
    for source in sources:
        for node in ast.parse(source).body:
            if getattr(node, "name", None) == name:
                function = ast.get_source_segment(source, node)
                if name in ("criar_questoes_eixo", "criar_rubrica_polaridade_ordinal"):
                    function = function.replace(
                        "    spec = axis_specs[axis]\n",
                        "    spec = axis_specs[axis]\n    if isinstance(spec, DefinicaoEixo):\n        spec = spec.model_dump(mode='json')\n",
                    )
                return function + "\n\n"
    raise ValueError(name)


def domain_reference(sources):
    header = DOMAIN_HEADER
    for source in sources:
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in {"_MARCACAO_MD", "_RETICENCIAS"}
                for target in node.targets
            ):
                header += ast.get_source_segment(source, node) + "\n"
    return (header + "\n" + "".join(extract_function(sources, name) for name in DOMAIN_FUNCTIONS)).rstrip() + "\n"


def evidence_reference(sources):
    source = next(source for source in sources if "async def audit_evidence(" in source)
    source = source[:source.index("async def enriquecer_evidencias")]
    source = source.replace("from tcc_lib.segmentacao import intervalos_sentencas", "from app.pipeline.sentences import intervalos_sentencas")
    source = source.replace("RELATIONS = {", "from app.analysis_defaults import CONTEXTO_POSICAO_POLITICA\n\nRELATIONS = {", 1)
    return source.rstrip() + "\n"


def export_references(output_dir):
    output_dir = Path(output_dir).resolve()
    pipeline_dir = (ROOT / "app/api/app/pipeline").resolve()
    # Mesmo com --output-dir, não permita substituir módulos de produção.
    if output_dir == pipeline_dir or pipeline_dir.is_relative_to(output_dir) or output_dir.is_relative_to(pipeline_dir):
        raise ValueError("Escolha um diretório de referência fora de app/api/app/pipeline.")
    sources = notebook_sources()
    references = {
        "domain.py": domain_reference(sources),
        "evidence.py": evidence_reference(sources),
        "prompting.py": "from app.analysis_defaults import CONTEXTO_POSICAO_POLITICA\n\n" + extract_function(sources, "instrucoes_escala").rstrip() + "\n",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, source in references.items():
        (output_dir / name).write_text(source, encoding="utf-8")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    arguments = parser.parse_args()
    print(f"Referências exportadas para {export_references(arguments.output_dir)}")


if __name__ == "__main__":
    main()
