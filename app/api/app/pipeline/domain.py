"""Regras de decisão da análise, com paridade verificada contra o notebook."""
import math

from ..analysis_defaults import ESCALA_ATUAL
from ..polarity import classe_nivel, validar_escala, valor_nivel
from .probabilities import (
    chaves_mais_provaveis, ler_campo_resposta,
    margem_distribuicao, normalizar_distribuicao, validar_probabilidade,
)
from .quotes import evidencia_literal_confere

MOTIVOS_POLARIDADE = {"empate_nivel", "baixa_confianca_nivel", "direcao_ambigua", "intensidade_ambigua"}


def normalizar_relevancia_noul(resposta, limiar=0.5):
    """Converte a probabilidade Noul em relevância binária pelo limiar informado."""
    if not 0.0 <= limiar <= 1.0:
        raise ValueError("limiar deve estar entre 0 e 1.")
    probabilidade_relevancia = float(ler_campo_resposta(resposta, "noul"))
    if not 0.0 <= probabilidade_relevancia <= 1.0:
        raise ValueError("A probabilidade Noul deve estar entre 0 e 1.")
    return {
        "choice": "A" if probabilidade_relevancia >= limiar else "B",
        "probabilities": {"A": probabilidade_relevancia, "B": 1.0 - probabilidade_relevancia},
    }


def normalizar_relevancia_choice(resposta):
    """Valida a escolha de relevância e normaliza as probabilidades de sim e não."""
    escolha = ler_campo_resposta(resposta, "choice")
    if escolha not in {"A", "B"}:
        raise ValueError("Choice de relevância deve retornar A ou B.")
    return {
        "choice": escolha,
        "probabilities": normalizar_distribuicao(ler_campo_resposta(resposta, "probabilities"), ("A", "B")),
    }


def probabilidades_por_nivel(resposta, primitiva, escala):
    """Converte índices Score ou chaves Choice para os níveis da escala configurada."""
    chaves_niveis = tuple(nivel.chave for nivel in escala.niveis)
    probabilidades_brutas = dict(ler_campo_resposta(resposta, "probabilities"))
    # Score usa índices; Choice já devolve as chaves configuradas na escala.
    if primitiva == "score":
        indices_esperados = {str(indice) for indice in range(len(chaves_niveis))}
        if {str(chave) for chave in probabilidades_brutas} != indices_esperados or len(probabilidades_brutas) != len(chaves_niveis):
            raise ValueError(f"Esperados os índices Score {sorted(indices_esperados)}.")
        probabilidades_brutas = {
            chaves_niveis[int(indice)]: probabilidade
            for indice, probabilidade in probabilidades_brutas.items()
        }
    elif primitiva != "choice":
        raise ValueError("Primitiva inválida.")
    return normalizar_distribuicao(probabilidades_brutas, chaves_niveis)


def agrupar_probabilidades_por_polo(probabilidades, escala):
    """Soma as probabilidades dos polos A e B e mantém a massa do centro em C."""
    return {
        "A": math.fsum(probabilidades[nivel.chave] for nivel in escala.niveis if nivel.polo == "A"),
        "B": math.fsum(probabilidades[nivel.chave] for nivel in escala.niveis if nivel.polo == "B"),
        "C": probabilidades[escala.centro.chave],
    }


def selecionar_nivel_global(probabilidades, escala):
    """Retorna o nível com maior probabilidade, ou None quando há empate."""
    chaves_vencedoras = chaves_mais_provaveis(probabilidades)
    return escala.por_chave[chaves_vencedoras[0]] if len(chaves_vencedoras) == 1 else None


def selecionar_grupo_politico(probabilidades_grupos):
    """Seleciona o grupo A, B ou C apenas quando existe um vencedor único."""
    grupos_vencedores = chaves_mais_provaveis(probabilidades_grupos)
    return grupos_vencedores[0] if len(grupos_vencedores) == 1 else None


def _niveis_do_grupo(escala, grupo):
    """Filtra os níveis do polo A, B ou do centro, representado pelo grupo C."""
    niveis = escala.niveis
    return [nivel for nivel in niveis if (nivel.polo or "C") == grupo]


def _niveis_mais_provaveis(probabilidades, candidatos):
    """Retorna os candidatos de maior probabilidade, incluindo empates numéricos."""
    probabilidades_candidatos = [probabilidades[nivel.chave] for nivel in candidatos]
    maior_probabilidade = max(probabilidades_candidatos, default=0)
    return [
        nivel for nivel in candidatos
        if math.isclose(probabilidades[nivel.chave], maior_probabilidade, abs_tol=1e-12, rel_tol=0)
    ]


