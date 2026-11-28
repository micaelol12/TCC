"""Rubricas compartilhadas por JEV e LLM, obtidas da configuração da análise."""
from ..analysis_defaults import AXIS_SPECS, CONTEXTO_POSICAO_POLITICA, ESCALA_ATUAL
from ..polarity import DefinicaoEixo, validar_escala


def definicao_eixo(axis, axis_specs):
    """Obtém a definição do eixo como dicionário, aceitando o modelo validado ou dados brutos."""
    definicao = axis_specs[axis]

    return definicao.model_dump(mode="json") if isinstance(definicao, DefinicaoEixo) else definicao


def criar_questoes_eixo(axis, axis_specs=AXIS_SPECS, contexto_posicao_politica=CONTEXTO_POSICAO_POLITICA):
    """Cria a pergunta de relevância; a polaridade é definida pela rubrica ordinal."""
    definicao = definicao_eixo(axis, axis_specs)

    return {
        "instructions": contexto_posicao_politica.rstrip() + " " + f"O trecho contém conteúdo substantivo sobre {definicao['name']}, incluindo propostas, ideias, definições ou modelos políticos?",
        "criteria": {
            "A": f"Sim. Há evidência substantiva sobre {definicao['topic']}.",
            "B": f"Não. Não há evidência substantiva sobre {definicao['topic']}.",
        },
    }


def criar_rubrica_polaridade_ordinal(axis, axis_specs=AXIS_SPECS, escala=None, contexto_posicao_politica=CONTEXTO_POSICAO_POLITICA):
    """Monta a rubrica de polaridade com os polos e as âncoras da escala desta execução."""
    # As definições vêm da configuração; a mesma rubrica é usada por JEV e LLM.
    escala = validar_escala(ESCALA_ATUAL if escala is None else escala)

    definicao = definicao_eixo(axis, axis_specs)
    polos = definicao["poles"]

    instructions = (contexto_posicao_politica.rstrip() + " " +
        f"Qual situação caracteriza a proposta, ideia, modelo ou arranjo apresentado no trecho sobre {definicao['name']}? "
        f"Polo B ({polos['B']['label']}): {polos['B']['description']} "
        f"Polo A ({polos['A']['label']}): {polos['A']['description']} "
        "Intensidade depende do alcance e da profundidade da proposta, ideia, modelo ou arranjo caracterizado, não da retórica "
        "nem da confiança. Diferencie as características do objeto descrito da adesão do enunciador. Uma definição com características direcionais não é mera menção temática. Não atribua como defendida uma posição explicitamente rejeitada nem converta automaticamente sua rejeição em defesa do polo oposto. Não deduza posições por identidade do autor nem informação externa. " + definicao["note"])

    niveis = {
        nivel.chave: {
            "valor": nivel.codigo, "nivel": nivel.rotulo,
            **escala.rubricas_por_eixo[axis][nivel.chave].model_dump(mode="json"),
        } for nivel in escala.niveis
    }

    return {"instructions": instructions, "niveis": niveis}
