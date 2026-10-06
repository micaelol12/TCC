"""Gera a base de textos longos: planos sintéticos com gabarito e trechos de planos reais.

1. Planos sintéticos (com gabarito). Cada plano tem um perfil: um nível de -2 a 2 por eixo,
   ou o eixo ausente. O texto é montado em rodadas; cada rodada acrescenta um parágrafo de
   cada eixo presente (do nível do perfil) e um parágrafo neutro, em ordem embaralhada. Os
   parágrafos (base_sintetica/paragrafos/*.json) têm ~130-190 palavras, estilo de plano de
   governo, e incluem crítica ao polo oposto, retórica enfática sem mudança de intensidade e
   distratores. Tamanhos aninhados: o texto de r rodadas é prefixo do de r+1. O tamanho
   "diluido" acrescenta 30 parágrafos neutros ao de 6 rodadas, intercalados.
   Gabarito por eixo: nível do perfil (relevante=True); nível 0 = parágrafos de diagnóstico ou
   distratores (relevante=None: as duas respostas são aceitas); ausente = relevante False.

2. Trechos reais (sem gabarito). De cada plano escolhido em tcc/textos_candidatos.json, após a
   mesma limpeza da seção 10.1 do notebook, toma parágrafos consecutivos a partir de 15% do
   documento até atingir cada tamanho-alvo. Os trechos são aninhados (o menor é prefixo do
   maior). Servem para medir acionamento do LLM, latência e estabilidade em texto real.

Uso: python base_sintetica/gerar_base_longa.py   (não faz chamadas de API)
"""

import hashlib
import json
import random
import re
from pathlib import Path

import tiktoken

SEMENTE = 42
PASTA = Path(__file__).parent
RAIZ = PASTA.parent
SAIDA = PASTA / "base_longa.json"
EIXOS = ("economic", "diplomatic", "state", "society")
ENC = tiktoken.get_encoding("cl100k_base")

# Perfis: nível por eixo (None = eixo ausente do texto).
PERFIS = {
    "P1_esquerda_forte":      {"economic": 2, "diplomatic": 1, "state": 1, "society": 2},
    "P2_direita_forte":       {"economic": -2, "diplomatic": -1, "state": -2, "society": -2},
    "P3_centro_esquerda":     {"economic": 1, "diplomatic": 1, "state": 1, "society": 1},
    "P4_centro_direita":      {"economic": -1, "diplomatic": -1, "state": -1, "society": -1},
    "P5_liberal":             {"economic": -2, "diplomatic": 1, "state": 2, "society": 1},
    "P6_nacional_estatista":  {"economic": 2, "diplomatic": -2, "state": -1, "society": -1},
    "P7_sem_posicao":         {"economic": 0, "diplomatic": 0, "state": 0, "society": 0},
    "P8_dois_eixos":          {"economic": 1, "diplomatic": None, "state": -1, "society": None},
}
# Tamanho -> (rodadas, parágrafos neutros extras intercalados).
TAMANHOS_SINTETICOS = {"r1": (1, 0), "r2": (2, 0), "r4": (4, 0), "r6": (6, 0), "diluido": (6, 30)}

# Planos reais (rótulo cego -> candidato) e tamanhos-alvo em tokens.
PLANOS_REAIS = {
    "Plano A": "Lula (PT)",
    "Plano B": "Hertz Dias (PSTU)",
    "Plano C": "ROMEU ZEMA (NOVO)",
    "Plano D": "Flávio Bolsonaro (PL)",
    "Plano E": "Renan Santos (Missão)",
    "Plano F": "Samara Martins (UP)",
}
TAMANHOS_REAIS = [300, 600, 1200, 2500, 5000, 10000, 16000]
INICIO_RELATIVO = 0.15

# Mesma limpeza da seção 10.1 do notebook (limpar_markdown).
RE_IMAGEM = re.compile(r"<!-- Start of picture text -->.*?<!-- End of picture text -->", re.S)
RE_SUMARIO = re.compile(r"^.*\.{5,}.*\d+\s*\|?\s*$", re.M)
RE_QUEBRA_PAGINA = re.compile(r"(?<=[a-zà-úç,;0-9])[ \t]*\n(?:[ \t]*\n)+[ \t]*(?=[a-zà-úç(])")


def limpar_markdown(md):
    md = RE_IMAGEM.sub("", md)
    md = RE_SUMARIO.sub("", md)
    md = RE_QUEBRA_PAGINA.sub(" ", md)
    md = re.sub(r"\*\*|__|<br\s*/?>", "", md)
    md = re.sub(r"^\|?\s*:?-{3,}.*$", "", md, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def n_tokens(texto):
    return len(ENC.encode(texto))


def carregar_paragrafos():
    banco = {}
    for eixo in EIXOS:
        dados = json.loads((PASTA / "paragrafos" / f"{eixo}.json").read_text(encoding="utf-8"))
        assert dados["eixo"] == eixo
        for nivel in (-2, -1, 0, 1, 2):
            banco[(eixo, nivel)] = [p for p in dados["paragrafos"] if p["nivel"] == nivel]
            assert len(banco[(eixo, nivel)]) >= 6, (eixo, nivel)
    neutros = json.loads((PASTA / "paragrafos" / "neutro.json").read_text(encoding="utf-8"))["paragrafos"]
    assert len(neutros) >= 36
    return banco, neutros


def planos_sinteticos():
    banco, neutros = carregar_paragrafos()
    itens = []
    for k, (perfil, niveis) in enumerate(PERFIS.items()):
        rng = random.Random(f"{SEMENTE}-{perfil}")
        presentes = [e for e in EIXOS if niveis[e] is not None]
        # Ordem dos parágrafos de cada eixo e dos neutros, própria do perfil.
        filas = {e: rng.sample(banco[(e, niveis[e])], 6) for e in presentes}
        ordem_neutros = rng.sample(range(len(neutros)), len(neutros))
        rodadas = []
        for r in range(6):
            bloco = [{"tipo": "posicao", "eixo": e, "nivel": niveis[e], "estilo": filas[e][r]["estilo"],
                      "texto": filas[e][r]["texto"]} for e in presentes]
            bloco.append({"tipo": "neutro", "eixo": None, "nivel": None, "estilo": "neutro",
                          "texto": neutros[ordem_neutros[r]]["texto"]})
            rng.shuffle(bloco)
            rodadas.append(bloco)
        for tamanho, (n_rodadas, n_extra) in TAMANHOS_SINTETICOS.items():
            paragrafos = [p for bloco in rodadas[:n_rodadas] for p in bloco]
            if n_extra:
                extras = [{"tipo": "neutro", "eixo": None, "nivel": None, "estilo": "neutro",
                           "texto": neutros[i]["texto"]} for i in ordem_neutros[6:6 + n_extra]]
                # Intercala: um neutro extra a cada parágrafo, mantendo a ordem original.
                misturados = []
                for i in range(max(len(paragrafos), len(extras))):
                    misturados += paragrafos[i:i + 1] + extras[i:i + 1]
                paragrafos = misturados
            gabarito = {e: ({"relevante": False, "nivel": None} if niveis[e] is None else
                            {"relevante": None if niveis[e] == 0 else True, "nivel": niveis[e]})
                        for e in EIXOS}
            itens.append({"id": f"sint-{perfil}-{tamanho}", "fonte": "sintetico", "documento": perfil,
                          "tamanho": tamanho, "texto": "\n\n".join(p["texto"] for p in paragrafos),
                          "gabarito": gabarito, "paragrafos": paragrafos})
    return itens


def trechos_reais():
    planos = {p["candidato"]: p for p in json.loads((RAIZ / "tcc" / "textos_candidatos.json").read_text(encoding="utf-8"))}
    itens = []
    for rotulo, candidato in PLANOS_REAIS.items():
        texto = limpar_markdown(planos[candidato]["md"])
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        inicio = int(INICIO_RELATIVO * len(paragrafos))
        tokens_par = [n_tokens(p) for p in paragrafos]
        for alvo in TAMANHOS_REAIS:
            fim, total = inicio, 0
            while fim < len(paragrafos) and total < alvo:
                total += tokens_par[fim]
                fim += 1
            if total < alvo:
                raise ValueError(f"{candidato}: texto insuficiente para {alvo} tokens.")
            itens.append({"id": f"real-{rotulo.replace(' ', '_')}-{alvo}", "fonte": "real", "documento": rotulo,
                          "candidato": candidato, "arquivo": planos[candidato]["filename"],
                          "tamanho": str(alvo), "paragrafo_inicial": inicio, "paragrafo_final": fim,
                          "texto": "\n\n".join(paragrafos[inicio:fim]), "gabarito": None})
    return itens


def main():
    itens = planos_sinteticos() + trechos_reais()
    for item in itens:
        item["n_tokens"] = n_tokens(item["texto"])
        item["n_palavras"] = len(item["texto"].split())
        item["sha256"] = hashlib.sha256(item["texto"].encode("utf-8")).hexdigest()
    assert len({i["id"] for i in itens}) == len(itens)
    base = {"descricao": __doc__.strip().splitlines()[0], "semente": SEMENTE, "perfis": PERFIS,
            "tamanhos_sinteticos": TAMANHOS_SINTETICOS, "tamanhos_reais": TAMANHOS_REAIS,
            "planos_reais": PLANOS_REAIS, "itens": itens}
    SAIDA.write_text(json.dumps(base, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(itens)} textos gravados em {SAIDA}")
    for fonte in ("sintetico", "real"):
        tamanhos = dict.fromkeys(i["tamanho"] for i in itens if i["fonte"] == fonte)
        for t in tamanhos:
            toks = sorted(i["n_tokens"] for i in itens if i["fonte"] == fonte and i["tamanho"] == t)
            print(f"  {fonte:<9} {t:<8} n={len(toks)}  tokens {toks[0]}–{toks[-1]} (mediana {toks[len(toks) // 2]})")


if __name__ == "__main__":
    main()
