"""Regras puras extraídas do notebook de pesquisa local."""
from __future__ import annotations
import math
import re
import unicodedata
from collections.abc import Mapping
from copy import deepcopy
from .rubrics import AXIS_SPECS

NIVEIS_POLARIDADE = {"polo_B_forte": -2, "polo_B_moderado": -1, "sem_posicao": 0, "polo_A_moderado": 1, "polo_A_forte": 2}
CHAVES_NIVEIS = tuple(NIVEIS_POLARIDADE)

def criar_questoes_eixo(axis, axis_specs=AXIS_SPECS):
    """Cria a pergunta de relevância; a polaridade é definida pela rubrica ordinal."""
    spec = axis_specs[axis]
    return {
        "instructions": f"O trecho contém uma proposta ou posição sobre {spec['name']}?",
        "criteria": {
            "A": f"Sim. Há evidência substantiva sobre {spec['topic']}.",
            "B": f"Não. Não há evidência substantiva sobre {spec['topic']}.",
        },
    }

def criar_rubrica_polaridade_ordinal(axis, axis_specs=AXIS_SPECS):
    """Rubrica ordinal de 5 níveis, comum ao JEV e ao LLM."""
    spec = axis_specs[axis]
    polo_b, polo_a = spec["poles"]["B"], spec["poles"]["A"]
    rotulo_b, rotulo_a = polo_b["label"], polo_a["label"]
    texto_b = " ".join(polo_b["description"].split())
    texto_a = " ".join(polo_a["description"].split())
    instructions = (
        f"Qual situação descreve a posição defendida pelo texto sobre {spec['name']}? "
        f"Os dois polos são: polo B ({rotulo_b}): {texto_b} Polo A ({rotulo_a}): {texto_a} "
        "Considere somente posições efetivamente defendidas pelo texto. Diferencie posições "
        "defendidas de posições apenas citadas, negadas ou criticadas. A intensidade depende do "
        "alcance e da profundidade da mudança proposta, não da ênfase retórica nem da certeza com "
        "que o texto se expressa. Não deduza a posição com base na identidade do autor, partido, "
        "organização ou qualquer informação externa ao próprio texto. " + spec["note"]
    )
    rotulos = {
        "polo_B_forte": f"Polo B ({rotulo_b}), forte",
        "polo_B_moderado": f"Polo B ({rotulo_b}), moderado",
        "sem_posicao": "Sem posição entre os polos",
        "polo_A_moderado": f"Polo A ({rotulo_a}), moderado",
        "polo_A_forte": f"Polo A ({rotulo_a}), forte",
    }
    niveis = {
        chave: {"nivel": rotulos[chave], **deepcopy(spec["intensity_anchors"][chave])}
        for chave in CHAVES_NIVEIS
    }
    return {"instructions": instructions, "niveis": niveis}


def _score_campo(objeto, nome):
    return objeto[nome] if isinstance(objeto, Mapping) else getattr(objeto, nome)

def _score_probabilidade(valor, nome):
    valor = float(valor)
    if not math.isfinite(valor) or not 0 <= valor <= 1:
        raise ValueError(f"{nome} deve estar entre 0 e 1; recebido {valor}.")
    return valor

def _score_distribuicao(valores, chaves):
    probabilidades = {
        str(k): _score_probabilidade(v, f"probabilidade {k}")
        for k, v in valores.items()
    }
    if set(probabilidades) != set(chaves):
        raise ValueError(f"Esperadas as probabilidades {list(chaves)}.")
    total = math.fsum(probabilidades.values())
    if total <= 0 or abs(total - 1.0) > 0.03:
        raise ValueError(f"Distribuição inválida: soma={total}; {probabilidades}.")
    return {k: v / total for k, v in probabilidades.items()}


def _score_margem(distribuicao):
    valores = sorted(distribuicao.values(), reverse=True)
    return valores[0] - valores[1]

def _score_classe(distribuicao):
    maior = max(distribuicao.values())
    vencedores = [
        k for k, p in distribuicao.items()
        if math.isclose(p, maior, rel_tol=0, abs_tol=1e-12)
    ]
    return vencedores[0] if len(vencedores) == 1 else "C"


