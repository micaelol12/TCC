"""Portuguese sentence rules mirrored from tcc_lib/segmentacao.py.

Regenerate with scripts/replicate_sentence_rules.py. No network access.
"""
from bisect import bisect_right

from dataclasses import dataclass

from functools import lru_cache

from itertools import groupby

from pathlib import Path

import re

_ESTRUTURA = re.compile(
    r"^[ \t]*(?P<marca>#{1,6}[ \t]+|[-*+•][ \t]+|"
    r"(?:\d+(?:\.\d+)*[.)]|\([\da-z]+\)|[a-z]\)|\d+[ \t]*[–—-]|"
    r"[IVXLCDM]+[ \t]*[.)–—-])[ \t]+|"
    r"[\"“‘']?(?:Art\.\s+\d+(?:\.\d+)*(?:[º°o])?(?:-[A-Za-z0-9]+)?\.?|"
    r"§[ \t]*\d+[º°o]?\.?)[ \t]*|\|)",
    re.IGNORECASE,
)

_FIM_FRASE = re.compile(r'''[.!?]["'”’»\)\]]*\s*$''')

_NUMERO_REFERENCIA = r"\d+(?:\.\d+)*(?:[º°o])?(?:-[A-Za-z0-9]+)?(?:/\d+)?"

_REFERENCIAS = tuple(re.compile(padrao, re.IGNORECASE) for padrao in (
    rf"\b(?:arts?|págs?)\.\s*{_NUMERO_REFERENCIA}",
    r"\bincs?\.\s*(?:[IVXLCDM]+|\d+)\b",
    rf"\b(?:n\.[º°]|n[º°]\.?)\s*{_NUMERO_REFERENCIA}",
    rf"\b(?:res|dec|ac|port)\.(?:-[A-Za-zÀ-ÿ]+)?\s+(?:n[º°]\s*)?{_NUMERO_REFERENCIA}",
    r"\b(?:dr|dra|sr|sra|prof|profa|exmo|exma|av|rod)\.\s+[^\W\d_][\w-]*",
    r"\b[A-Za-z0-9]+(?:[.,][A-Za-z0-9]+)+(?:/\d+)?\b",
    r"\b(?:[A-Za-z]\.){2,}\s+(?-i:[a-zà-ÿ])\w*",
    r"(?:https?://|www\.)[^\s<>\"“”]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
))

def _intervalos_referencias(texto):
    return [(m.start(), m.start() + len(m.group().rstrip('.,;:!?)]}”’»')))
            for padrao in _REFERENCIAS for m in padrao.finditer(texto)]

def _intervalos_linguisticos(texto):
    """Une fronteiras do Punkt que caiam dentro de uma referência conhecida."""
    referencias = _intervalos_referencias(texto)
    intervalos = []
    for inicio, fim in _sentenciador().span_tokenize(texto):
        if intervalos and any(a < intervalos[-1][1] < b for a, b in referencias):
            intervalos[-1] = (intervalos[-1][0], fim)
        else:
            intervalos.append((inicio, fim))
    return intervalos

@lru_cache(maxsize=1)
def _sentenciador():
    from nltk.tabdata import PunktDecoder
    from nltk.tokenize.punkt import (
        PunktLanguageVars, PunktParameters, PunktSentenceTokenizer,
    )

    class Portugues(PunktLanguageVars):
        re_boundary_realignment = re.compile(r'''["'”’»\)\]}]+?(?:\s+|(?=--)|$)''', re.MULTILINE)

    pasta = Path(__file__).with_name("resources") / "punkt_portuguese"
    parametros = PunktParameters()
    decoder = PunktDecoder()
    # Lê somente os quatro recursos fixos do projeto, sem procurar nltk_data
    # externo nem depender das permissões globais de caminhos do NLTK.
    with (pasta / "collocations.tab").open(encoding="utf-8") as arquivo:
        parametros.collocations = set(decoder.tab2tups(arquivo))
    with (pasta / "sent_starters.txt").open(encoding="utf-8") as arquivo:
        parametros.sent_starters = decoder.txt2set(arquivo)
    with (pasta / "abbrev_types.txt").open(encoding="utf-8") as arquivo:
        parametros.abbrev_types = decoder.txt2set(arquivo)
    with (pasta / "ortho_context.tab").open(encoding="utf-8") as arquivo:
        parametros.ortho_context = decoder.tab2intdict(arquivo)
    parametros.abbrev_types.update({
        "art", "arts", "dr", "dra", "sr", "sra", "prof", "profa", "n", "nº", "n°", "no", "n.º",
        "inc", "incs", "pág", "págs", "exmo", "exma", "av", "rod",
    })
    return PunktSentenceTokenizer(parametros, lang_vars=Portugues())

