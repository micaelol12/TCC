"""Offline cl100k_base encoding; the vocabulary is packaged with this API."""
from functools import lru_cache
from pathlib import Path

import tiktoken
from tiktoken.load import load_tiktoken_bpe


@lru_cache(maxsize=1)
def encoder():
    """Carrega e mantém em cache o tokenizador a partir do vocabulário distribuído com a API."""
    # O vocabulário acompanha a API: não há download durante a requisição.
    vocabulary = Path(__file__).with_name("cl100k_base.tiktoken")

    ranks = load_tiktoken_bpe(str(vocabulary), expected_hash="223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7")

    return tiktoken.Encoding(
        name="cl100k_base_local",
        pat_str=r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s""",
        mergeable_ranks=ranks,
        special_tokens={"<|endoftext|>": 100257, "<|fim_prefix|>": 100258, "<|fim_middle|>": 100259, "<|fim_suffix|>": 100260, "<|endofprompt|>": 100276},
    )


def split_text(text: str, *, max_tokens: int, chunk_tokens: int = 600,
               strategy: str = "tokens") -> tuple[list[str], int]:
    """Valida o limite total e divide o texto pela estratégia de tokens ou sentenças."""
    if strategy not in {"sentencas", "tokens"} or type(chunk_tokens) is not int or chunk_tokens <= 0:
        raise ValueError("invalid_segmentation")

    tokenizer = encoder()

    tokens = tokenizer.encode(text, disallowed_special=())

    if len(tokens) > max_tokens:
        raise ValueError("token_limit")

    if strategy == "sentencas":
        chunks = split_by_sentences(text, tokenizer, chunk_tokens)
    else:
        chunks = split_by_tokens(tokens, tokenizer, chunk_tokens)
    return chunks, len(tokens)


def split_by_sentences(text, tokenizer, chunk_tokens):
    """Agrupa sentenças por alvo de tokens e recupera os cortes no texto original."""
    from .sentences import _agrupar_sentencas, _unidades

    # chunk_tokens é um alvo: uma sentença indivisível pode ultrapassá-lo.
    def count_tokens(value):
        """Conta tokens sem tratar sequências especiais do texto como comandos do tokenizador."""
        return len(tokenizer.encode(value, disallowed_special=()))

    grouped = _agrupar_sentencas(text, _unidades(text), chunk_tokens, count_tokens)

    return _restore_original_chunks(text, grouped)


def _restore_original_chunks(text: str, grouped: list[str]) -> list[str]:
    """Recupera os chunks no texto original, incluindo espaços e quebras de linha.

    Os grupos chegam sem espaços nas bordas. Seus inícios definem os cortes
    para que a concatenação dos chunks reconstrua exatamente o texto recebido.
    """
    starts = []
    offset = 0

    for chunk in grouped:
        # Avança a busca para localizar corretamente até trechos repetidos.
        start = text.index(chunk, offset)
        starts.append(start)
        offset = start + len(chunk)

    if not starts:
        return [text] if text else []

    boundaries = [0, *starts[1:], len(text)]
    intervals = list(zip(boundaries, boundaries[1:]))

    return [text[start:end] for start, end in intervals]


def split_by_tokens(tokens, tokenizer, chunk_tokens):
    """Divide os tokens preservando caracteres UTF-8 completos nas fronteiras dos trechos."""
    chunks = []
    start = 0
    total_tokens = len(tokens)

    while start < total_tokens:
        end = min(start + chunk_tokens, total_tokens)
        chunk, end = _decode_token_chunk(tokens, tokenizer, start, end)
        chunks.append(chunk)
        start = end

    return chunks


def _decode_token_chunk(tokens, tokenizer, start, end):
    """Decodifica um trecho e retorna seu texto e a posição final ajustada.

    Um token pode conter apenas parte dos bytes de um caractere. Se necessário,
    inclui tokens seguintes até completar o UTF-8, preservando acentos e símbolos.
    A posição retornada indica onde o próximo chunk deve começar.
    """
    selected_tokens = tokens[start:end]
    encoded_chunk = b"".join(tokenizer.decode_single_token_bytes(token) for token in selected_tokens)
    total_tokens = len(tokens)

    while end < total_tokens:
        try:
            encoded_chunk.decode("utf-8")
            break
        except UnicodeDecodeError:
            encoded_chunk += tokenizer.decode_single_token_bytes(tokens[end])
            end += 1

    return encoded_chunk.decode("utf-8"), end
