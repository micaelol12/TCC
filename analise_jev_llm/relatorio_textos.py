"""Relatório HTML local das avaliações já calculadas no notebook."""

import base64
from datetime import datetime
from html import escape
import json
from pathlib import Path

import pandas as pd


def _json_html(dados):
    return escape(json.dumps(dados, ensure_ascii=False, indent=2, default=str))


def _parametros_html(dados, prefixo=""):
    linhas = []
    for chave, valor in dados.items():
        nome = f"{prefixo}.{chave}" if prefixo else str(chave)
        if isinstance(valor, dict) and valor:
            linhas.append(_parametros_html(valor, nome))
        else:
            linhas.append(f"<tr><th scope='row'>{escape(nome)}</th>"
                          f"<td><code>{_json_html(valor)}</code></td></tr>")
    return "".join(linhas)


def _tabela_html(tabela):
    if not isinstance(tabela, pd.DataFrame):
        tabela = pd.DataFrame(tabela)
    return ("<div class='tabela'>"
            + tabela.round(3).to_html(index=False, escape=True, na_rep="—", border=0)
            + "</div>")


def _imagem_html(caminho, descricao):
    if not caminho.is_file():
        return ""
    dados = base64.b64encode(caminho.read_bytes()).decode("ascii")
    return f"<img alt='{escape(descricao, quote=True)}' src='data:image/png;base64,{dados}'>"


