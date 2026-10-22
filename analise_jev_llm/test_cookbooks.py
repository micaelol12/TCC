"""Testes das salvaguardas e métricas, sem rede nem credenciais reais."""
import json
import tempfile
import unittest
from pathlib import Path

from tcc_lib import jev_cookbooks as cb


def answer(relevant=True, level=4):
    result = {}
    for axis in cb.AXES:
        result[axis + "_relevancia"] = {"choice": "A" if relevant else "B",
                                       "probabilities": {"A": float(relevant), "B": float(not relevant)}}
        result[axis + "_polaridade"] = {"confidence": 1., "probabilities": {str(i): float(i == level) for i in range(5)}}
    return {"answers": result, "model": "fixed"}


class FakeLab:
    def __init__(self):
        self.calls = []

    def jev(self, state, questions, fresh=False):
        self.calls.append((state, questions, fresh))
        return answer()


class CookbookTests(unittest.TestCase):
    def test_stability_calls_are_fresh_and_input_unchanged(self):
        lab = FakeLab()
        tables = cb.stability(lab, cb.PILOT[:1], repeats=3)
        self.assertEqual(len(lab.calls), 3)
        self.assertTrue(all(fresh for _, _, fresh in lab.calls))
        self.assertEqual(len({state for state, _, _ in lab.calls}), 1)
        self.assertTrue((tables["estabilidade_resumo"].acordo_modal == 1).all())
        self.assertTrue((tables["estabilidade_resumo"].desvio_score == 0).all())

    def test_coarse_direction_never_invents_intensity(self):
        row = dict(relevance_margin=.9, relevant=True, level=1, confidence=.4,
                   p_a=.9, p_b=.05, p_zero=.05)
        self.assertEqual(cb.coarse_decision(row), ("direcao", "A"))
        row.update(p_a=.45, p_b=.45)
        self.assertEqual(cb.coarse_decision(row), ("incerta", None))
        row.update(relevant=False)
        self.assertEqual(cb.coarse_decision(row), ("ausente", None))
        row.update(relevance_margin=.1)
        self.assertEqual(cb.coarse_decision(row), ("incerta", None))

    def test_missing_quote_does_not_call_model(self):
        lab = FakeLab()
        r = cb.citation_verdict(lab, "Texto sobre outro assunto.", "privatizar todos os hospitais públicos", "Defende privatização")
        self.assertEqual(r["verdict"], "nao_localizada")
        self.assertEqual(lab.calls, [])

    def test_negation_quote_is_found_before_semantic_check(self):
        self.assertTrue(cb._score_evidencia_confere(
            "Rejeitamos a proposta de privatizar todos os hospitais públicos.",
            "privatizar todos os hospitais públicos"))

    def test_cache_budget_fresh_and_model_drift(self):
        with tempfile.TemporaryDirectory(dir=cb.ROOT) as directory:
            lab = cb.Lab(live=True, max_calls=2, output=Path(directory) / "run")
            lab.cache = Path(directory) / "cache"
            count = []
            def invoke():
                count.append(1)
                return {"model": "v1", "answers": {}}
            lab._request("fake", "alias", {"x": 1}, invoke)
            lab._request("fake", "alias", {"x": 1}, invoke)
            self.assertEqual(len(count), 1)
            self.assertTrue(lab.events[-1]["cached"])
            lab._request("fake", "alias", {"x": 1}, invoke, fresh=True)
            self.assertEqual(len(count), 2)
            with self.assertRaises(cb.BudgetExceeded):
                lab._request("fake", "alias", {"x": 2}, invoke)
            lab.max_calls = 3
            with self.assertRaises(ValueError):
                lab._request("fake", "alias", {"x": 3}, lambda: {"model": "v2"})
            self.assertEqual(lab.events[-1]["status"], "error")

    def test_errors_are_recorded_without_provider_message(self):
        with tempfile.TemporaryDirectory(dir=cb.ROOT) as directory:
            lab = cb.Lab(live=True, output=directory)
            lab.cache = Path(directory) / "cache"
            def fail():
                raise ValueError("FAKE_SECRET_MUST_NOT_BE_SAVED")
            with self.assertRaises(ValueError):
                lab._request("fake", "v1", {}, fail)
            self.assertNotIn("FAKE_SECRET", (Path(directory) / "requests.json").read_text())

    def test_failed_experiment_does_not_claim_success(self):
        with tempfile.TemporaryDirectory(dir=cb.ROOT) as directory:
            lab = cb.Lab(output=directory)
            def fail(_):
                raise ValueError("bad data")
            self.assertEqual(lab.run("failure", fail), {})
            self.assertEqual(lab.status[-1]["status"], "incompleto")

    def test_resume_restores_tables_without_repeating_inferences(self):
        with tempfile.TemporaryDirectory(dir=cb.ROOT) as directory:
            lab = cb.Lab(output=directory)
            lab.run("confianca", lambda _: {"confianca_detalhes": cb.pd.DataFrame([{"valor": 42}])})
            resumed = cb.Lab(output=directory, resume=True)
            def should_not_run(_):
                self.fail("Experimento concluído não deve ser repetido na retomada")
            tables = resumed.run("confianca", should_not_run)
            self.assertEqual(tables["confianca_detalhes"].iloc[0].valor, 42)
            self.assertEqual(resumed.calls, 0)


if __name__ == "__main__":
    unittest.main()
