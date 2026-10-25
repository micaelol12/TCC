"""Offline cl100k_base encoding; the vocabulary is packaged with this API."""
from functools import lru_cache
from pathlib import Path
import tiktoken
from tiktoken.load import load_tiktoken_bpe


@lru_cache(maxsize=1)
def encoder():
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
    if strategy not in {"sentencas", "tokens"} or type(chunk_tokens) is not int or chunk_tokens <= 0:
        raise ValueError("invalid_segmentation")
    tokenizer = encoder()
    tokens = tokenizer.encode(text, disallowed_special=())
    if len(tokens) > max_tokens:
        raise ValueError("token_limit")
    if strategy == "sentencas":
        from .sentences import _agrupar_sentencas, _unidades
        count = lambda value: len(tokenizer.encode(value, disallowed_special=()))
        grouped = _agrupar_sentencas(text, _unidades(text), chunk_tokens, count)
        # Preserve the exact submitted text, including whitespace between chunks,
        # so evidence offsets and report reconstruction continue to work.
        starts = []
        offset = 0
        for chunk in grouped:
            start = text.index(chunk, offset)
            starts.append(start)
            offset = start + len(chunk)
        if not starts:
            return ([text] if text else []), len(tokens)
        boundaries = [0, *starts[1:], len(text)]
        return [text[a:b] for a, b in zip(boundaries, boundaries[1:])], len(tokens)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_tokens, len(tokens))
        raw = b"".join(tokenizer.decode_single_token_bytes(token) for token in tokens[start:end])
        while end < len(tokens):
            try:
                raw.decode("utf-8")
                break
            except UnicodeDecodeError:
                raw += tokenizer.decode_single_token_bytes(tokens[end])
                end += 1
        chunks.append(raw.decode("utf-8"))
        start = end
    return chunks, len(tokens)