def salvar_relatorio_textos(resultados, pasta_rodada):
    """Salva resultados_textos.html com parâmetros congelados e recursos embutidos.

    Usa o protocolo salvo na avaliação, sem consultar as configurações atuais do
    notebook e sem chamadas externas. Gráficos e fluxogramas ficam dentro do HTML.
    """
    pasta_rodada = Path(pasta_rodada)
    protocolo = json.loads((pasta_rodada / "protocolo.json").read_text(encoding="utf-8"))
    resultados = list(resultados)
    linhas, paineis = [], []
    for numero, item in enumerate(resultados, start=1):
        original = item["original"]
        erro = item.get("erro")
        linha = {
            "id": item["id"], "grupo": item["grupo"],
            "complexidade": original.get("complexidade"),
            "trechos": len(item["chunks"]), "erro": erro,
        }
        partes = [f"<section id='texto-{numero}'><h2>{escape(item['id'])}</h2>",
                  f"<p><strong>Grupo:</strong> {escape(str(item['grupo']))} · "
                  f"<strong>Complexidade:</strong> {escape(str(original.get('complexidade', '—')))} · "
                  f"<strong>Trechos:</strong> {len(item['chunks'])}</p>",
                  "<details><summary>Texto de entrada e metadados</summary><pre>"
                  + escape(str(original.get("texto", ""))) + "</pre><pre>"
                  + _json_html({k: v for k, v in original.items() if k != "texto"})
                  + "</pre></details>"]
        diagnostico = (item.get("preparacao") or {}).get("diagnostico_segmentacao", [])
        if diagnostico:
            linha["trechos acima do alvo"] = sum(d["acima_alvo"] for d in diagnostico)
            partes.append("<details><summary>Segmentação usada: tokens, sentenças e exceções</summary>"
                          + _tabela_html(diagnostico) + "</details>")
        if erro:
            partes.append(f"<p class='erro'>Avaliação não concluída: {escape(str(erro))}</p>")
        else:
            cobertura = item["cobertura"]
            linha.update({f"índice A — {r['eixo']}": r["índice A"]
                          for r in cobertura.to_dict(orient="records")})
            linha["chamadas LLM"] = sum(r.get("chamadas_llm", 0) for r in item["registros"])
            linha["chamadas JEV evidências"] = sum(
                r.get("chamadas_jev_evidencias", 0) for r in item["registros"])
            partes.extend([
                "<h3>Cobertura e índices</h3>", _tabela_html(cobertura),
                "<h3>Oito valores</h3>", _tabela_html(item["resultado"]["eixos"]),
                _imagem_html(Path(item["pasta"]) / "grafico_8values.png",
                             f"Oito valores de {item['id']}"),
            ])
            for chave, titulo in (("detalhes", "Decisões"), ("evidencias", "Evidências"),
                                   ("auditoria", "Auditoria das evidências")):
                if chave in item:
                    partes.append(f"<details><summary>{titulo}</summary>"
                                  + _tabela_html(item[chave]) + "</details>")
            fluxo = Path(item["pasta"]) / "fluxograma.html"
            if fluxo.is_file():
                partes.append(
                    "<details><summary>Fluxograma interativo</summary>"
                    f"<iframe loading='lazy' sandbox='allow-scripts' "
                    f"title='Fluxograma de {escape(item['id'], quote=True)}' "
                    f"srcdoc='{escape(fluxo.read_text(encoding='utf-8'), quote=True)}'>"
                    "</iframe></details>")
        partes.append("<p><a href='#comparacao'>Voltar à comparação geral</a></p></section>")
        linhas.append(linha)
        paineis.append("".join(partes))

    concluidos = sum(item.get("erro") is None for item in resultados)
    contexto = protocolo.get("contexto", {})
    navegacao = " · ".join(
        f"<a href='#texto-{i}'>{escape(item['id'])}</a>"
        for i, item in enumerate(resultados, start=1))
    conteudo = (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Resultados dos textos</title><style>"
        "*{box-sizing:border-box}body{margin:0;background:#f1f5f9;color:#172033;"
        "font:15px/1.55 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:24px}"
        "header,section{background:white;border:1px solid #dbe3ed;border-radius:12px;"
        "padding:24px;margin-bottom:24px}h1,h2,h3{line-height:1.25;color:#123753}"
        "a{color:#145b91}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f8fafc;"
        "padding:16px;border-radius:6px}code{white-space:pre-wrap;overflow-wrap:anywhere}"
        ".tabela{overflow-x:auto;margin:16px 0}table{border-collapse:collapse;width:100%;"
        "font-size:13px}th,td{padding:9px 12px;text-align:left;border-bottom:1px solid #e2e8f0;"
        "vertical-align:top}thead,table.parametros th{background:#edf4fa}"
        "details{border:1px solid #dbe3ed;padding:12px;margin:12px 0;border-radius:6px}"
        "summary{cursor:pointer;font-weight:600}img{display:block;max-width:100%;height:auto;"
        "margin:16px auto}iframe{width:100%;height:900px;border:0;margin-top:12px}"
        ".erro{background:#fff1f2;color:#9f1239;padding:12px;border-radius:6px}"
        "nav{overflow-wrap:anywhere}@media print{body{background:white}main{padding:0}"
        "section{break-inside:avoid}iframe{display:none}}</style></head><body><main>"
        "<header><h1>Resultados dos textos</h1>"
        f"<p><strong>Rodada:</strong> {escape(str(contexto.get('id', pasta_rodada.name)))}<br>"
        f"<strong>Relatório gerado em:</strong> {escape(datetime.now().astimezone().isoformat(timespec='seconds'))}<br>"
        f"<strong>Textos concluídos:</strong> {concluidos}/{len(resultados)} · "
        f"<strong>Falhas:</strong> {len(resultados) - concluidos}</p>"
        "<h2>Parâmetros usados na execução</h2>"
        "<p>Valores registrados no protocolo da rodada, incluindo modelos, limiares, "
        "segmentação, tentativas e cálculo dos índices.</p>"
        "<div class='tabela'><table class='parametros'><thead><tr><th>Parâmetro</th>"
        "<th>Valor</th></tr></thead><tbody>"
        + _parametros_html(protocolo) + "</tbody></table></div>"
        "<p>Índices e rótulos exploratórios. Ausência de evidência aparece como —; "
        "textos com erro não recebem pontuação. O conjunto não fornece gabarito "
        "ideológico para calcular acurácia.</p></header>"
        "<section id='comparacao'><h2>Comparação geral dos textos</h2>"
        + _tabela_html(linhas)
        + _imagem_html(pasta_rodada / "comparacao.png", "Comparação dos índices por texto e eixo")
        + "<nav aria-label='Resultados por texto'>" + navegacao + "</nav></section>"
        + "".join(paineis) + "</main></body></html>"
    )
    caminho = pasta_rodada / "resultados_textos.html"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho
