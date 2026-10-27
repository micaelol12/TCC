"""Avaliação por documento e exportações do notebook, sem chamadas externas."""

import ast
import asyncio
from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from analise_jev_llm.test_passo_a_passo_metricas import NS, decisao, registro
from analise_jev_llm.fluxograma_playground import criar_dados_fluxograma, renderizar_fluxograma


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "Pipeline - Passo a Passo.ipynb"


def carregar_testes():
    ns = {**NS, "Path": Path, "json": json, "deepcopy": deepcopy,
          "re": re, "Mapping": Mapping, "BaseModel": BaseModel,
          "asyncio": asyncio, "TENTATIVAS": 1, "PAUSA_SEGUNDOS": 0,
          "RecursiveCharacterTextSplitter": RecursiveCharacterTextSplitter,
          "criar_dados_fluxograma": criar_dados_fluxograma,
          "renderizar_fluxograma": renderizar_fluxograma}
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    nomes = {"preparar_textos_teste", "salvar_json_teste", "salvar_artefatos_teste",
             "avaliar_textos_teste", "ler_json", "_json_estrito", "classificar_lote",
             "tabela_decisoes", "tabela_evidencias_playground", "tabela_auditoria_evidencias"}
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if source.startswith("RE_IMAGEM") or source.startswith("def dividir_texto_em_chunks_tokens"):
            exec(source, ns)
        for node in ast.parse(source).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in nomes:
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(NOTEBOOK), "exec"), ns)
    # Importa o mesmo leitor sem depender de células que leem planos de governo.
    return ns


class TextosTesteNotebookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = carregar_testes()

    def config(self, tmp):
        return {"arquivo": str(ROOT / "pesquisa_exemplos/textos_teste.json"),
                "grupos": ["textos_pequenos", "textos_grandes"],
                "limpar_markdown": True, "dividir_em_chunks": True,
                "chunks": {"max_tokens": 600, "overlap_tokens": 0,
                           "encoding_name": "cl100k_base"},
                "dpi_grafico": 40, "pasta_saida": tmp}

    def test_prepara_todos_sem_truncar_e_preserva_metadados(self):
        preparados = self.ns["preparar_textos_teste"](self.config("unused"))
        self.assertEqual(len(preparados), 28)
        self.assertEqual(len({p["id"] for p in preparados}), 28)
        self.assertTrue(all(p["erro"] is None for p in preparados))
        maior = preparados[-1]
        self.assertGreater(len(maior["chunks"]), 10)
        self.assertTrue(maior["chunks"][-1].endswith("Resolução nº 23.732/2024."))
        self.assertIn("Tribunal Superior Eleitoral", maior["original"]["fonte"]["nome"])
        self.assertIn("2024-02-27", maior["original"]["data"])

    def test_falha_isolada_e_artefatos_individuais_com_resultados_distintos(self):
        ns = self.ns

        class Pipeline:
            rubricas = {}
            escala = ns["ESCALA_5_NIVEIS"]

            async def classificar(self, texto):
                if texto == "falhar":
                    raise RuntimeError("falha controlada")
                nivel = 2 if texto == "primeiro" else -2
                r = registro(texto, decisao(True, nivel))
                r.update(chamadas_llm=0, motivos_fallback={e: [] for e in ns["AXIS_SPECS"]})
                for etapa in ("eixos", "eixos_jev"):
                    for d in r[etapa].values():
                        d["evidencia"] = ""
                return r

        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            preparados = [
                {"id": f"texto_{i}", "grupo": "grupo", "posicao": i,
                 "original": {"texto": texto, "complexidade": "claro"},
                 "chunks": [texto], "preparacao": {"dividir_em_chunks": False}, "erro": None}
                for i, texto in enumerate(["primeiro", "falhar", "terceiro"], 1)
            ]
            resultados = asyncio.run(ns["avaliar_textos_teste"](
                preparados, Pipeline(), {"id": "rodada"}, self.config(tmp), pasta))
            self.assertEqual([r["erro"] is None for r in resultados], [True, False, True])
            for item, esperado in [(resultados[0], 100), (resultados[2], 0)]:
                cobertura = item["cobertura"].set_index("eixo")
                self.assertEqual(cobertura.loc["economic", "índice A"], esperado)
                self.assertEqual(cobertura.loc["economic", "chunks"], 1)
                for nome in ["cobertura.csv", "valores_8values.csv", "decisoes.csv", "evidencias.csv",
                             "auditoria.csv", "grafico_8values.png", "fluxograma.html", "resultado.json"]:
                    self.assertGreater((item["pasta"] / nome).stat().st_size, 0)
                dados = json.loads((item["pasta"] / "resultado.json").read_text(encoding="utf-8"))
                self.assertEqual(dados["contexto"]["nome"], item["id"])
                self.assertEqual(dados["registros"][0]["texto"], item["original"]["texto"])
                fluxo = item["dados_fluxograma"]
                self.assertEqual(fluxo["cobertura"][0]["índice A"], esperado)
                self.assertIsNone(fluxo["cobertura"][1]["índice A"])
            falha = resultados[1]
            self.assertIsNone(falha["cobertura"])
            self.assertFalse((falha["pasta"] / "resultado.json").exists())
            status = json.loads((falha["pasta"] / "status.json").read_text(encoding="utf-8"))
            self.assertFalse(status["concluido"])
            self.assertIn("falha controlada", status["erro"])
            self.assertIn("falha controlada", (falha["pasta"] / "registros.jsonl").read_text(encoding="utf-8"))

            # A célula de exibição usa os resultados existentes e mantém falhas ausentes.
            ns.update(resultados_testes=resultados, pasta_rodada_testes=pasta,
                      CONFIG_TESTES={**self.config(tmp), "mostrar_detalhes": True,
                                     "mostrar_grafico": True, "mostrar_fluxograma": True})
            cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
            source = "".join(next(c for c in cells if c.get("id") == "testes-exibicao")["source"])
            with patch("IPython.display.display") as mostrar, patch.object(ns["plt"], "show"):
                ns["display"] = mostrar
                exec(source, ns)
            comparacao = ns["comparacao_testes"].set_index("id")
            self.assertEqual(comparacao.loc["texto_1", "índice A — economic"], 100)
            self.assertEqual(comparacao.loc["texto_3", "índice A — economic"], 0)
            self.assertTrue(ns["pd"].isna(comparacao.loc["texto_2", "índice A — economic"]))
            self.assertGreater((pasta / "comparacao.png").stat().st_size, 0)
            self.assertGreater((pasta / "comparacao.csv").stat().st_size, 0)

            # A exportação usa o protocolo da rodada e inclui recursos offline,
            # mesmo se as configurações atuais já tiverem sido alteradas.
            protocolo = {"contexto": {"id": "rodada", "pipeline": {
                "modelo_llm": "modelo-usado", "cascata": {"limiar_noul": 0.7}}},
                "preparacao_e_exibicao": self.config(tmp)}
            (pasta / "protocolo.json").write_text(json.dumps(protocolo), encoding="utf-8")
            ns["CONFIG_PIPELINE_TESTES"] = {"modelo_llm": "modelo-alterado-depois"}
            resultados[0]["original"]["texto"] = "Texto <script>alert('entrada')</script> & fonte"
            source = "".join(next(c for c in cells if c.get("id") == "testes-relatorio-html")["source"])
            with patch("IPython.display.display") as mostrar:
                ns["display"] = mostrar
                exec(source, ns)
            caminho = pasta / "resultados_textos.html"
            self.assertEqual(ns["caminho_relatorio_testes"], caminho)
            html = caminho.read_text(encoding="utf-8")
            self.assertIn("modelo-usado", html)
            self.assertNotIn("modelo-alterado-depois", html)
            self.assertIn("contexto.pipeline.cascata.limiar_noul", html)
            self.assertLess(html.index("Parâmetros usados"), html.index("Comparação geral"))
            self.assertIn("&lt;script&gt;alert", html)
            self.assertNotIn("<script>alert('entrada')</script>", html)
            self.assertIn("data:image/png;base64,", html)
            self.assertIn("srcdoc=", html)
            self.assertIn("Textos concluídos:</strong> 2/3", html)
            self.assertIn("Avaliação não concluída: " + falha["erro"], html)
            self.assertIn("texto_1", html)
            self.assertIn("texto_3", html)


if __name__ == "__main__":
    unittest.main()