def _normalizar_polaridade_ordinal(resposta, relevante, primitiva='score'):
    """Converte a resposta do JEV no nível mais provável (-2..2) e em métricas auxiliares."""
    brutas = dict(_score_campo(resposta, 'probabilities'))
    if primitiva == 'score':
        if {int(k) for k in brutas} != set(range(len(CHAVES_NIVEIS))):
            raise ValueError(f'Esperados os níveis 0 a 4 do Score. Recebido: {brutas}')
        brutas = {CHAVES_NIVEIS[int(k)]: v for k, v in brutas.items()}
    probabilidades = _score_distribuicao(brutas, CHAVES_NIVEIS)
    chave = _score_classe(probabilidades)  # 'C' em empate exato entre níveis
    nivel_jev = None if chave == 'C' else NIVEIS_POLARIDADE[chave]
    nivel = nivel_jev if relevante else None
    p_a = probabilidades['polo_A_moderado'] + probabilidades['polo_A_forte']
    p_b = probabilidades['polo_B_moderado'] + probabilidades['polo_B_forte']
    p_0 = probabilidades['sem_posicao']
    if not relevante:
        status = 'sem_evidencia'
    elif nivel is None:
        status = 'empate'
    elif nivel == 0:
        status = 'sem_posicao'
    else:
        status = 'direcional'
    return {
        'nivel': nivel,
        'nivel_jev_bruto': nivel_jev,  # nível mesmo quando o eixo é irrelevante (diagnóstico de prior)
        'valor_0_100': None if nivel is None else 50.0 + 25.0 * nivel,
        'classe': 'C' if nivel in (None, 0) else ('A' if nivel > 0 else 'B'),
        'probabilities_nivel': probabilidades,
        'probabilities_abc': {'A': p_a, 'B': p_b, 'C': p_0},
        'p_polo_A': p_a, 'p_polo_B': p_b, 'p_sem_posicao': p_0,
        'margem_direcao': abs(p_a - p_b),
        # Só diagnóstico: não usar como intensidade (jev-1.13 desaconselha interpolar níveis).
        'nivel_esperado_diagnostico': math.fsum(NIVEIS_POLARIDADE[k] * p for k, p in probabilidades.items()),
        'confianca_nivel': _score_probabilidade(_score_campo(resposta, 'confidence'), 'confidence'),
        'status': status,
    }


def decidir_jev(eixo, respostas, config):
    resposta_rel = respostas[f"{eixo}_relevancia"]
    if config["tipo_relevancia"] == "noul":
        rel = _normalizar_relevancia_noul_2_polos(
            resposta_rel, limiar=config["limiar_noul"],
        )
    else:
        escolha = _score_campo(resposta_rel, "choice")
        if escolha not in {"A", "B"}:
            raise ValueError("Choice de relevância deve retornar A ou B.")
        rel = {
            "choice": escolha,
            "probabilities": _score_distribuicao(
                _score_campo(resposta_rel, "probabilities"), ("A", "B")),
        }
    relevante = rel["choice"] == "A"
    posicao = _normalizar_polaridade_ordinal(
        respostas[f"{eixo}_polaridade"], relevante,
        primitiva=config["primitiva_polaridade"],
    )
    return {
        "eixo": eixo, "relevante": relevante,
        "probabilities_relevancia": rel["probabilities"],
        "margem_relevancia": _score_margem(rel["probabilities"]),
        **posicao,
        "metodo": "jev_ordinal", "modelo": None, "evidencia": None,
        "evidencia_verificada": None, "resposta_llm": None,
        "llm_reverteu_relevancia": False, "erro_llm": None, "meta_llm": None,
    }


def motivos_fallback(decisao, config):
    motivos = []
    if decisao["margem_relevancia"] < config["margem_relevancia_minima"]:
        motivos.append("relevancia_ambigua")
    if decisao["relevante"]:
        if decisao["nivel"] is None:
            motivos.append("empate_nivel")
        if decisao["confianca_nivel"] < config["confianca_nivel_minima"]:
            motivos.append("baixa_confianca_nivel")
        if (decisao["nivel"] not in (None, 0)
                and decisao["margem_direcao"] < config["margem_direcao_minima"]):
            motivos.append("direcao_ambigua")
    return motivos


