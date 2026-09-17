"""Integração real Torch/ST/sklearn em encoder minúsculo; R6, METODOLOGIA.md.

Valida a mecânica de treino, não o desempenho de E5 nem um corpus público.
"""
import importlib.util
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("sentence_transformers"), "Dependências ML não instaladas")
class TrainingTest(unittest.TestCase):
    """R6: pesos devem mudar, cache invalidar e cabeça produzir classes válidas."""

    def test_low_vram_residency(self):
        """R4: alternância libera modelo anterior, sem alterar pesos ou exigir CUDA no teste."""
        from investigacao.modelos import activate_model, _RESIDENT_MODELS

        class Model:
            """R4: fixture de movimentação; GPU real é validada pelos experimentos."""
            def __init__(self):
                """R4: registra apenas a localização, sem executar um classificador."""
                self.moves = []

            def to(self, device):
                """R4: captura a sequência RAM/GPU para validar a política de residência."""
                self.moves.append(device)
                return self

        left, right = Model(), Model()
        with patch.dict(_RESIDENT_MODELS, {}, clear=True), patch("torch.cuda.empty_cache") as empty:
            activate_model(left, "cuda", True)
            activate_model(right, "cuda", True)
            activate_model(right, "cuda", True)
            self.assertEqual(left.moves, ["cuda", "cpu"])
            self.assertEqual(right.moves, ["cuda", "cuda"])
            self.assertEqual(empty.call_count, 1)

    def test_real_training_loop(self):
        """R6/R4: uma época em fixture; seleção de C usa dev separado do treino."""
        import numpy as np
        import torch
        from sentence_transformers import SentenceTransformer, models
        from investigacao.modelos import finetune, fit_head, conditioned
        torch.set_num_threads(1)
        torch.manual_seed(42)
        vocabulary = ["query", "alvo", "texto", "impostos", "apoio", "defendo", "rejeito", "condeno", "sim", "não"]

        class TinyEncoder:
            """R6: fixture treinável BoW+Dense; explicitamente não é E5."""
            def __init__(self):
                """R6: inicializa representação pequena para integração sem download."""
                self.model = SentenceTransformer(modules=[models.BoW(vocabulary),
                    models.Dense(len(vocabulary), 4), models.Normalize()], device="cpu")
                self.cache = {"stale": True}

            def encode(self, texts):
                """R6: mesma interface de embedding normalizado do protocolo."""
                return self.model.encode(["query: " + t for t in texts], normalize_embeddings=True)

        encoder = TinyEncoder()
        train = [dict(id=str(i), target="impostos", text=t, label=y, split="train")
                 for i, (t, y) in enumerate([("apoio sim", "favor"), ("defendo sim", "favor"),
                                             ("rejeito não", "against"), ("condeno não", "against")])]
        dev = [dict(id="d1", target="impostos", text="apoio defendo", label="favor", split="dev"),
               dict(id="d2", target="impostos", text="rejeito condeno", label="against", split="dev")]
        before = encoder.model[1].linear.weight.detach().clone()
        training = finetune(encoder, train, batch_size=2, per_example=1)
        self.assertFalse(torch.equal(before, encoder.model[1].linear.weight))
        self.assertEqual(encoder.cache, {})
        self.assertTrue(all(np.isfinite(training["loss_values"])))
        head, selection = fit_head(encoder, train, dev)
        self.assertIn(selection["C"], selection["grid"])
        self.assertEqual(len(head.predict(encoder.encode([conditioned(r) for r in dev]))), 2)


if __name__ == "__main__":
    unittest.main()
