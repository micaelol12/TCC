"""Verificações locais da cascata: clientes simulados, sem inferência remota."""

import ast
import asyncio
import importlib.util
import json
import math
import sys
import time
import types
import unittest
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# O runtime de diagnóstico pode não ter o SDK. Nesse caso, somente os
# construtores de perguntas são substituídos; o algoritmo e o Pydantic são reais.
SDK_SIMULADO = importlib.util.find_spec("typesafe_sdk") is None
if SDK_SIMULADO:
    sdk = types.ModuleType("typesafe_sdk")

    class PerguntaSimulada:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    sdk.Choice = sdk.Noul = sdk.Score = PerguntaSimulada
    sys.modules["typesafe_sdk"] = sdk

from analise_jev_llm.pipeline_score import (
    CascataJevLLMScore, RespostaLLMScore,
    executar_benchmark_jev_llm_score, processar_documento_com_jev_score,
)

nb = json.loads((ROOT / "TCC.ipynb").read_text(encoding="utf-8"))
ns = {"pd": pd, "time": time, "Mapping": Mapping,
      "Callable": Callable, "Sequence": Sequence}
nomes = {"AXIS_SPECS", "EFFECT_TO_AXIS", "NIVEIS_SCORE", "calcular_margem",
         "esperado_pelo_efeito", "_choice_e_probabilidades", "executar_benchmark_8values"}
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    source = "".join(cell.get("source", []))
    if not any(n in source for n in nomes):
        continue
    try:
        tree = ast.parse(source)
    except SyntaxError:
        continue  # Células de execução contêm await/IPython.
    for node in tree.body:
        nome = getattr(node, "name", None)
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            nome = node.targets[0].id
        if nome in nomes:
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<notebook-defs>", "exec"), ns)

SPECS, NIVEIS = ns["AXIS_SPECS"], ns["NIVEIS_SCORE"]


def resposta_jev(*, relevante=True, nivel=3, confidence=1.0):
    answers = {}
    for eixo in SPECS:
        answers[f"{eixo}_relevancia"] = {
            "noul": 0.95 if relevante else 0.05,
            "choice": "A" if relevante else "B",
            "probabilities": {"A": 0.95 if relevante else 0.05,
                              "B": 0.05 if relevante else 0.95},
        }
        answers[f"{eixo}_polaridade"] = {
            "score": nivel, "confidence": confidence,
            "probabilities": {str(i): float(i == nivel) for i in range(5)},
        }
    return {"model": "jev-simulado", "answers": answers}


class ClienteJEVSimulado:
    def __init__(self, resposta):
        self.resposta, self.chamadas = resposta, []

    async def system_one(self, *, state, questions):
        self.chamadas.append((state, questions))
        return self.resposta(state) if callable(self.resposta) else self.resposta


class ClienteLLMSimulado:
    model = "llm-simulado"

    def __init__(self, resposta=None):
        self.resposta, self.chamadas = resposta, []

    async def generate(self, prompt, response_schema):
        self.chamadas.append(prompt)
        payload = json.loads(prompt.split("\n", 1)[1])
        self.payload = payload
        dados = self.resposta(payload) if self.resposta else {
            "eixos": [{"eixo": e, "relevante": True, "nivel": 2,
                       "evidencia": payload["texto"]} for e in payload["rubricas"]]
        }
        return response_schema.model_validate(dados)


def pipeline(resposta, llm=None, **kwargs):
    return CascataJevLLMScore(
        ClienteJEVSimulado(resposta), llm or ClienteLLMSimulado(), SPECS, NIVEIS, **kwargs)