def _score_normalizar_citacao(texto):
    """Normaliza apresentação preservando palavras, acentos e pontuação."""
    texto = unicodedata.normalize("NFKC", texto).translate(str.maketrans({
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "–": "-", "—": "-", "\u00ad": None, "\u200b": None, "\ufeff": None,
    }))
    return " ".join(texto.split()).casefold()

_MARCACAO_MD = re.compile(r"(\*\*|__|<br\s*/?>|^#{1,6}\s+|^>\s?|\|)", re.M)

_RETICENCIAS = re.compile(r"^(\.\.\.|…)\s*|\s*(\.\.\.|…)$")

MIN_PALAVRAS_EVIDENCIA = 4

def _sem_markdown(texto):
    return _MARCACAO_MD.sub(" ", texto)


def _score_evidencia_confere(texto, evidencia, min_palavras=MIN_PALAVRAS_EVIDENCIA):
    """Trecho contínuo do texto, ignorando marcação Markdown e escapes do JSON do prompt.

    Paráfrases, omissões internas e citações com menos de `min_palavras` palavras são recusadas.
    """
    citacao = evidencia.replace("\\n", " ").replace('\\"', '"')
    citacao = _score_normalizar_citacao(_sem_markdown(citacao)).strip(" \"'.,;:")
    citacao = _RETICENCIAS.sub("", citacao).strip(" \"'")
    if len(citacao.split()) < min_palavras:
        return False
    return citacao in _score_normalizar_citacao(_sem_markdown(texto))


def decisao_vazia(eixo):
    """Campos de uma decisão sem probabilidades (LLM ou falha)."""
    return {
        "eixo": eixo, "relevante": None,
        "probabilities_relevancia": None, "margem_relevancia": None,
        "nivel": None, "nivel_jev_bruto": None, "valor_0_100": None, "classe": "C",
        "probabilities_nivel": None, "probabilities_abc": None,
        "p_polo_A": None, "p_polo_B": None, "p_sem_posicao": None,
        "margem_direcao": None, "nivel_esperado_diagnostico": None,
        "confianca_nivel": None, "status": None, "metodo": None, "modelo": None,
        "evidencia": None, "evidencia_verificada": None, "resposta_llm": None,
        "llm_reverteu_relevancia": False, "erro_llm": None, "meta_llm": None,
    }


MOTIVOS_POLARIDADE = {"empate_nivel", "baixa_confianca_nivel", "direcao_ambigua"}


def decidir_llm(item, texto, original, motivos, modelo, meta):
    evidencia_ok = (_score_evidencia_confere(texto, item.evidencia)
                    if item.relevante is True else None)
    relevante = None if evidencia_ok is False else item.relevante
    nivel = None if evidencia_ok is False else item.nivel
    if evidencia_ok is False:
        status = "evidencia_nao_verificada"
    elif relevante is None:
        status = "relevancia_indeterminada"
    elif not relevante:
        status = "sem_evidencia"
    elif nivel is None:
        status = "posicao_indeterminada"
    else:
        status = "sem_posicao" if nivel == 0 else "direcional"
    return {
        **decisao_vazia(item.eixo), "relevante": relevante, "nivel": nivel,
        "valor_0_100": None if nivel is None else 50.0 + 25.0 * nivel,
        "classe": "C" if nivel in (None, 0) else ("A" if nivel > 0 else "B"),
        "status": status, "metodo": "llm_ordinal", "modelo": modelo,
        "evidencia": item.evidencia, "evidencia_verificada": evidencia_ok,
        "resposta_llm": item.model_dump(), "meta_llm": meta,
        "llm_reverteu_relevancia": bool(
            set(motivos) <= MOTIVOS_POLARIDADE and original["relevante"]
            and item.relevante is not True),
    }
