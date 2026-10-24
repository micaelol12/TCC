import asyncio
import unittest
from types import SimpleNamespace

from app.pipeline.aggregation import aggregate
from app.pipeline.domain import motivos_fallback, criar_rubrica_polaridade_ordinal, _normalizar_polaridade_ordinal, decidir_llm
from app.pipeline.clients import jev_questions
from app.pipeline.validation import LlmAxis
from app.polarity import COUNT_KEYS
from app.pipeline.segmentation import split_text
from app.pipeline.strategies import JEV_CONFIG, classify_chunk, jev_decisions
from app.pipeline.validation import validate_answer

AXES = ("economic", "diplomatic", "state", "society")
TEXT = "Vamos ampliar programas de transferência de renda para famílias pobres."


def answers(confidence=0.8):
    return {key: value for axis in AXES for key, value in {
        f"{axis}_relevancia": {"choice": "A", "probabilities": {"A": 0.9, "B": 0.1}},
        f"{axis}_polaridade": {"probabilities": {"0": 0.01, "1": 0.01, "2": 0.02, "3": 0.02,
            "4": 0.08, "5": 0.8, "6": 0.02, "7": 0.02, "8": 0.02}, "confidence": confidence},
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
    def test_polarity_primitive_builds_and_decodes_the_matching_provider_contract(self):
        from typesafe_sdk import Choice, Score
        from app.experiment_config import ExperimentConfig
        from app.polarity import ESCALA_5_NIVEIS, ESCALA_9_NIVEIS
        for scale in (ESCALA_5_NIVEIS, ESCALA_9_NIVEIS):
            for primitive, question_type in (("score", Score), ("choice", Choice)):
                with self.subTest(scale=scale.id, primitive=primitive):
                    config = ExperimentConfig(escala=scale, primitiva_polaridade=primitive)
                    questions = jev_questions(scale, primitive)
                    rubric = criar_rubrica_polaridade_ordinal('economic', escala=scale)
                    self.assertIsInstance(questions['economic_relevancia'], Choice)
                    polarity = questions['economic_polaridade']
                    self.assertIsInstance(polarity, question_type)
                    self.assertEqual(polarity.criteria, list(rubric['niveis'].values()) if primitive == 'score' else rubric['niveis'])
                    keys = list(map(str, range(len(scale.niveis)))) if primitive == 'score' else list(rubric['niveis'])
                    raw = {key: value for axis in AXES for key, value in {
                        f'{axis}_relevancia': {'choice': 'A', 'probabilities': {'A': .99, 'B': .01}},
                        f'{axis}_polaridade': {'probabilities': {key: int(i == 1) for i, key in enumerate(keys)}, 'confidence': .99},
                    }.items()}
                    decisions, _ = jev_decisions({'answers': raw}, config.jev_config())
                    self.assertEqual(decisions['economic']['nivel'], scale.niveis[1].codigo)
                    self.assertEqual(decisions['economic']['reason'], [])
        with self.assertRaises(ValueError): jev_questions(primitiva_polaridade='invalid')

    def test_nine_levels_use_the_same_rubric_and_conversion_for_both_providers(self):
        questions = jev_questions()
        for axis in AXES:
            rubric = criar_rubrica_polaridade_ordinal(axis)
            self.assertEqual([item['valor'] for item in rubric['niveis'].values()], list(range(-4, 5)))
            self.assertEqual(len(questions[f'{axis}_polaridade'].criteria), 9)
            self.assertTrue(all(item['situacao'] and item['exemplos'] for item in rubric['niveis'].values()))
        for index, level in enumerate(range(-4, 5)):
            with self.subTest(level=level):
                response = {'probabilities': {str(i): int(i == index) for i in range(9)}, 'confidence': .9}
                jev = _normalizar_polaridade_ordinal(response, True)
                self.assertEqual(jev['nivel'], level)
                self.assertEqual(jev['valor_0_100'], index * 12.5)
                self.assertEqual(jev['p_polo_A'], int(level > 0))
                self.assertEqual(jev['p_polo_B'], int(level < 0))
                item = LlmAxis(eixo='economic', relevante=True, nivel=level, evidencia=TEXT)
                llm = decidir_llm(item, TEXT, {'relevante': True}, [], 'fake', None)
                self.assertEqual(llm['valor_0_100'], jev['valor_0_100'])
                rows = [{axis: {'relevante': True, 'nivel': level, 'method': 'jev', 'reason': [], 'quote': None} for axis in AXES}]
                aggregated = aggregate(rows, 1)[0]
                self.assertEqual(aggregated.pole_a, index * 12.5)
                self.assertEqual(aggregated.pole_b, 100 - index * 12.5)
                self.assertEqual(aggregated.level_counts.model_dump()[COUNT_KEYS[level]], 1)

    def test_nine_level_distribution_ties_and_invalid_levels(self):
        response = {'probabilities': {str(i): .5 if i in (2, 6) else 0 for i in range(9)}, 'confidence': .5}
        tied = _normalizar_polaridade_ordinal(response, True)
        self.assertEqual(tied['status'], 'empate')
        self.assertIsNone(tied['valor_0_100'])
        self.assertEqual(tied['margem_direcao'], 0)
        self.assertIsNone(_normalizar_polaridade_ordinal(response, False)['nivel'])
        with self.assertRaises(ValueError):
            _normalizar_polaridade_ordinal({'probabilities': {str(i): .2 for i in range(5)}, 'confidence': .8}, True)
        for level in (-5, 5, 1.5):
            with self.assertRaises(ValueError):
                LlmAxis(eixo='economic', relevante=True, nivel=level, evidencia=TEXT)

    def test_jev_decision_and_strict_threshold(self):
        decisions, _ = jev_decisions({"answers": answers()})
        self.assertEqual(decisions["economic"]["nivel"], 1)
        original = decisions["economic"]["original"]
        exactly = {**original, "margem_relevancia": 0.60, "confianca_nivel": 0.50, "margem_direcao": 0.20}
        self.assertEqual(motivos_fallback(exactly, JEV_CONFIG), [])
        self.assertIn("baixa_confianca_nivel", motivos_fallback({**exactly, "confianca_nivel": 0.49}, JEV_CONFIG))

    def test_aggregation_and_absence(self):
        rows = []
        for level in (2, 4, 0):
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
