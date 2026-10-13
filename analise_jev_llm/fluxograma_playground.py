"""Inspeção local dos registros da cascata, sem inferências nem dependências web."""

import html
import json
import math
from collections.abc import Mapping
from pathlib import Path


EIXOS = ("economic", "diplomatic", "state", "society")


def _json_local(valor):
    """Copia os dados e converte escalares pandas/numpy para JSON estrito."""
    if isinstance(valor, Mapping):
        return {str(k): _json_local(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_local(v) for v in valor]
    if isinstance(valor, float):
        return valor if math.isfinite(valor) else None
    if valor is None or isinstance(valor, (str, int, bool)):
        return valor
    if hasattr(valor, "item"):
        return _json_local(valor.item())
    raise TypeError(f"Tipo não serializável no fluxograma: {type(valor).__name__}")


def criar_dados_fluxograma(registros, cobertura, *, contexto=None, rubricas=None,
                           resultado_8values=None):
    """Congela uma execução. Os parâmetros por chunk vêm do próprio registro.

    `contexto` deve conter somente os parâmetros públicos da execução (nunca o
    cliente de API ou credenciais). A cobertura é a tabela calculada pelo notebook;
    o visualizador não reclassifica nem recalcula índices ou intervalos.
    """
    registros = list(registros)
    if not registros:
        raise ValueError("Execute a análise do playground antes de gerar o fluxograma.")
    for i, registro in enumerate(registros, 1):
        if not isinstance(registro.get("texto"), str):
            raise ValueError(f"Chunk {i} não contém o texto analisado.")
        for etapa in ("eixos_jev", "eixos"):
            if set(registro.get(etapa, {})) != set(EIXOS):
                raise ValueError(f"Chunk {i}: {etapa} deve conter os quatro eixos.")
    linhas = cobertura.to_dict(orient="records") if hasattr(cobertura, "to_dict") else list(cobertura)
    if len(linhas) != len(EIXOS) or {r["eixo"] for r in linhas} != set(EIXOS):
        raise ValueError("A cobertura deve conter exatamente uma linha por eixo.")
    if any("chunks" in r and r["chunks"] != len(registros) for r in linhas):
        raise ValueError("A cobertura e os registros devem pertencer à mesma execução (quantidade de chunks).")
    return _json_local({
        "registros": registros, "cobertura": linhas,
        "contexto": contexto or {}, "rubricas": rubricas or {},
        "resultado_8values": resultado_8values or {},
    })


def renderizar_fluxograma(dados):
    """HTML autônomo, utilizável offline; texto analisado nunca vira código HTML."""
    serializado = json.dumps(_json_local(dados), ensure_ascii=False, allow_nan=False)
    # Impede que texto, evidências ou rubricas encerrem o elemento <script>.
    serializado = (serializado.replace("&", "\\u0026").replace("<", "\\u003c")
                  .replace(">", "\\u003e").replace("\u2028", "\\u2028")
                  .replace("\u2029", "\\u2029"))
    template = Path(__file__).with_name("fluxograma_playground.html").read_text(encoding="utf-8")
    return template.replace("__DADOS_FLUXOGRAMA__", serializado)


def exibir_fluxograma(dados, caminho=None, *, altura=1080):
    """Mostra um iframe isolado e, opcionalmente, salva o mesmo painel em HTML."""
    from IPython.display import HTML, display

    pagina = renderizar_fluxograma(dados)
    if caminho is not None:
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(pagina, encoding="utf-8")
    display(HTML(
        '<iframe title="Fluxograma interativo da execução JEV e LLM" '
        'sandbox="allow-scripts" style="width:100%;border:1px solid #dce3ec;'
        f'border-radius:14px;height:{int(altura)}px" srcdoc="{html.escape(pagina, quote=True)}">'
        '</iframe>'
    ))
    return caminho
