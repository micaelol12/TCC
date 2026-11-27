"""Segmentação local: sentenças em português, parágrafos e contagem cl100k.

O tamanho alvo é uma referência; uma sentença longa nunca é truncada. O modo
``tokens`` conserva o splitter anterior para comparações controladas.
"""
from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from itertools import groupby
from pathlib import Path
import re

import tiktoken


# Marcadores que iniciam blocos: títulos, listas, artigos legais e tabelas.
_ESTRUTURA = re.compile(
    r"^[ \t]*(?P<marca>#{1,6}[ \t]+|[-*+•][ \t]+|"
    r"(?:\d+(?:\.\d+)*[.)]|\([\da-z]+\)|[a-z]\)|\d+[ \t]*[–—-]|"
    r"[IVXLCDM]+[ \t]*[.)–—-])[ \t]+|"
    r"[\"“‘']?(?:Art\.\s+\d+(?:\.\d+)*(?:[º°o])?(?:-[A-Za-z0-9]+)?\.?|"
    r"§[ \t]*\d+[º°o]?\.?)[ \t]*|\|)",
    re.IGNORECASE,
)
# Uma frase pode terminar com pontuação seguida de aspas ou parênteses.
_FIM_FRASE = re.compile(r'''[.!?]["'”’»\)\]]*\s*$''')

# Protege somente referências reconhecidas, sem reescrever o texto. O número
# ou nome seguinte faz parte do intervalo para impedir cortes após a abreviação.
_NUMERO_REFERENCIA = r"\d+(?:\.\d+)*(?:[º°o])?(?:-[A-Za-z0-9]+)?(?:/\d+)?"
_PADROES_REFERENCIAS = (
    # Artigos e páginas: art. 5º, arts. 17, pág. 12.
    rf"\b(?:arts?|págs?)\.\s*{_NUMERO_REFERENCIA}",
    # Incisos em algarismos romanos ou arábicos.
    r"\bincs?\.\s*(?:[IVXLCDM]+|\d+)\b",
    # Abreviações de número: n.º, nº e n°.
    rf"\b(?:n\.[º°]|n[º°]\.?)\s*{_NUMERO_REFERENCIA}",
    # Atos legais: Res.-TSE nº 23.732/2024, dec., ac. e port.
    rf"\b(?:res|dec|ac|port)\.(?:-[A-Za-zÀ-ÿ]+)?\s+(?:n[º°]\s*)?{_NUMERO_REFERENCIA}",
    # Tratamentos e endereços acompanhados de nome: Dr. Silva, Av. Brasil.
    r"\b(?:dr|dra|sr|sra|prof|profa|exmo|exma|av|rod)\.\s+[^\W\d_][\w-]*",
    # Números, versões e códigos com pontos ou vírgulas internos.
    r"\b[A-Za-z0-9]+(?:[.,][A-Za-z0-9]+)+(?:/\d+)?\b",
    # Siglas pontuadas seguidas de palavra em minúsculas.
    r"\b(?:[A-Za-z]\.){2,}\s+(?-i:[a-zà-ÿ])\w*",
    # URLs e endereços de e-mail.
    r"(?:https?://|www\.)[^\s<>\"“”]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
)
_REFERENCIAS = tuple(re.compile(padrao, re.IGNORECASE) for padrao in _PADROES_REFERENCIAS)


def _intervalos_referencias(texto):
    """Localiza referências cujo ponto interno não deve encerrar uma sentença.

    Retira a pontuação final do intervalo protegido para permitir o corte real
    da frase. Os índices continuam relativos ao texto recebido.
    """
    intervalos = []
    for padrao in _REFERENCIAS:
        referencias_encontradas = list(padrao.finditer(texto))
        for referencia in referencias_encontradas:
            conteudo = referencia.group().rstrip('.,;:!?)]}”’»')
            intervalos.append((referencia.start(), referencia.start() + len(conteudo)))
    return intervalos


