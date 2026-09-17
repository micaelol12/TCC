"""Valida requisitos científicos R1–R7; fontes em investigacao/METODOLOGIA.md.

Dados artificiais testam engenharia/invariantes; não medem qualidade semântica.
"""
import unittest
import tempfile
import zipfile
import json
from pathlib import Path
import numpy as np

from investigacao.protocolo import (calibrate, classification_metrics, contrastive_pairs,
    connected_groups, grouped_bootstrap,
    direction_scores, evidence_state, inserted_context, pair_diagnostic, quiz_summary,
    retrieval_metrics, segments, validate_corpus)
from investigacao.dados import import_ustancebr, split_development
from investigacao.experimentos import document, robustness, sabia_agreement


class ProtocolTests(unittest.TestCase):
    """R4/R5: regressões de vazamento, ausência e invariância por construção."""

    def test_geometry(self):
        """R2: centro ortogonal e margem proporcional; polos iguais rejeitados."""
        p, n = np.array([1., 0]), np.array([0., 1])
        x = np.array([[1., 0], [0., 1]])
        projection, margin = direction_scores(x, p, n)
        np.testing.assert_allclose(margin, projection * np.linalg.norm(p - n))
        self.assertAlmostEqual(float(((p + n) / 2) @ (p - n)), 0)
        with self.assertRaises(ValueError):
            direction_scores(x, p, p)

    def test_metrics_and_pair_calibration(self):
        """R3/R4: BA/MCC conhecidos; B4 consegue corrigir offset sem vazar o par."""
        perfect = classification_metrics(["favor", "against"], ["favor", "against"])
        self.assertEqual(perfect["mcc"], 1)
        result = pair_diagnostic([[3, 1], [3.1, 1.1], [3.2, 1.2]])
        self.assertEqual(result["ordering_accuracy"], 1)
        self.assertEqual(result["raw"]["balanced_accuracy"], .5)
        self.assertGreater(result["leave_one_pair_out"]["balanced_accuracy"], .5)
        with self.assertRaises(ValueError):
            calibrate([1, 2], ["favor", "favor"])

    def test_corpus_leakage(self):
        """R4: autor/duplicata/família cruzando splits interrompe antes do treino."""
        metadata = dict(name="fixture", version="1", source="controlled", license="test",
                        label_definition="binary", split_policy="fixture", annotation_unit="text_target")
        rows = [dict(id=f"{s}_{y}", text=f"Texto {s} {y}", target="alvo", label=y,
                     split=s, author_id=f"{s}_{y}", label_source="corpus_publico")
                for s in ("train", "dev", "test") for y in ("favor", "against")]
        self.assertEqual(validate_corpus(rows, metadata)["n"], 6)
        for field in ("author_id", "text", "family_id"):
            bad = [dict(r) for r in rows]
            bad[0][field] = bad[2][field] = "mesma origem"
            with self.assertRaises(ValueError):
                validate_corpus(bad, metadata)
        metadata["annotation_unit"] = "author"
        with self.assertRaises(ValueError):
            validate_corpus(rows, metadata)

    def test_contrastive_pairs(self):
        """R6: pares alvo-condicionados, só treino, sem autopares e deterministas."""
        rows = [dict(id=str(i), text=f"texto {i}", target=str(i // 4),
                     label="favor" if i % 2 else "against", split="train") for i in range(8)]
        pairs = contrastive_pairs(rows)
        self.assertEqual(pairs, contrastive_pairs(rows))
        for a, b, label in pairs:
            self.assertNotEqual(a, b)
            self.assertEqual(rows[a]["target"], rows[b]["target"])
            self.assertEqual(label, int(rows[a]["label"] == rows[b]["label"]))
        rows[-1]["split"] = "test"
        with self.assertRaises(ValueError):
            contrastive_pairs(rows)

    def test_offsets_and_duplicates(self):
        """R5: offsets revertem ao original; duplicatas mantêm ocorrências sem peso."""
        text = "um dois\n\num dois"
        chunks = segments(text, 2, 0)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(chunks[0]["occurrences"]), 2)
        for a, b in chunks[0]["occurrences"]:
            self.assertEqual(text[a:b], "um dois")
        self.assertEqual(segments(""), [])
        with self.assertRaises(ValueError):
            segments("a b", 2, 2)

    def test_absence_conflict_and_nli(self):
        """R7: neutral não vira neutralidade explícita; duplicação não muda decisão."""
        favor = dict(text="apoio", entailment=.9, contradiction=.05, neutral=.05)
        against = dict(text="rejeito", entailment=.05, contradiction=.9, neutral=.05)
        neutral = dict(text="assunto", entailment=.01, contradiction=.01, neutral=.98)
        self.assertEqual(evidence_state([]), "sem_evidencia")
        self.assertEqual(evidence_state([neutral]), "incerta")
        self.assertEqual(evidence_state([favor, favor]), "favoravel")
        self.assertEqual(evidence_state([favor, against]), "conflito")
        self.assertEqual(evidence_state([against, favor]), "conflito")

    def test_quiz_missingness(self):
        """Plano §7/R2: ausência [0,100], observações completas colapsam intervalo."""
        q = [dict(id=i, effect=dict(econ=w, dipl=w, govt=w, scty=w)) for i, w in [(1, 10), (2, -10)]]
        missing = quiz_summary(q, {})["econ"]
        self.assertEqual(missing["identification_interval"], [0, 100])
        self.assertEqual(missing["coverage"], 0)
        self.assertIsNone(missing["conditional_score"])
        full = quiz_summary(q, {"1": 1, "2": -1})["econ"]
        self.assertEqual(full["identification_interval"], [100, 100])
        partial = quiz_summary(q, {"1": 1})["econ"]
        self.assertEqual(partial["identification_interval"], [50, 100])
        self.assertEqual(partial["coverage"], .5)
        with self.assertRaises(ValueError):
            quiz_summary(q, {"1": 2})

    def test_inserted_retrieval(self):
        """R5: conta passagem contrária também; recall restrito à inserção conhecida."""
        source = dict(id="s", text="evidência contra", target="t", label="against", split="test")
        context = inserted_context(source, [dict(id="d", text="outro assunto")])
        self.assertEqual(context["text"][context["start"]:context["end"]], source["text"])
        chunks = segments(context["text"], 2, 0)
        metric = retrieval_metrics(chunks, [0., 1.], context["start"], context["end"])
        self.assertEqual(metric["recall_inserted"]["1"], 1)

    def test_grouped_bootstrap(self):
        """R8: modelos idênticos têm delta e intervalo nulos, mesmo em grupos."""
        y = ["favor", "against"] * 3
        r = grouped_bootstrap(y, y, y, ["a", "a", "b", "b", "c", "c"], repeats=30)
        self.assertEqual(r["percentile_interval_95"], [0, 0])
        self.assertEqual(r["groups"], 3)

    def test_transitive_groups_and_split(self):
        """R4: duplicata une autores transitivamente, teste nunca vira dev."""
        rows = [dict(text="a", author_id="1", split="train"),
                dict(text="a", author_id="2", split="train"),
                dict(text="b", author_id="2", split="train"),
                dict(text="c", author_id="3", split="train"),
                dict(text="d", author_id="4", split="test")]
        groups = connected_groups(rows)
        self.assertEqual(len(set(groups[:3])), 1)
        parts = split_development(rows)
        self.assertEqual(parts[-1]["split"], "test")
        self.assertEqual(len({r["split"] for r in parts[:3]}), 1)

    def test_document_pipeline_without_intensity(self):
        """R5/R7: integração controlada de recuperação/NLI sem inventar intensidade."""
        class Encoder:
            """R5: fixture vetorial determinista, sem alegação semântica."""
            def encode(self, texts, role="query"):
                """R5: vetores fixos para verificar encadeamento e ausência."""
                return np.array([[1., 0.] for _ in texts]).reshape(-1, 2)
        class Infer:
            """R7: probabilidades conhecidas por construção para teste do agregador."""
            def predict(self, pairs):
                """R7: resposta sempre entailment para isolar o contrato do pipeline."""
                return [dict(entailment=.9, contradiction=.05, neutral=.05) for _ in pairs]
        questions = [dict(id=1, question="Uma proposição", effect=dict(econ=10, dipl=10, govt=10, scty=10))]
        r = robustness("Uma passagem. Outra passagem.", questions, Encoder(), Infer())
        self.assertEqual(r["base"]["items"][0]["state"], "favoravel")
        self.assertIsNone(r["base"]["items"][0]["response"])
        self.assertEqual(r["base"]["quiz"]["econ"]["identification_interval"], [0, 100])
        self.assertTrue(all(v for k, v in r["checks"][0].items() if k != "question_id"))
        empty = document("", questions, Encoder(), Infer())
        self.assertEqual(empty["items"][0]["state"], "sem_evidencia")

    def test_ustancebr_adapter(self):
        """R3/R4: fixture do formato real r3; join, rótulos e dev agrupado."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            hydrated = []
            with zipfile.ZipFile(root / "r3.zip", "w") as archive:
                for split, authors in (("train", range(6)), ("test", range(6, 8))):
                    csv = "Tweet_ID;Polarity\n"
                    for author in authors:
                        for label in ("for", "against"):
                            key = f"{author}{label}"
                            csv += f"_{key};{label}\n"
                            hydrated.append(dict(id=key, author_id=str(author), text=f"Texto único {key}"))
                    archive.writestr(f"IDs/r3_bo_{split}_ids.csv", csv.encode("utf-8-sig"))
            path = root / "hydrated.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in hydrated), encoding="utf-8")
            audit = import_ustancebr(root / "r3.zip", path, root / "output")
            self.assertEqual(audit["counts"]["test"], 4)
            self.assertGreater(audit["counts"]["dev"], 0)

    def test_sabia_not_truth(self):
        """R3/§6: compara por ID e preserva escopo de concordância."""
        config = dict(model="sabia-fixo", prompt_sha256="fixture", temperature=0)
        ref = [dict(question_id=2, state="incerta"), dict(question_id=1, state="contraria")]
        items = [dict(question_id=1, state="favoravel"), dict(question_id=2, state="incerta")]
        result = sabia_agreement(items, ref, config)
        self.assertEqual(result["agreement"], .5)
        self.assertEqual(result["disagreements"][0]["question_id"], 1)
        with self.assertRaises(ValueError):
            sabia_agreement(items, ref + ref, config)


if __name__ == "__main__":
    unittest.main()