def _e_titulo(linha):
    return bool(re.match(r"^#{1,6}\s", linha)) or (
        any(c.isalpha() for c in linha) and linha.isupper()
        and not _FIM_FRASE.search(linha) and not _ESTRUTURA.match(linha)
    )

@dataclass(frozen=True)
class _Unidade:
    inicio: int
    fim: int
    paragrafo: tuple[int, int]
    titulo: bool = False

def _unidades(texto):
    """Offsets no texto recebido; quebras de linha não encerram uma sentença.

    Marcadores estruturais delimitam blocos, inclusive itens sem pontuação. O
    prefixo de enumeração pertence à primeira sentença, nunca vira um chunk só.
    """
    blocos = []
    inicio = 0
    offset = 0
    referencias = _intervalos_referencias(texto)
    for linha in texto.splitlines(keepends=True):
        conteudo = linha.strip()
        continuacao = any(a < offset < b for a, b in referencias)
        if conteudo and not continuacao and (_ESTRUTURA.match(linha) or _e_titulo(conteudo)):
            if texto[inicio:offset].strip():
                blocos.append((inicio, offset, False))
            inicio = offset
            if _e_titulo(conteudo) or conteudo.startswith("|"):
                blocos.append((inicio, offset + len(linha), True))
                inicio = offset + len(linha)
        offset += len(linha)
    if texto[inicio:].strip():
        blocos.append((inicio, len(texto), False))

    paragrafos = [m.end() for m in re.finditer(r"\n[ \t]*\n", texto)]
    unidades = []
    for inicio, fim, titulo in blocos:
        bloco = texto[inicio:fim]
        deslocamento = len(bloco) - len(bloco.lstrip())
        bloco = bloco.strip()
        inicio += deslocamento
        if titulo:
            intervalos = [(0, len(bloco))]
        else:
            marca = _ESTRUTURA.match(bloco)
            prefixo = marca.end() if marca else 0
            intervalos = [(a + prefixo, b + prefixo)
                          for a, b in _intervalos_linguisticos(bloco[prefixo:])]
            if intervalos:
                intervalos[0] = (0, intervalos[0][1])
            else:
                intervalos = [(0, len(bloco))]
        # Blocos de lista/título também separam grupos sem exigir linha em branco.
        grupo_base = len(unidades)
        for a, b in intervalos:
            unidades.append(_Unidade(inicio + a, inicio + b,
                                     (grupo_base, bisect_right(paragrafos, inicio + a)), titulo))
    return unidades

def intervalos_sentencas(texto):
    """Fronteiras compartilhadas pelos chunks e evidências, no texto original."""
    return [(unidade.inicio, unidade.fim) for unidade in _unidades(texto)]

def _agrupar_sentencas(texto, unidades, alvo, contar):
    grupos = [list(g) for _, g in groupby(unidades, key=lambda u: u.paragrafo)]
    # Mantém o título com o parágrafo seguinte quando o conjunto cabe no alvo.
    reunidos = []
    for grupo in grupos:
        if reunidos and all(u.titulo for u in reunidos[-1]):
            reunidos[-1].extend(grupo)
        else:
            reunidos.append(grupo)
    chunks = []
    atual = []

    def trecho(us):
        return texto[us[0].inicio:us[-1].fim].strip()

    def adicionar(us):
        nonlocal atual
        if atual and contar(trecho(atual + us)) > alvo:
            chunks.append(trecho(atual))
            atual = []
        atual.extend(us)
        if contar(trecho(atual)) > alvo:
            # Uma unidade indivisível acima do alvo fica sozinha, sem corte.
            chunks.append(trecho(atual))
            atual = []

    for grupo in reunidos:
        if contar(trecho(grupo)) <= alvo:
            adicionar(grupo)
        else:
            if grupo[0].titulo and atual:
                # Não deixa um título no fim do chunk anterior ao dividir um
                # parágrafo longo. Ele acompanha a primeira sentença se couber.
                chunks.append(trecho(atual))
                atual = []
            for unidade in grupo:
                adicionar([unidade])
    if atual:
        chunks.append(trecho(atual))
    return chunks
