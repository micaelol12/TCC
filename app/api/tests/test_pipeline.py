import asyncio
import unittest
from types import SimpleNamespace

from app.pipeline.aggregation import aggregate
from app.pipeline.domain import motivos_fallback
from app.pipeline.segmentation import split_text
from app.pipeline.strategies import JEV_CONFIG, classify_chunk, jev_decisions
from app.pipeline.validation import validate_answer

AXES = ("economic", "diplomatic", "state", "society")
TEXT = "Vamos ampliar programas de transferência de renda para famílias pobres."


def answers(confidence=0.8):
    return {key: value for axis in AXES for key, value in {
        f"{axis}_relevancia": {"choice": "A", "probabilities": {"A": 0.9, "B": 0.1}},
        f"{axis}_polaridade": {"probabilities": {"0": 0.03, "1": 0.03, "2": 0.08, "3": 0.8, "4": 0.06}, "confidence": confidence},
    }.items()}


class FakeJev:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def system_one(self, **kwargs):
        self.calls += 1
        return self.response


class FakeLlm:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
        self.responses = self

    async def parse(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(output_parsed=self.payload, model="fake-llm")


def llm_payload(axes=AXES):
    return {"eixos": [{"eixo": axis, "relevante": True, "nivel": 1, "evidencia": "ampliar programas de transferência de renda"} for axis in axes]}


class DomainTests(unittest.TestCase):
    def test_jev_decision_and_strict_threshold(self):
        decisions, _ = jev_decisions({"answers": answers()})
        self.assertEqual(decisions["economic"]["nivel"], 1)
        original = decisions["economic"]["original"]
        exactly = {**original, "margem_relevancia": 0.60, "confianca_nivel": 0.50, "margem_direcao": 0.20}
        self.assertEqual(motivos_fallback(exactly, JEV_CONFIG), [])
        self.assertIn("baixa_confianca_nivel", motivos_fallback({**exactly, "confianca_nivel": 0.49}, JEV_CONFIG))

    def test_aggregation_and_absence(self):
        rows = []
        for level in (1, 2, 0):
            rows.append({axis: {"relevante": axis == "economic", "nivel": level if axis == "economic" else None,
                                "method": "jev", "reason": [], "quote": None} for axis in AXES})
        result = aggregate(rows, 3)
        self.assertEqual(result[0].pole_a, 75)
        self.assertEqual(result[0].pole_b, 25)
        self.assertFalse(result[0].sufficient_evidence)
        self.assertEqual(result[1].status, "no_evidence")
        self.assertIsNone(result[1].pole_a)
        self.assertIsNone(result[1].ci95)

    def test_evidence_must_be_literal_and_four_words(self):
        good = validate_answer(llm_payload(["economic"]), ["economic"], TEXT)
        self.assertEqual(good["economic"]["nivel"], 1)
        bad = validate_answer({"eixos": [{"eixo": "economic", "relevante": True, "nivel": 1,
                                        "evidencia": "uma citação inteiramente inventada"}]}, ["economic"], TEXT)
        self.assertIsNone(bad["economic"]["nivel"])
        with self.assertRaises(ValueError):
            validate_answer({"eixos": llm_payload(["economic"])["eixos"] * 2}, ["economic"], TEXT)

    def test_packaged_tokenizer_preserves_text(self):
        text = "Ação pública, educação e cooperação. " * 400
        chunks, count = split_text(text, max_tokens=12000)
        self.assertEqual("".join(chunks), text)
        self.assertGreater(count, 600)


class StrategyTests(unittest.IsolatedAsyncioTestCase):
    async def test_low_never_uses_llm(self):
        jev, llm = FakeJev({"answers": answers(confidence=0.1)}), FakeLlm(llm_payload())
        result, calls, _ = await classify_chunk(TEXT, "low", jev, {}, llm, SimpleNamespace(llm_model="fake"))
        self.assertEqual(calls, {"jev": 1, "llm": 0})
        self.assertEqual(llm.calls, 0)
        self.assertEqual(result["economic"]["method"], "jev")

    async def test_medium_reviews_only_uncertain_axes(self):
        response = answers()
        response["economic_polaridade"]["confidence"] = 0.1
        jev, llm = FakeJev({"answers": response}), FakeLlm(llm_payload(["economic"]))
        result, calls, _ = await classify_chunk(TEXT, "medium", jev, {}, llm, SimpleNamespace(llm_model="fake"))
        self.assertEqual(calls, {"jev": 1, "llm": 1})
        self.assertEqual(result["economic"]["method"], "llm")
        self.assertEqual(result["state"]["method"], "jev")

    async def test_medium_skips_llm_when_confident(self):
        jev, llm = FakeJev({"answers": answers()}), FakeLlm(llm_payload())
        _, calls, _ = await classify_chunk(TEXT, "medium", jev, {}, llm, SimpleNamespace(llm_model="fake"))
        self.assertEqual(calls["llm"], 0)

    async def test_high_never_uses_jev(self):
        jev, llm = FakeJev({"answers": answers()}), FakeLlm(llm_payload())
        result, calls, _ = await classify_chunk(TEXT, "high", jev, {}, llm, SimpleNamespace(llm_model="fake"))
        self.assertEqual(calls, {"jev": 0, "llm": 1})
        self.assertEqual(jev.calls, 0)
        self.assertEqual(result["economic"]["method"], "llm")


if __name__ == "__main__":
    unittest.main()