class TestPipelineScore(unittest.IsolatedAsyncioTestCase):
    async def test_posicao_moderada_certa_nao_vira_extremo(self):
        p = pipeline(resposta_jev())
        r = await p.classificar("texto")
        self.assertEqual(r["chamadas_llm"], 0)
        self.assertEqual(r["eixos"]["economic"]["score_8values"], 75)
        self.assertEqual(r["eixos"]["economic"]["confidence_score"], 1)

    async def test_irrelevante_seguro_ignora_score_incerto(self):
        p = pipeline(resposta_jev(relevante=False, confidence=0))
        r = await p.classificar("texto")
        self.assertEqual(r["chamadas_llm"], 0)
        self.assertIsNone(r["eixos"]["economic"]["score_8values"])

    async def test_relevancia_ambigua_encaminha_todos_em_uma_chamada(self):
        resposta = resposta_jev()
        for eixo in SPECS:
            resposta["answers"][f"{eixo}_relevancia"]["noul"] = 0.45
        p = pipeline(resposta)
        r = await p.classificar("texto")
        self.assertEqual(r["chamadas_llm"], 1)
        self.assertEqual(len(p.llm.chamadas), 1)
        for eixo in SPECS:
            self.assertFalse(r["eixos_jev"][eixo]["relevante"])
            self.assertEqual(r["eixos"][eixo]["score_8values"], 50)
            self.assertIsNone(r["eixos"][eixo]["confidence_score"])
            self.assertIsNone(r["eixos"][eixo]["probabilities_score"])
            self.assertEqual(p.llm.payload["rubricas"][eixo], p.rubricas[eixo])

    async def test_llm_recebe_so_eixo_encaminhado_e_preserva_demais(self):
        resposta = resposta_jev()
        resposta["answers"]["economic_polaridade"]["confidence"] = 0.1
        p = pipeline(resposta)
        r = await p.classificar("texto")
        self.assertEqual(r["eixos_encaminhados"], ["economic"])
        self.assertEqual(set(p.llm.payload["rubricas"]), {"economic"})
        self.assertEqual(r["eixos"]["state"], r["eixos_jev"]["state"])

    async def test_fallback_pode_abster_sem_preencher_centro(self):
        def abster(payload):
            return {"eixos": [{"eixo": e, "relevante": True, "nivel": None,
                               "evidencia": payload["texto"]} for e in payload["rubricas"]]}
        p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(abster))
        r = await p.classificar("texto")
        self.assertIsNone(r["eixos"]["economic"]["score_8values"])
        self.assertEqual(r["eixos"]["economic"]["status"], "posicao_indeterminada")

    async def test_schema_rejeita_nivel_sem_relevancia(self):
        with self.assertRaises(ValueError):
            RespostaLLMScore.model_validate({"eixos": [
                {"eixo": "economic", "relevante": False, "nivel": 2, "evidencia": ""}]})

    async def test_llm_nao_pode_responder_eixo_extra(self):
        def extra(payload):
            return {"eixos": [{"eixo": "outro", "relevante": False,
                               "nivel": None, "evidencia": ""}]}
        p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(extra))
        with self.assertRaisesRegex(ValueError, "exatamente"):
            await p.classificar("texto")

    async def test_evidencia_ausente_abstem_sem_interromper(self):
        def inventar(payload):
            return {"eixos": [{"eixo": e, "relevante": True, "nivel": 3,
                               "evidencia": "citação inexistente"} for e in payload["rubricas"]]}
        p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(inventar))
        r = await p.classificar("texto")
        self.assertEqual(r["chamadas_llm"], 1)
        for eixo in SPECS:
            d = r["eixos"][eixo]
            self.assertEqual(d["status"], "evidencia_nao_verificada")
            self.assertFalse(d["evidencia_verificada"])
            self.assertIsNone(d["relevante"])
            self.assertIsNone(d["score_8values"])
            self.assertEqual(d["classe"], "C")
            self.assertEqual(d["resposta_llm"]["nivel"], 3)
            self.assertEqual(r["eixos_jev"][eixo]["score_8values"], 75)

    async def test_citacao_aceita_formato_unicode_caixa_e_aspas(self):
        def citar(payload):
            return {"eixos": [{"eixo": e, "relevante": True, "nivel": 3,
                               "evidencia": '“AMPLIAR OS SERVIÇOS PÚBLICOS”'}
                              for e in payload["rubricas"]]}
        p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(citar))
        r = await p.classificar("Defendo ampliar\u00a0os serviços\npúblicos.")
        for d in r["eixos"].values():
            self.assertTrue(d["evidencia_verificada"])
            self.assertEqual(d["score_8values"], 75)

    async def test_citacao_invalida_nao_descarta_outros_eixos_validos(self):
        def citar(payload):
            return {"eixos": [{"eixo": e, "relevante": True, "nivel": 3,
                               "evidencia": "texto inventado" if e == "economic" else payload["texto"]}
                              for e in payload["rubricas"]]}
        p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(citar))
        r = await p.classificar("Defendo ampliar os serviços públicos.")
        self.assertEqual(r["eixos"]["economic"]["status"], "evidencia_nao_verificada")
        for eixo in ("diplomatic", "state", "society"):
            self.assertEqual(r["eixos"][eixo]["score_8values"], 75)

    async def test_citacao_vazia_ou_parafrase_nao_valida_posicao(self):
        for evidencia in ("", '""', "ampliar os serviços privados", "ampliar ... públicos"):
            def citar(payload, evidencia=evidencia):
                return {"eixos": [{"eixo": e, "relevante": True, "nivel": 3,
                                   "evidencia": evidencia} for e in payload["rubricas"]]}
            p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(citar))
            r = await p.classificar("Defendo ampliar os serviços públicos.")
            self.assertIsNone(r["eixos"]["economic"]["score_8values"])

    async def test_benchmark_continua_e_registra_evidencia_invalida(self):
        def citar(payload):
            return {"eixos": [{"eixo": e, "relevante": True, "nivel": 3,
                               "evidencia": "inexistente" if payload["texto"] == "texto 1" else payload["texto"]}
                              for e in payload["rubricas"]]}
        p = pipeline(resposta_jev(confidence=0), ClienteLLMSimulado(citar))
        perguntas = [types.SimpleNamespace(
            id=i, question=f"texto {i}", effect=types.SimpleNamespace(
                model_dump=lambda: {"econ": 10, "dipl": 10, "govt": 10, "scty": 10}))
            for i in (1, 2)]
        r = await executar_benchmark_jev_llm_score(
            perguntas, p, ns["executar_benchmark_8values"], pausa_segundos=0)
        self.assertEqual(len(r["detalhes"]), 8)
        invalidos = r["detalhes"].loc[r["detalhes"]["id"] == 1]
        self.assertTrue((invalidos["status final"] == "evidencia_nao_verificada").all())
        self.assertTrue(invalidos["score 8values"].isna().all())
        self.assertFalse(invalidos["passou"].any())
        self.assertTrue(r["detalhes"].loc[r["detalhes"]["id"] == 2, "passou"].all())
        self.assertEqual(r["desempenho"].iloc[0]["eixos com evidência não verificada"], 4)
        self.assertEqual(len(p.jev_client.chamadas), 2)

    async def test_noul_e_choice_recebem_mesmas_definicoes(self):
        p_noul = pipeline(resposta_jev())
        p_choice = pipeline(resposta_jev(), tipo_relevancia="choice")
        self.assertEqual(p_noul.rubricas, p_choice.rubricas)
        c_noul = p_noul.perguntas["economic_relevancia"].criteria
        c_choice = p_choice.perguntas["economic_relevancia"].criteria
        self.assertEqual(c_noul["true"], c_choice["A"])
        self.assertEqual(c_noul["false"], c_choice["B"])
        r = await p_choice.classificar("texto")
        self.assertEqual(r["eixos"]["economic"]["score_8values"], 75)

    async def test_arredondamento_e_distribuicao_invalida(self):
        resposta = resposta_jev()
        for eixo in SPECS:
            resposta["answers"][f"{eixo}_polaridade"]["probabilities"]["3"] = 0.99
        r = await pipeline(resposta).classificar("texto")
        self.assertAlmostEqual(sum(r["eixos"]["economic"]["probabilities_score"].values()), 1)
        resposta["answers"]["economic_polaridade"]["probabilities"]["3"] = 0.5
        with self.assertRaisesRegex(ValueError, "soma"):
            await pipeline(resposta).classificar("texto")

    async def test_documento_inclui_centro_e_informa_ausencia(self):
        def responder(texto):
            r = resposta_jev(relevante=False)
            if texto != "sem tema":
                r["answers"]["economic_relevancia"]["noul"] = 0.95
                nivel = 3 if texto == "redistribuição" else 2
                r["answers"]["economic_polaridade"] = {
                    "score": nivel, "confidence": 1,
                    "probabilities": {str(i): float(i == nivel) for i in range(5)}}
            return r
        p = pipeline(responder, usar_fallback=False)
        r = await processar_documento_com_jev_score(
            "documento", p, separar_em_chunks=lambda _: ["redistribuição", "equilíbrio", "sem tema"])
        self.assertEqual(r["scores"]["equality"], 62.5)
        self.assertEqual(r["scores"]["wealth"], 37.5)
        self.assertIsNone(r["scores"]["peace"])
        linha = r["cobertura"].set_index("eixo").loc["economic"]
        self.assertAlmostEqual(linha["cobertura"], 2 / 3)
        self.assertEqual(len(r["chunks"]), 3)

    async def test_benchmark_preserva_correcoes_e_pioras_sem_segunda_chamada_jev(self):
        def responder(texto):
            r = resposta_jev(relevante=False)
            r["answers"]["economic_relevancia"]["noul"] = 0.95
            r["answers"]["economic_polaridade"] = {
                "score": 0.3, "confidence": 0.75,
                "probabilities": {"0": .7, "1": .3, "2": 0, "3": 0, "4": 0}}
            return r
        def responder_llm(payload):
            return {"eixos": [{"eixo": "economic", "relevante": True, "nivel": 3,
                               "evidencia": payload["texto"]}]}
        p = pipeline(responder, ClienteLLMSimulado(responder_llm), confianca_score_minima=.9)
        perguntas = [types.SimpleNamespace(
            id=i, question=f"texto {i}", effect=types.SimpleNamespace(
                model_dump=lambda efeito=efeito: {"econ": efeito, "dipl": 0, "govt": 0, "scty": 0}))
            for i, efeito in [(1, 10), (2, -10)]]
        r = await executar_benchmark_jev_llm_score(
            perguntas, p, ns["executar_benchmark_8values"], pausa_segundos=0)
        self.assertEqual(len(r["detalhes"]), 8)
        self.assertEqual(len(p.jev_client.chamadas), 2)
        self.assertEqual(len(p.llm.chamadas), 2)
        self.assertEqual(r["detalhes"]["fallback corrigiu"].sum(), 1)
        self.assertEqual(r["detalhes"]["fallback piorou"].sum(), 1)
        acionados = r["detalhes"].loc[r["detalhes"]["LLM ativado no eixo"]]
        self.assertTrue(acionados["margem polaridade"].isna().all())

    async def test_limites_invalidos_rejeitados(self):
        for valor in (-.1, 1.1, math.nan):
            with self.assertRaises(ValueError):
                pipeline(resposta_jev(), confianca_score_minima=valor)


if __name__ == "__main__":
    print("SDK simulado:", SDK_SIMULADO, "— sem chamadas à API")
    unittest.main(verbosity=2)
