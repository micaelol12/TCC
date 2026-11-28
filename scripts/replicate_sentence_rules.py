"""Replica o sentenciador puro do notebook para a API independente, sem executá-lo."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sentence_source():
    """Extrai as regras compartilhadas, preservando comentários e formatação."""
    source = (ROOT / "tcc_lib/segmentacao.py").read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    excluded = {"_encoder", "normalizar_quebras_texto", "configuracao_chunks", "preparar_segmentacao"}
    parts = []
    previous_end = 0

    for node in ast.parse(source).body:
        # Inclui o espaço e os comentários entre declarações. O AST sozinho
        # não representa esses comentários e a extração anterior os descartava.
        part = "".join(lines[previous_end:node.end_lineno])
        previous_end = node.end_lineno

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue

        if isinstance(node, ast.Import) and any(alias.name == "tiktoken" for alias in node.names):
            continue

        if getattr(node, "name", None) in excluded:
            continue

        parts.append(part)

    header = ('"""Segmentação em português para chunks e evidências, sem acesso à rede.\n\n'
              'Fluxo: blocos estruturais -> sentenças com índices originais -> chunks.\n'
              'As referências conhecidas são protegidas contra cortes internos.\n\n'
              'Gerado de tcc_lib/segmentacao.py; edite a origem e execute\n'
              'scripts/replicate_sentence_rules.py para atualizar este arquivo.\n"""\n')

    return header + "".join(parts).rstrip("\n") + "\n"


if __name__ == "__main__":
    (ROOT / "app/api/app/pipeline/sentences.py").write_text(sentence_source(), encoding="utf-8")
