"""Leitura e normalização das probabilidades devolvidas pelos provedores."""
import math
from collections.abc import Mapping


def ler_campo_resposta(objeto, nome):
    """Lê campos de respostas representadas por mapeamentos ou objetos do SDK."""
    return objeto[nome] if isinstance(objeto, Mapping) else getattr(objeto, nome)


def validar_probabilidade(valor, nome):
    """Converte o valor em float e exige uma probabilidade finita entre zero e um."""
    valor = float(valor)
    if not math.isfinite(valor) or not 0 <= valor <= 1:
        raise ValueError(f"{nome} deve estar entre 0 e 1; recebido {valor}.")
    return valor


def normalizar_distribuicao(valores, chaves):
    """Valida as chaves e a soma, corrigindo apenas pequenos arredondamentos do provedor."""
    probabilidades = {
        str(chave): validar_probabilidade(probabilidade, f"probabilidade {chave}")
        for chave, probabilidade in valores.items()
    }
    if set(probabilidades) != set(chaves):
        raise ValueError(f"Esperadas as probabilidades {list(chaves)}.")

    total = math.fsum(probabilidades.values())

    if total <= 0 or abs(total - 1.0) > 0.03:
        raise ValueError(f"Distribuição inválida: soma={total}; {probabilidades}.")
    # Tolera pequeno arredondamento do provedor e normaliza a soma para 1.
    return {chave: probabilidade / total for chave, probabilidade in probabilidades.items()}


def margem_distribuicao(distribuicao):
    """Mede a diferença entre as duas maiores probabilidades da distribuição."""
    valores = sorted(distribuicao.values(), reverse=True)
    return valores[0] - valores[1]


def classe_mais_provavel(distribuicao):
    """Retorna a classe vencedora ou C quando as maiores probabilidades empatam."""
    vencedores = chaves_mais_provaveis(distribuicao)
    return vencedores[0] if len(vencedores) == 1 else "C"


def chaves_mais_provaveis(distribuicao):
    """Lista todas as alternativas máximas, com tolerância para diferenças numéricas."""
    maior_probabilidade = max(distribuicao.values())
    return [
        chave for chave, probabilidade in distribuicao.items()
        if math.isclose(probabilidade, maior_probabilidade, rel_tol=0, abs_tol=1e-12)
    ]
