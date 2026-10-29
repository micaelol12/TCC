"""Réplica das regras puras validadas no notebook autoritativo."""
import math
import re
import unicodedata
from collections.abc import Mapping
from copy import deepcopy
from .rubrics import AXIS_SPECS
from ..polarity import CONTEXTO_POSICAO_POLITICA, ESCALA_ATUAL, validar_escala, valor_nivel, classe_nivel, NIVEIS_POLARIDADE
CHAVES_NIVEIS = tuple(NIVEIS_POLARIDADE)
MIN_PALAVRAS_EVIDENCIA = 4
MOTIVOS_POLARIDADE = {"empate_nivel", "baixa_confianca_nivel", "direcao_ambigua", "intensidade_ambigua"}
_MARCACAO_MD = re.compile(r"(\*\*|__|<br\s*/?>|^#{1,6}\s+|^>\s?|\|)", re.M)
_RETICENCIAS = re.compile(r"^(\.\.\.|…)\s*|\s*(\.\.\.|…)$")

def criar_questoes_eixo(axis, axis_specs=AXIS_SPECS):
    """Cria a pergunta de relevância; a polaridade é definida pela rubrica ordinal."""
    spec = axis_specs[axis]
    return {
        "instructions": CONTEXTO_POSICAO_POLITICA + f"O trecho contém uma proposta ou posição sobre {spec['name']}?",
        "criteria": {
            "A": f"Sim. Há evidência substantiva sobre {spec['topic']}.",
            "B": f"Não. Não há evidência substantiva sobre {spec['topic']}.",
        },
    }

def criar_rubrica_polaridade_ordinal(axis, axis_specs=AXIS_SPECS, escala=None):
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)
    spec = axis_specs[axis]
    polos = spec["poles"]
    instructions = (CONTEXTO_POSICAO_POLITICA +
        f"Qual situação descreve a posição expressa no trecho sobre {spec['name']}? "
        f"Polo B ({polos['B']['label']}): {polos['B']['description']} "
        f"Polo A ({polos['A']['label']}): {polos['A']['description']} "
        "Considere as posições expressas conforme o contexto da análise, incluindo falas de terceiros e respeitando o sentido de negações e críticas. "
        "Intensidade depende do alcance e da profundidade da mudança proposta, não da retórica "
        "nem da confiança. Não deduza posições por identidade do autor nem informação externa. " + spec["note"])
    niveis = {n.chave: {"valor": n.codigo, "nivel": n.rotulo,
        **escala.rubricas_por_eixo[axis][n.chave].model_dump(mode="json")} for n in escala.niveis}
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

def _normalizar_relevancia_noul_2_polos(resposta, limiar=0.5):
    if not 0.0 <= limiar <= 1.0:
        raise ValueError('limiar deve estar entre 0 e 1.')
    p = float(_score_campo(resposta, 'noul'))
    if not 0.0 <= p <= 1.0:
        raise ValueError('A probabilidade Noul deve estar entre 0 e 1.')
    return {'choice': 'A' if p >= limiar else 'B', 'probabilities': {'A': p, 'B': 1.0 - p}}