def _nivel_mais_proximo_do_centro(niveis):
    """Escolhe o nível mais próximo de 0,5 ou retorna None se não houver níveis."""
    # A intensidade segue a posição na escala, e não o código numérico do nível.
    return min(niveis, key=lambda nivel: abs(nivel.valor - .5), default=None)


def selecionar_nivel_no_grupo(probabilidades, escala, grupo):
    """Escolhe o nível do grupo e resolve empate pela intensidade mais próxima do centro."""
    candidatos = _niveis_do_grupo(escala, grupo)
    vencedores = _niveis_mais_provaveis(probabilidades, candidatos)
    nivel_selecionado = _nivel_mais_proximo_do_centro(vencedores)
    empate_no_grupo = len(vencedores) > 1
    return nivel_selecionado, empate_no_grupo


def probabilidade_condicional_nivel(nivel_selecionado, probabilidades, probabilidades_grupos):
    """Calcula a probabilidade do nível dentro do polo; o centro não tem essa medida."""
    if nivel_selecionado is None or nivel_selecionado.polo is None:
        return None
    return probabilidades[nivel_selecionado.chave] / probabilidades_grupos[nivel_selecionado.polo]


def status_polaridade(relevante, nivel, escala):
    """Distingue ausência de evidência, empate, centro e posição direcional."""
    if not relevante:
        return "sem_evidencia"
    if nivel is None:
        return "empate"
    return "sem_posicao" if escala.por_codigo[nivel].polo is None else "direcional"


def normalizar_polaridade_ordinal(resposta, relevante, primitiva="score", escala=None, regra_decisao="nivel"):
    """Seleciona por nível global ou por polo, preservando ambos nos diagnósticos."""
    if regra_decisao not in {"nivel", "polo_primeiro"}:
        raise ValueError("regra_decisao deve ser nivel ou polo_primeiro.")
    
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)
    probabilidades = probabilidades_por_nivel(resposta, primitiva, escala)
    nivel_global = selecionar_nivel_global(probabilidades, escala)
    probabilidades_grupos = agrupar_probabilidades_por_polo(probabilidades, escala)
    grupo_selecionado = selecionar_grupo_politico(probabilidades_grupos)
    nivel_selecionado = nivel_global
    desempate_intensidade = False
    
    if regra_decisao == "polo_primeiro":
        nivel_selecionado, empate_no_grupo = selecionar_nivel_no_grupo(probabilidades, escala, grupo_selecionado)
        desempate_intensidade = relevante and grupo_selecionado in ("A", "B") and empate_no_grupo

    nivel = nivel_selecionado.codigo if relevante and nivel_selecionado else None
    
    return {
        "nivel": nivel,
        "chave_nivel": nivel_selecionado.chave if relevante and nivel_selecionado else None,
        "nivel_jev_bruto": nivel_global.codigo if nivel_global else None,
        "regra_decisao": regra_decisao,
        "desempate_intensidade": desempate_intensidade,
        "grupo_mais_provavel": grupo_selecionado,
        "margem_grupo": margem_distribuicao(probabilidades_grupos),
        "probabilidade_nivel_condicional": probabilidade_condicional_nivel(nivel_selecionado, probabilidades, probabilidades_grupos),
        "valor_0_100": None if nivel is None else valor_nivel(nivel, escala),
        "classe": classe_nivel(nivel, escala),
        "probabilities_nivel": probabilidades,
        "probabilities_abc": probabilidades_grupos,
        "p_polo_A": probabilidades_grupos["A"],
        "p_polo_B": probabilidades_grupos["B"],
        "p_sem_posicao": probabilidades_grupos["C"],
        "margem_direcao": abs(probabilidades_grupos["A"] - probabilidades_grupos["B"]),
        "nivel_esperado_diagnostico": math.fsum(
            escala.por_chave[chave].codigo * probabilidade for chave, probabilidade in probabilidades.items()
        ),
        "confianca_nivel": validar_probabilidade(ler_campo_resposta(resposta, "confidence"), "confidence"),
        "status": status_polaridade(relevante, nivel, escala),
        "escala_id": escala.id, "escala_versao": escala.versao, "escala_hash": escala.hash,
    }


