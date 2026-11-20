"""Preservação dos corpos JSON do JEV, sem chamadas externas."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import httpx2
import matplotlib
from typesafe_sdk import SystemOneResponse

matplotlib.use("Agg")

from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


TEXTO = "Nacionalização e estatização do sistema monetário, financeiro e bancário."


class JevHTTP:
    def __init__(self, ns):
        self.ns, self.payloads = ns, []

    async def system_one(self, *, questions, **kwargs):
        answers = {}
        for nome, pergunta in questions.items():
            if nome.endswith("_exists"):
                answers[nome] = {"type": "noul", "noul": 0.88}
                continue
            chaves = list(pergunta.criteria)
            if nome.endswith("_relevancia"):
                escolha = "A" if nome.startswith("economic_") else "B"
            elif nome.endswith("_polaridade"):
                escolha = (self.ns["ESCALA_9_NIVEIS"].niveis[-1].chave
                           if nome.startswith("economic_") else "sem_posicao")
            else:
                escolha = "S000" if nome.endswith("_where") else "sustenta"
            answers[nome] = {
                "type": "choice", "choice": escolha, "confidence": 0.96,
                # Soma aproximada: a aplicação normaliza, o corpo bruto deve manter .99.
                "probabilities": {k: 0.99 if k == escolha else 0.0 for k in chaves},
                "campo_futuro": {"preservar": True},
            }
        payload = {"model": "jev-simulado", "answers": answers,
                   "usage": {"input_tokens": 123, "output_tokens": 12},
                   "campo_api_nao_modelado": {"chamada": len(self.payloads) + 1}}
        self.payloads.append(deepcopy(payload))
        return SystemOneResponse.from_http_response(httpx2.Response(200, json=payload))


class RespostasBrutasTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = carregar_pipeline_notebook()

    def pipeline(self, jev, *, evidencias=False):
        return self.ns["CascataJevLLM2Polos"](
            jev, None, self.ns["AXIS_SPECS"], escala=self.ns["ESCALA_9_NIVEIS"],
            primitiva_polaridade="choice", usar_fallback=False,
            jev_evidence_search=evidencias, semantic_evidence_check=evidencias,
        )

    async def test_corpo_http_completo_e_evidencias_chegam_aos_dois_arquivos(self):
        jev = JevHTTP(self.ns)
        pipeline = self.pipeline(jev, evidencias=True)
        preparado = {"id": "texto_001", "grupo": "teste", "posicao": 1,
                     "original": {"texto": TEXTO}, "chunks": [TEXTO],
                     "preparacao": {}, "erro": None}
        with tempfile.TemporaryDirectory() as tmp:
            resultados = await self.ns["avaliar_textos_teste"](
                [preparado], pipeline, {"id": "simulado"}, {"dpi_grafico": 30}, Path(tmp))
            self.assertIsNone(resultados[0]["erro"])
            pasta = Path(tmp) / "texto_001"
            agregado = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            linha = json.loads((pasta / "registros.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(len(jev.payloads), 3)
            for registro in (agregado["registros"][0], linha["registro"]):
                self.assertEqual(registro["origem_resposta_jev_bruta"], "http")
                self.assertEqual(registro["resposta_jev_bruta"], jev.payloads[0])
                brutas = registro["respostas_jev_evidencias_brutas"]
                self.assertEqual([r["etapa"] for r in brutas], ["search", "semantic"])
                self.assertEqual([r["origem"] for r in brutas], ["http", "http"])
                self.assertEqual([r["resposta"] for r in brutas], jev.payloads[1:])
                self.assertEqual(registro["eixos_jev"]["economic"]["nivel"], 4)
                self.assertEqual(registro["eixos_jev"]["economic"]["p_polo_A"], 1.0)
                self.assertEqual(registro["chamadas_jev_evidencias"], 2)

    async def test_sem_evidencias_e_sem_acumular_respostas_entre_textos(self):
        jev = JevHTTP(self.ns)
        pipeline = self.pipeline(jev)
        primeiro = await pipeline.classificar(TEXTO)
        segundo = await pipeline.classificar("Outra frase sobre estatização dos bancos.")
        self.assertEqual(len(jev.payloads), 2)
        self.assertEqual(primeiro["resposta_jev_bruta"], jev.payloads[0])
        self.assertEqual(segundo["resposta_jev_bruta"], jev.payloads[1])
        self.assertEqual(primeiro["respostas_jev_evidencias_brutas"], [])
        self.assertEqual(segundo["respostas_jev_evidencias_brutas"], [])

    async def test_clientes_sem_http_sao_identificados_e_copiados(self):
        resposta = {"model": "simulado", "answers": {"economic": {"score": 4}}}
        captura = self.ns["_resposta_bruta_jev"](resposta)
        self.assertEqual(captura, {"origem": "mapping", "resposta": resposta})
        resposta["answers"]["economic"]["score"] = 0
        self.assertEqual(captura["resposta"]["answers"]["economic"]["score"], 4)

        jev = JevHTTP(self.ns)
        sdk_http = await jev.system_one(questions=self.pipeline(jev).perguntas)
        sdk_local = SystemOneResponse.model_validate(sdk_http.model_dump(mode="json"))
        captura_sdk = self.ns["_resposta_bruta_jev"](sdk_local)
        self.assertEqual(captura_sdk["origem"], "sdk")
        self.assertEqual(captura_sdk["resposta"], sdk_local.model_dump(mode="json"))
        self.assertNotIn("campo_api_nao_modelado", captura_sdk["resposta"])


if __name__ == "__main__":
    unittest.main()
