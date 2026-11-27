"""Conferência literal de citações, tolerando apenas diferenças de apresentação."""
import re
import unicodedata

MIN_PALAVRAS_EVIDENCIA = 4

_MARCACAO_MD = re.compile(r"(\*\*|__|<br\s*/?>|^#{1,6}\s+|^>\s?|\|)", re.M)
_RETICENCIAS = re.compile(r"^(\.\.\.|…)\s*|\s*(\.\.\.|…)$")


def normalizar_citacao(texto):
    """Normaliza apresentação preservando palavras, acentos e pontuação."""
    texto = unicodedata.normalize("NFKC", texto).translate(str.maketrans({
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "–": "-", "—": "-", "\u00ad": None, "\u200b": None, "\ufeff": None,
    }))
    return " ".join(texto.split()).casefold()


def remover_marcacao_markdown(texto):
    """Remove marcações de apresentação antes da comparação literal da citação."""
    return _MARCACAO_MD.sub(" ", texto)


def evidencia_literal_confere(texto, evidencia, min_palavras=MIN_PALAVRAS_EVIDENCIA):
    """Trecho contínuo do texto, ignorando marcação Markdown e escapes do JSON do prompt.

    Paráfrases, omissões internas e citações com menos de `min_palavras` palavras são recusadas.
    """
    citacao = evidencia.replace("\\n", " ").replace('\\"', '"')

    citacao = normalizar_citacao(remover_marcacao_markdown(citacao)).strip(" \"'.,;:")
    citacao = _RETICENCIAS.sub("", citacao).strip(" \"'")

    if len(citacao.split()) < min_palavras:
        return False
    return citacao in normalizar_citacao(remover_marcacao_markdown(texto))