def _intervalos_linguisticos(texto):
    """Une fronteiras do Punkt que caiam dentro de uma referência conhecida."""
    referencias = _intervalos_referencias(texto)
    intervalos = []
    sentencas = list(_sentenciador().span_tokenize(texto))
    for inicio, fim in sentencas:
        # Se o corte anterior atravessou uma referência, estende a sentença.
        corte_em_referencia = bool(intervalos) and any(
            inicio_ref < intervalos[-1][1] < fim_ref
            for inicio_ref, fim_ref in referencias
        )
        if corte_em_referencia:
            intervalos[-1] = (intervalos[-1][0], fim)
        else:
            intervalos.append((inicio, fim))
    return intervalos


@lru_cache(maxsize=8)
def _encoder(nome):
    return tiktoken.get_encoding(nome)


@lru_cache(maxsize=1)
def _sentenciador():
    """Carrega uma única vez o Punkt em português usando os recursos locais."""
    from nltk.tabdata import PunktDecoder
    from nltk.tokenize.punkt import (
        PunktLanguageVars, PunktParameters, PunktSentenceTokenizer,
    )

    class Portugues(PunktLanguageVars):
        """Mantém aspas e delimitadores de fechamento na sentença anterior."""

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


def normalizar_quebras_texto(texto):
    """Une linhas de prosa; preserva parágrafos, títulos, listas e tabelas.

    Não decide que uma linha curta é um título apenas por seu comprimento.
    Títulos sem marcação são reconhecidos somente em maiúsculas, sem ponto final.
    """
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    linhas = texto.split("\n")
    saida = []
    unidas = 0
    anterior_titulo = False
    for linha in linhas:
        atual = linha.strip()
        titulo = _e_titulo(atual)
        estrutura = bool(_ESTRUTURA.match(atual))
        if (saida and saida[-1] and atual and not estrutura
                and not titulo and not anterior_titulo
                and not saida[-1].lstrip().startswith("|")):
            saida[-1] += " " + atual
            unidas += 1
        else:
            saida.append(atual)
        anterior_titulo = titulo
    return "\n".join(saida).strip(), unidas


def _e_titulo(linha):
    """Reconhece títulos Markdown ou em maiúsculas sem pontuação de frase."""
    return bool(re.match(r"^#{1,6}\s", linha)) or (
        any(c.isalpha() for c in linha) and linha.isupper()
        and not _FIM_FRASE.search(linha) and not _ESTRUTURA.match(linha)
    )


@dataclass(frozen=True)
class _Unidade:
    """Sentença ou linha indivisível, com índices no texto original.

    ``paragrafo`` identifica o bloco estrutural e o parágrafo dentro dele.
    ``titulo`` também marca linhas de tabela, que não passam pelo Punkt.
    """

    inicio: int
    fim: int
    paragrafo: tuple[int, int]
    titulo: bool = False


def _continua_referencia(offset, referencias):
    """Verifica se a linha começa dentro de uma referência iniciada antes.

    ``offset`` é a posição inicial da linha no texto. Os limites da referência
    ficam de fora: começar exatamente no início ou no fim não é continuação.
    """
    return any(inicio_ref < offset < fim_ref for inicio_ref, fim_ref in referencias)


def _blocos_estruturais(texto):
    """Retorna (início, fim, título/tabela) para cada bloco do texto.

    Uma quebra de linha comum não encerra o bloco. Marcadores de lista e de
    artigo iniciam blocos; títulos e linhas de tabela ficam isolados.
    """
    blocos = []
    inicio = 0
    offset = 0
    referencias = _intervalos_referencias(texto)
    linhas = texto.splitlines(keepends=True)
    for linha in linhas:
        conteudo = linha.strip()
        # Uma referência pode continuar na linha seguinte, como em "Art.\n9º".
        continuacao = _continua_referencia(offset, referencias)
        titulo = _e_titulo(conteudo)
        if conteudo and not continuacao and (_ESTRUTURA.match(linha) or titulo):
            if texto[inicio:offset].strip():
                blocos.append((inicio, offset, False))
            inicio = offset
            if titulo or conteudo.startswith("|"):
                blocos.append((inicio, offset + len(linha), True))
                inicio = offset + len(linha)
        offset += len(linha)
    if texto[inicio:].strip():
        blocos.append((inicio, len(texto), False))
    return blocos