def _normalizar_polaridade_ordinal(resposta, relevante, primitiva='score', escala=None, regra_decisao='nivel'):
    """MAP global ou polo primeiro; preserva distribuição e decisão global para auditoria."""
    if regra_decisao not in {'nivel', 'polo_primeiro'}:
        raise ValueError('regra_decisao deve ser nivel ou polo_primeiro.')
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)
    chaves = tuple(n.chave for n in escala.niveis)
    brutas = dict(_score_campo(resposta, 'probabilities'))
    if primitiva == 'score':
        indices = {str(i) for i in range(len(chaves))}
        if {str(k) for k in brutas} != indices or len(brutas) != len(chaves):
            raise ValueError(f'Esperados os índices Score {sorted(indices)}.')
        brutas = {chaves[int(k)]: v for k, v in brutas.items()}
    elif primitiva != 'choice':
        raise ValueError('Primitiva inválida.')
    probabilidades = _score_distribuicao(brutas, chaves)
    maior = max(probabilidades.values())
    vencedores = [k for k, v in probabilidades.items() if math.isclose(v, maior, abs_tol=1e-12, rel_tol=0)]
    selecionado = escala.por_chave[vencedores[0]] if len(vencedores) == 1 else None
    nivel_jev = selecionado.codigo if selecionado else None
    p_a = math.fsum(probabilidades[n.chave] for n in escala.niveis if n.polo == 'A')
    p_b = math.fsum(probabilidades[n.chave] for n in escala.niveis if n.polo == 'B')
    p_0 = probabilidades[escala.centro.chave]
    grupos = {'A': p_a, 'B': p_b, 'C': p_0}
    maior_grupo = max(grupos.values())
    vencedores_grupo = [g for g, p in grupos.items() if math.isclose(p, maior_grupo, abs_tol=1e-12, rel_tol=0)]
    grupo = vencedores_grupo[0] if len(vencedores_grupo) == 1 else None
    desempate_intensidade = False
    if regra_decisao == 'polo_primeiro':
        candidatos = [n for n in escala.niveis if (n.polo or 'C') == grupo]
        maior_no_grupo = max((probabilidades[n.chave] for n in candidatos), default=0)
        vencedores_no_grupo = [n for n in candidatos if math.isclose(probabilidades[n.chave], maior_no_grupo, abs_tol=1e-12, rel_tol=0)]
        # Os códigos são identificadores; a intensidade segue a posição na escala.
        selecionado = min(vencedores_no_grupo, key=lambda n: abs(n.valor - .5), default=None)
        desempate_intensidade = relevante and grupo in ('A', 'B') and len(vencedores_no_grupo) > 1
    nivel = selecionado.codigo if relevante and selecionado else None
    suporte_condicional = (probabilidades[selecionado.chave] / grupos[selecionado.polo or 'C']
                           if selecionado and selecionado.polo is not None else None)
    status = ('sem_evidencia' if not relevante else 'empate' if nivel is None
              else 'sem_posicao' if escala.por_codigo[nivel].polo is None else 'direcional')
    return {
        'nivel': nivel, 'chave_nivel': selecionado.chave if relevante and selecionado else None,
        'nivel_jev_bruto': nivel_jev,
        'regra_decisao': regra_decisao,
        'desempate_intensidade': desempate_intensidade,
        'grupo_mais_provavel': grupo,
        'margem_grupo': _score_margem(grupos),
        'probabilidade_nivel_condicional': suporte_condicional,
        'valor_0_100': None if nivel is None else valor_nivel(nivel, escala),
        'classe': classe_nivel(nivel, escala),
        'probabilities_nivel': probabilidades,
        'probabilities_abc': grupos,
        'p_polo_A': p_a, 'p_polo_B': p_b, 'p_sem_posicao': p_0,
        'margem_direcao': abs(p_a - p_b),
        'nivel_esperado_diagnostico': math.fsum(escala.por_chave[k].codigo * p for k, p in probabilidades.items()),
        'confianca_nivel': _score_probabilidade(_score_campo(resposta, 'confidence'), 'confidence'),
        'status': status, 'escala_id': escala.id, 'escala_versao': escala.versao, 'escala_hash': escala.hash,
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
        primitiva=config["primitiva_polaridade"], escala=config.get("escala"),
        regra_decisao=config.get("regra_decisao", "nivel"),
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
        if config.get("regra_decisao", "nivel") == "polo_primeiro":
            if decisao['margem_grupo'] < config['margem_direcao_minima']:
                motivos.append('direcao_ambigua')
            if (decisao['grupo_mais_provavel'] in ('A', 'B')
                    and (decisao.get('desempate_intensidade', False)
                         or decisao['probabilidade_nivel_condicional'] is None
                         or decisao['probabilidade_nivel_condicional'] < config['confianca_nivel_minima'])):
                motivos.append('intensidade_ambigua')
            return motivos
        if decisao["confianca_nivel"] < config["confianca_nivel_minima"]:
            motivos.append("baixa_confianca_nivel")
        if (decisao["nivel"] is not None and classe_nivel(decisao["nivel"], validar_escala(config.get("escala", ESCALA_ATUAL))) != "C"
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

def decidir_llm(item, texto, original, motivos, modelo, meta, escala=None):
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)
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
        status = "sem_posicao" if escala.por_codigo[nivel].polo is None else "direcional"
    return {
        **decisao_vazia(item.eixo), "relevante": relevante, "nivel": nivel,
        "valor_0_100": None if nivel is None else valor_nivel(nivel, escala),
        "classe": classe_nivel(nivel, escala),
        "status": status, "metodo": "llm_ordinal", "modelo": modelo,
        "evidencia": item.evidencia, "evidencia_verificada": evidencia_ok,
        "resposta_llm": item.model_dump(), "meta_llm": meta,
        "llm_reverteu_relevancia": bool(
            set(motivos) <= MOTIVOS_POLARIDADE and original["relevante"]
            and item.relevante is not True),
    }