def decidir_jev(eixo, respostas, config):
    """Combina relevância e polaridade do JEV em uma decisão com diagnósticos por eixo."""
    # A alternativa A da relevância significa "sim", não o polo político A.
    resposta_relevancia = respostas[f"{eixo}_relevancia"]
    relevancia = (
        normalizar_relevancia_noul(resposta_relevancia, limiar=config["limiar_noul"])
        if config["tipo_relevancia"] == "noul" else normalizar_relevancia_choice(resposta_relevancia)
    )
    relevante = relevancia["choice"] == "A"
    polaridade = normalizar_polaridade_ordinal(
        respostas[f"{eixo}_polaridade"], relevante,
        primitiva=config["primitiva_polaridade"], escala=config.get("escala"),
        regra_decisao=config.get("regra_decisao", "nivel"),
    )
    return {
        "eixo": eixo, "relevante": relevante,
        "probabilities_relevancia": relevancia["probabilities"],
        "margem_relevancia": margem_distribuicao(relevancia["probabilities"]),
        **polaridade,
        "metodo": "jev_ordinal", "modelo": None, "evidencia": None,
        "evidencia_verificada": None, "resposta_llm": None,
        "llm_reverteu_relevancia": False, "erro_llm": None, "meta_llm": None,
    }


def motivos_revisao_polo_primeiro(decisao, config):
    """Sinaliza direção ou intensidade ambígua conforme a regra de polo primeiro."""
    motivos = []
    if decisao["margem_grupo"] < config["margem_direcao_minima"]:
        motivos.append("direcao_ambigua")
    if decisao["grupo_mais_provavel"] in ("A", "B"):
        intensidade_ambigua = (
            decisao.get("desempate_intensidade", False)
            or decisao["probabilidade_nivel_condicional"] is None
            or decisao["probabilidade_nivel_condicional"] < config["confianca_nivel_minima"]
        )
        if intensidade_ambigua:
            motivos.append("intensidade_ambigua")
    return motivos


def motivos_revisao_nivel_global(decisao, config):
    """Sinaliza baixa confiança ou direção ambígua na seleção global do nível."""
    motivos = []
    if decisao["confianca_nivel"] < config["confianca_nivel_minima"]:
        motivos.append("baixa_confianca_nivel")
    if decisao["nivel"] is not None:
        escala = validar_escala(config.get("escala", ESCALA_ATUAL))
        if classe_nivel(decisao["nivel"], escala) != "C" and decisao["margem_direcao"] < config["margem_direcao_minima"]:
            motivos.append("direcao_ambigua")
    return motivos


def motivos_fallback(decisao, config):
    """Sinaliza revisão sem modificar a decisão nem os limiares estritos."""
    motivos = []
    if decisao["margem_relevancia"] < config["margem_relevancia_minima"]:
        motivos.append("relevancia_ambigua")
    if not decisao["relevante"]:
        return motivos
    if decisao["nivel"] is None:
        motivos.append("empate_nivel")
    if config.get("regra_decisao", "nivel") == "polo_primeiro":
        return motivos + motivos_revisao_polo_primeiro(decisao, config)
    return motivos + motivos_revisao_nivel_global(decisao, config)


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


def status_decisao_llm(relevante, nivel, evidencia_verificada, escala):
    """Determina o estado da decisão LLM considerando a conferência literal da evidência."""
    if evidencia_verificada is False:
        return "evidencia_nao_verificada"
    if relevante is None:
        return "relevancia_indeterminada"
    if not relevante:
        return "sem_evidencia"
    if nivel is None:
        return "posicao_indeterminada"
    return "sem_posicao" if escala.por_codigo[nivel].polo is None else "direcional"


def decidir_llm(item, texto, original, motivos, modelo, meta, escala=None):
    """Converte a resposta LLM em decisão e invalida posições cuja evidência não confere."""
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)

    evidencia_verificada = evidencia_literal_confere(texto, item.evidencia) if item.relevante is True else None

    relevante = None if evidencia_verificada is False else item.relevante

    nivel = None if evidencia_verificada is False else item.nivel

    status = status_decisao_llm(relevante, nivel, evidencia_verificada, escala)

    return {
        **decisao_vazia(item.eixo), "relevante": relevante, "nivel": nivel,
        "valor_0_100": None if nivel is None else valor_nivel(nivel, escala),
        "classe": classe_nivel(nivel, escala),
        "status": status, "metodo": "llm_ordinal", "modelo": modelo,
        "evidencia": item.evidencia, "evidencia_verificada": evidencia_verificada,
        "resposta_llm": item.model_dump(), "meta_llm": meta,
        "llm_reverteu_relevancia": bool(
            set(motivos) <= MOTIVOS_POLARIDADE and original["relevante"]
            and item.relevante is not True),
    }