def _intervalos_bloco(bloco, titulo):
    """Divide um bloco já aparado, mantendo a enumeração na primeira sentença.

    Os intervalos são relativos ao bloco. Títulos, tabelas e blocos sem
    sentenças reconhecidas permanecem inteiros.
    """
    if titulo:
        return [(0, len(bloco))]

    marca = _ESTRUTURA.match(bloco)
    prefixo = marca.end() if marca else 0
    intervalos_linguisticos = _intervalos_linguisticos(bloco[prefixo:])
    intervalos = [
        (inicio + prefixo, fim + prefixo)
        for inicio, fim in intervalos_linguisticos
    ]
    if not intervalos:
        return [(0, len(bloco))]

    # O marcador pertence à primeira sentença, nunca vira um chunk separado.
    intervalos[0] = (0, intervalos[0][1])
    return intervalos


def _unidades(texto):
    """Converte blocos em unidades, preservando os índices no texto original.

    O fluxo é: identificar blocos, dividir cada bloco em sentenças e converter
    os índices locais para posições absolutas. Quebras comuns não cortam frases.
    """

    separadores_paragrafos = list(re.finditer(r"\n[ \t]*\n", texto))
    paragrafos = [separador.end() for separador in separadores_paragrafos]
    unidades = []
    blocos = _blocos_estruturais(texto)

    for inicio, fim, titulo in blocos:
        bloco = texto[inicio:fim]
        deslocamento = len(bloco) - len(bloco.lstrip())
        bloco = bloco.strip()
        inicio += deslocamento

        # Blocos de lista/título também separam grupos sem exigir linha em branco.
        grupo_base = len(unidades)
        intervalos = _intervalos_bloco(bloco, titulo)
        for inicio_local, fim_local in intervalos:
            inicio_sentenca = inicio + inicio_local
            unidades.append(_Unidade(
                inicio=inicio_sentenca,
                fim=inicio + fim_local,
                paragrafo=(grupo_base, bisect_right(paragrafos, inicio_sentenca)),
                titulo=titulo,
            ))
    return unidades


def intervalos_sentencas(texto):
    """Fronteiras compartilhadas pelos chunks e evidências, no texto original."""
    unidades = _unidades(texto)
    return [(unidade.inicio, unidade.fim) for unidade in unidades]


def configuracao_chunks(*, estrategia="sentencas", tokens_alvo=None, max_tokens=None,
                       overlap_tokens=0, encoding_name="cl100k_base",
                       limite_tokens_entrada=None):
    if estrategia not in {"sentencas", "tokens"}:
        raise ValueError("estrategia deve ser 'sentencas' ou 'tokens'.")
    if tokens_alvo is not None and max_tokens is not None:
        raise ValueError("Use tokens_alvo ou o alias antigo max_tokens, não os dois.")
    alvo = tokens_alvo if tokens_alvo is not None else max_tokens
    alvo = 600 if alvo is None else alvo
    if type(alvo) is not int or alvo <= 0:
        raise ValueError("tokens_alvo deve ser um inteiro positivo.")
    if type(overlap_tokens) is not int or not 0 <= overlap_tokens < alvo:
        raise ValueError("overlap_tokens deve estar entre zero e tokens_alvo - 1.")
    if estrategia == "sentencas" and overlap_tokens != 0:
        raise ValueError("A estratégia por sentenças exige overlap_tokens=0.")
    if limite_tokens_entrada is not None and (
        type(limite_tokens_entrada) is not int or limite_tokens_entrada < alvo
    ):
        raise ValueError("limite_tokens_entrada deve ser None ou um inteiro >= tokens_alvo.")
    return {"estrategia": estrategia, "tokens_alvo": alvo, "overlap_tokens": overlap_tokens,
            "encoding_name": encoding_name, "limite_tokens_entrada": limite_tokens_entrada}


def _grupos_com_titulos(unidades):
    """Agrupa unidades consecutivas por parágrafo e associa títulos ao seguinte.

    O agrupamento apenas sugere manter o conjunto unido; o alvo de tokens é
    aplicado depois, ao montar os chunks.
    """
    grupos_por_paragrafo = groupby(unidades, key=lambda unidade: unidade.paragrafo)
    grupos = [list(grupo) for _, grupo in grupos_por_paragrafo]
    reunidos = []
    for grupo in grupos:
        grupo_anterior = reunidos[-1] if reunidos else []
        if reunidos and all(unidade.titulo for unidade in grupo_anterior):
            grupo_anterior.extend(grupo)
        else:
            reunidos.append(grupo)
    return reunidos


