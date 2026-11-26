"""Benchmark LLM direto: integração offline, sem clientes ou chamadas reais."""

import ast
from contextlib import redirect_stdout
from copy import deepcopy
import inspect
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch

import matplotlib

matplotlib.use("Agg")

from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


ROOT = Path(__file__).resolve().parents[1]
TEXT = "Vamos ampliar os serviços públicos de saúde para toda a população."


class FakeLLM:
    model = "llm-simulado"
    ultima_chamada = {"modelo": model, "uso": {"total_tokens": 12}}

    def __init__(self, *, evidence=TEXT, fail=False):
        self.calls = []
        self.evidence, self.fail = evidence, fail

    async def generate(self, prompt, response_schema, instructions=None):
        data = json.loads(prompt)
        self.calls.append((data, instructions))
        if self.fail:
            raise RuntimeError("Falha simulada")
        return response_schema.model_validate({"eixos": [
            {"eixo": axis, "relevante": axis == "economic",
             "nivel": 1 if axis == "economic" else None,
             "evidencia": self.evidence if axis == "economic" else ""}
            for axis in data["rubricas"]]})


class BenchmarkLLMTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ns = carregar_pipeline_notebook()
        self.nb = json.loads((ROOT / "Pipeline.ipynb").read_text(encoding="utf-8"))
        # Configuração e amostra locais; nenhuma célula com APIs é executada aqui.
        exec("".join(self.nb["cells"][92]["source"]), self.ns)
        self.question = self.ns["Question"](
            id=1, question=TEXT, effect=self.ns["Effect"](econ=10, dipl=0, govt=0, scty=0))

    def pipeline(self, llm=None, **options):
        return self.ns["LLMSemJev"](
            llm or FakeLLM(), self.ns["AXIS_SPECS_BENCHMARK"],
            **{**deepcopy(self.ns["CONFIG_PIPELINE_BENCHMARK"]["cascata"]),
               "tentativas_llm": 1, **options})

    async def cell(self, index):
        result = eval(compile("".join(self.nb["cells"][index]["source"]),
                              f"Pipeline.ipynb:cell-{index}", "exec",
                              flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), self.ns)
        if inspect.isawaitable(result):
            await result

    async def test_direct_llm_preserves_prompt_and_counts_four_pairs_for_both_scales(self):
        for scale_name in ("ESCALA_5_NIVEIS", "ESCALA_9_NIVEIS"):
            with self.subTest(scale=scale_name):
                scale = self.ns[scale_name]
                llm = FakeLLM()
                pipeline = self.pipeline(llm, escala=scale)
                cascade = self.ns["CascataJevLLM2Polos"](
                    None, llm, self.ns["AXIS_SPECS_BENCHMARK"], escala=scale,
                    contexto_posicao_politica=pipeline.config["contexto_posicao_politica"])
                record = await pipeline.classificar(TEXT)
                self.assertEqual(len(llm.calls), 1)
                self.assertEqual(llm.calls[0][0], {"texto": TEXT, "rubricas": cascade.rubricas})
                self.assertEqual(llm.calls[0][1], self.ns["instrucoes_escala"](
                    scale, pipeline.config["contexto_posicao_politica"]))
                self.assertEqual(record["chamadas_jev"], 0)
                self.assertEqual(record["chamadas_jev_evidencias"], 0)
                self.assertEqual(record["chamadas_llm_efetivas"], 1)
                self.assertNotIn("eixos_jev", record)
                self.assertEqual(record["eixos_solicitados_llm"], list(cascade.rubricas))
                self.assertEqual(record["eixos_encaminhados"], [])
                self.assertIsNone(record["modelos_configurados"]["jev"])
                self.assertEqual(record["escala_hash"], scale.hash)
                details, summary = self.ns["avaliar_registros"]([self.question], [record])
                self.assertEqual(len(details), 4)
                self.assertEqual(set(details["etapa"]), {"eixos_llm"})
                self.assertTrue(details["acerto conjunto"].all())
                self.assertEqual(summary["pares"].sum(), 4)

    async def test_factory_requires_only_maritaca_and_disables_all_jev_checks(self):
        config = deepcopy(self.ns["CONFIG_PIPELINE_BENCHMARK"])
        config["cascata"].update(
            usar_fallback=False, semantic_evidence_check=True, jev_evidence_search=True)
        original = deepcopy(config)
        llm = FakeLLM()
        jev = Mock(side_effect=AssertionError("JEV não deve ser criado"))
        with patch.dict(self.ns["os"].environ, {"MARITACA_API_KEY": "simulada"}, clear=True), \
             patch.dict(self.ns, MaritacaClient=Mock(return_value=llm), AsyncTypeSafeClient=jev,
                        enriquecer_evidencias=AsyncMock(side_effect=AssertionError("Sem JEV"))):
            pipeline = self.ns["criar_pipeline_benchmark"](
                "llm", config, self.ns["AXIS_SPECS_BENCHMARK"])
            await pipeline.classificar(TEXT)
            jev.assert_not_called()
            self.ns["enriquecer_evidencias"].assert_not_called()
            self.assertIsNone(pipeline.jev_client)
            self.assertFalse(pipeline.config["semantic_evidence_check"])
            self.assertFalse(pipeline.config["jev_evidence_search"])
            self.assertFalse(pipeline.config["usar_fallback"])
            self.ns["MaritacaClient"].assert_called_once_with(
                api_key="simulada", model=config["modelo_llm"],
                temperature=config["temperatura_llm"], timeout=config["timeout_llm_s"], max_retries=0)
        self.assertEqual(config, original)

    async def test_failures_and_invalid_evidence_are_abstentions_without_jev(self):
        llm = FakeLLM(fail=True)
        with patch.object(self.ns["asyncio"], "sleep", new_callable=AsyncMock) as sleep:
            record = await self.pipeline(llm, tentativas_llm=2).classificar(TEXT)
        self.assertEqual(record["chamadas_llm_efetivas"], 2)
        self.assertEqual(len(llm.calls), 2)
        sleep.assert_awaited_once_with(1)
        self.assertTrue(all(d["status"] == "falha_llm" for d in record["eixos"].values()))
        details, _ = self.ns["avaliar_registros"]([self.question], [record])
        self.assertEqual(details["abstenção"].sum(), 4)
        self.assertEqual(details["acerto conjunto"].sum(), 0)
        invalid = await self.pipeline(FakeLLM(evidence="Uma frase que não aparece no texto original.")).classificar(TEXT)
        self.assertEqual(invalid["eixos"]["economic"]["status"], "evidencia_nao_verificada")
        self.assertIsNone(invalid["eixos"]["economic"]["relevante"])

    async def test_real_benchmark_cells_export_mode_records_metrics_and_diagnostic(self):
        llm = FakeLLM()
        with TemporaryDirectory() as directory:
            # Replica a disposição <raiz>/tcc/questions.json sem ler dados externos.
            self.ns.update(
                QUESTIONS=[self.question], QUESTIONS_PATH=str(Path(directory) / "tcc" / "questions.json"),
                TENTATIVAS=1, PAUSA_SEGUNDOS=0, display=lambda *args: None)
            self.ns["CONFIG_BENCHMARK"].update(modo="llm", executar=True)
            with patch.dict(self.ns["os"].environ, {"MARITACA_API_KEY": "simulada"}, clear=True), \
                 patch.dict(self.ns, MaritacaClient=Mock(return_value=llm),
                            AsyncTypeSafeClient=Mock(side_effect=AssertionError("Sem JEV")),
                            load_dotenv=Mock()), redirect_stdout(io.StringIO()) as output:
                await self.cell(100)
                await self.cell(102)
                with patch.object(self.ns["plt"], "show"):
                    await self.cell(104)
                    await self.cell(105)
                self.ns["plt"].close("all")
                folder = self.ns["pasta_benchmark"]
                stage = self.ns["ETAPA_METRICAS_BENCHMARK"]
                # Trocar o modo sem refazer a prévia é impedido antes de criar clientes.
                self.ns["CONFIG_BENCHMARK"]["modo"] = "cascata"
                with self.assertRaisesRegex(ValueError, "Reexecute a prévia"):
                    await self.cell(102)
            manifest = json.loads((folder / "manifesto.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["modo"], "llm")
            self.assertEqual(manifest["benchmark"]["modo"], "llm")
            self.assertIsNone(manifest["modelos_configurados"]["jev"])
            self.assertFalse(manifest["config_efetiva"]["semantic_evidence_check"])
            wrappers = [json.loads(line) for line in (folder / "benchmark.jsonl").read_text(encoding="utf-8").splitlines()]
            record = wrappers[0]["registro"]
            self.assertEqual(record["modo"], "llm")
            self.assertEqual(record["chamadas_jev"], 0)
            self.assertEqual(record["tentativas_lote"], 1)
            self.assertNotIn("tentativas_jev", record)
            details = self.ns["pd"].read_csv(folder / "benchmark_detalhes.csv")
            self.assertEqual(set(details["etapa"]), {"eixos_llm"})
            self.assertEqual(len(details), 4)
            self.assertEqual(stage, "eixos_llm")
            self.assertIn("Acertos conjuntos: 4/4", output.getvalue())
            self.assertEqual(len(llm.calls), 1)

    async def test_cascade_mode_still_creates_only_needed_providers(self):
        config = deepcopy(self.ns["CONFIG_PIPELINE_BENCHMARK"])
        with patch.dict(self.ns["os"].environ, {"TYPESAFE_API_KEY": "simulada"}, clear=True), \
             patch.dict(self.ns, AsyncTypeSafeClient=Mock(), MaritacaClient=Mock()):
            config["cascata"]["usar_fallback"] = False
            pipeline = self.ns["criar_pipeline_benchmark"](
                "cascata", config, self.ns["AXIS_SPECS_BENCHMARK"])
            self.assertIsNone(pipeline.llm)
            self.ns["MaritacaClient"].assert_not_called()
            self.ns["AsyncTypeSafeClient"].assert_called_once()
            config["cascata"]["usar_fallback"] = True
            with self.assertRaisesRegex(ValueError, "MARITACA_API_KEY"):
                self.ns["criar_pipeline_benchmark"]("cascata", config, self.ns["AXIS_SPECS_BENCHMARK"])
        with patch.dict(self.ns["os"].environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "MARITACA_API_KEY") as error:
                self.ns["criar_pipeline_benchmark"]("llm", config, self.ns["AXIS_SPECS_BENCHMARK"])
            self.assertNotIn("TYPESAFE_API_KEY", str(error.exception))
        with self.assertRaisesRegex(ValueError, "modo deve ser"):
            self.ns["criar_pipeline_benchmark"]("inválido", config, self.ns["AXIS_SPECS_BENCHMARK"])


if __name__ == "__main__":
    unittest.main()
