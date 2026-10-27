"""Replica o sentenciador puro do notebook para a API independente, sem executá-lo."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sentence_source():
    source = (ROOT / "tcc_lib/segmentacao.py").read_text(encoding="utf-8")
    excluded = {"_encoder", "normalizar_quebras_texto", "configuracao_chunks", "preparar_segmentacao"}
    parts = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.Import) and any(alias.name == "tiktoken" for alias in node.names):
            continue
        if getattr(node, "name", None) in excluded:
            continue
        start = min([node.lineno, *[d.lineno for d in getattr(node, "decorator_list", [])]])
        parts.append("\n".join(source.splitlines()[start - 1:node.end_lineno]))
    header = ('"""Portuguese sentence rules mirrored from tcc_lib/segmentacao.py.\n\n'
              'Regenerate with scripts/replicate_sentence_rules.py. No network access.\n"""\n')
    return header + "\n\n".join(parts) + "\n"


if __name__ == "__main__":
    (ROOT / "app/api/app/pipeline/sentences.py").write_text(sentence_source(), encoding="utf-8")