def _agrupar_sentencas(texto, unidades, alvo, contar):
    """Monta chunks pelo alvo de tokens, sem cortar unidades indivisíveis.

    ``contar`` recebe um trecho e retorna sua quantidade de tokens. Parágrafos
    que cabem no alvo são adicionados inteiros; os demais entram por sentença.
    """
    chunks = []
    atual = []

    def trecho(unidades_trecho):
        """Recupera o texto entre a primeira e a última unidade, sem bordas vazias."""
        return texto[unidades_trecho[0].inicio:unidades_trecho[-1].fim].strip()

    def adicionar(novas_unidades):
        """Acumula unidades e fecha o chunk quando a adição ultrapassa o alvo."""
        nonlocal atual
        if atual and contar(trecho(atual + novas_unidades)) > alvo:
            chunks.append(trecho(atual))
            atual = []
        atual.extend(novas_unidades)
        if contar(trecho(atual)) > alvo:
            # Uma unidade indivisível acima do alvo fica sozinha, sem corte.
            chunks.append(trecho(atual))
            atual = []

    grupos = _grupos_com_titulos(unidades)
    for grupo in grupos:
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


def preparar_segmentacao(texto, *, dividir_em_chunks=True, **opcoes):
    """Texto, protocolo resolvido e diagnóstico; não chama provedores.

    ``max_tokens`` continua aceito como alias de ``tokens_alvo``. Para reproduzir
    os cortes antigos, escolha explicitamente ``estrategia='tokens'``.
    ``limite_tokens_entrada`` é um orçamento opcional nesta codificação, já
    descontado o espaço necessário aos prompts; não mede tokens dos provedores.
    """
    if not isinstance(texto, str):
        raise TypeError("texto deve ser uma string.")
    if type(dividir_em_chunks) is not bool:
        raise ValueError("dividir_em_chunks deve ser booleano.")
    config = configuracao_chunks(**opcoes)
    encoder = _encoder(config["encoding_name"])
    contar = lambda t: len(encoder.encode(t, disallowed_special=()))
    alvo = config["tokens_alvo"]
    if not texto.strip():
        chunks = []
    elif not dividir_em_chunks:
        chunks = [texto]
    elif config["estrategia"] == "tokens":
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name=config["encoding_name"], chunk_size=alvo,
            chunk_overlap=config["overlap_tokens"],
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_text(texto)
    else:
        chunks = _agrupar_sentencas(texto, _unidades(texto), alvo, contar)

    diagnostico = []
    for i, chunk in enumerate(chunks, 1):
        unidades = _unidades(chunk)
        tokens = contar(chunk)
        if config["limite_tokens_entrada"] is not None and tokens > config["limite_tokens_entrada"]:
            raise ValueError(
                f"Trecho {i}: {tokens} tokens excedem limite_tokens_entrada="
                f"{config['limite_tokens_entrada']}. O texto não foi truncado."
            )
        longas = sum(not u.titulo and contar(chunk[u.inicio:u.fim]) > alvo for u in unidades)
        diagnostico.append({"trecho": i, "caracteres": len(chunk), "tokens": tokens,
                            "sentencas": sum(not u.titulo for u in unidades),
                            "acima_alvo": tokens > alvo, "sentencas_longas": longas,
                            "texto": chunk})
    versao = (("punkt_pt_referencias_v2" if config["estrategia"] == "sentencas" else "recursive_tokens_v1")
              if dividir_em_chunks else "texto_inteiro")
    return {"chunks": chunks, "config": config if dividir_em_chunks else None,
            "segmentador_versao": versao, "diagnostico": diagnostico,
            "metadados": {"chunks": config if dividir_em_chunks else None,
                          "segmentador_versao": versao,
                          "diagnostico_segmentacao": [
                              {k: v for k, v in d.items() if k != "texto"} for d in diagnostico]}}
