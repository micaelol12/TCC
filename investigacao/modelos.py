"""Adaptadores reais E5/NLI e supervisão; importações pesadas são tardias.

Referências R3/R6/R7 e adaptações em METODOLOGIA.md. Modelos só são carregados
do cache por padrão; revisões resolvidas e contagem de truncamentos são salvas.
"""
from __future__ import annotations

from collections import Counter
import weakref
import numpy as np

from .protocolo import normalize, classification_metrics, contrastive_pairs

E5_NAME = "intfloat/multilingual-e5-base"
NLI_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

# R4: execução com pouca VRAM preserva pesos/precisão; troca apenas a residência.
_RESIDENT_MODELS = {}


def activate_model(model, device, low_vram=False):
    """R4: um modelo por GPU em inferência; libera o anterior para RAM.

    Adaptação de engenharia para reprodução na GTX 1060, sem mudar inferência
    ou limiares (METODOLOGIA.md). Não constitui uma técnica de classificação.
    """
    import torch
    if not low_vram or not str(device).startswith("cuda"):
        return
    key = str(torch.device(device))
    previous = _RESIDENT_MODELS.get(key)
    previous = previous() if previous else None
    if previous is not None and previous is not model:
        previous.to("cpu")
        torch.cuda.empty_cache()
    model.to(device)
    _RESIDENT_MODELS[key] = weakref.ref(model)


class E5:
    """R1/R6: E5 fixo; query/query simétrico e query/passage para recuperação."""

    def __init__(self, name=E5_NAME, revision=None, device="cpu", local_only=True, batch_size=None, low_vram=False):
        """R4/R6: carrega revisão explícita/cache sem executar código remoto."""
        from sentence_transformers import SentenceTransformer
        if batch_size is not None and batch_size < 1:
            raise ValueError("batch_size deve ser positivo")
        self.device, self.batch_size, self.low_vram = device, batch_size, low_vram
        self.model = SentenceTransformer(name, revision=revision, device="cpu" if low_vram else device, local_files_only=local_only)
        self.model.max_seq_length = 512
        config = self.model[0].auto_model.config
        self.info = {"name": name, "revision": getattr(config, "_commit_hash", None),
                     "requested_revision": revision, "max_length": 512, "device": device,
                     "encoded": 0, "tokens": 0, "truncated": 0,
                     "dtype": str(next(self.model.parameters()).dtype),
                     "batch_size": batch_size or 16, "low_vram": low_vram}
        self.cache = {}

    def encode(self, texts, role="query", batch_size=16):
        """R6 + ficha E5: normaliza espaços/prefixos e registra truncamento real."""
        if role not in {"query", "passage"}:
            raise ValueError("Prefixo E5 inválido")
        inputs = [f"{role}: {normalize(t)}" for t in texts]
        missing = list(dict.fromkeys(x for x in inputs if x not in self.cache))
        if missing:
            activate_model(self.model, self.device, self.low_vram)
            lengths = [len(x) for x in self.model.tokenizer(missing, truncation=False)["input_ids"]]
            self.info["encoded"] += len(missing)
            self.info["tokens"] += sum(lengths)
            self.info["truncated"] += sum(n > self.model.max_seq_length for n in lengths)
            encoded = self.model.encode(missing, normalize_embeddings=True, batch_size=self.batch_size or batch_size, show_progress_bar=False)
            self.cache.update(zip(missing, encoded))
        if not inputs:
            return np.empty((0, self.model.get_sentence_embedding_dimension()))
        return np.array([self.cache[x] for x in inputs])


class NLI:
    """R7: trecho como premissa e proposição como hipótese; N != centro político."""

    def __init__(self, name=NLI_NAME, revision=None, device="cpu", local_only=True, batch_size=None, low_vram=False):
        """R4/R7: mapeia classes pelo config, sem assumir ordem dos logits."""
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        if batch_size is not None and batch_size < 1:
            raise ValueError("batch_size deve ser positivo")
        self.batch_size, self.low_vram = batch_size, low_vram
        self.tokenizer = AutoTokenizer.from_pretrained(name, revision=revision, local_files_only=local_only)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            name, revision=revision, local_files_only=local_only, torch_dtype=torch.float32).to("cpu" if low_vram else device).eval()
        self.device = device
        self.labels = {int(i): s.lower() for i, s in self.model.config.id2label.items()}
        if set(self.labels.values()) != {"entailment", "neutral", "contradiction"}:
            raise ValueError(f"Mapeamento NLI desconhecido: {self.labels}")
        self.info = {"name": name, "revision": getattr(self.model.config, "_commit_hash", None),
                     "requested_revision": revision, "device": device, "pairs": 0, "tokens": 0, "truncated": 0,
                     "id2label": self.labels, "max_length": 512, "dtype": "float32",
                     "batch_size": batch_size or 8, "low_vram": low_vram}
        self.cache = {}

    def predict(self, pairs, batch_size=8):
        """R7: softmax completo E/C/N; log de truncamento, execução em lotes."""
        import torch
        pairs = [(normalize(a), normalize(b)) for a, b in pairs]
        missing = list(dict.fromkeys(x for x in pairs if x not in self.cache))
        if missing:
            activate_model(self.model, self.device, self.low_vram)
        batch_size = self.batch_size or batch_size
        for start in range(0, len(missing), batch_size):
            batch = missing[start:start + batch_size]
            premises, hypotheses = map(list, zip(*batch))
            raw = self.tokenizer(premises, hypotheses, truncation=False)["input_ids"]
            self.info["tokens"] += sum(map(len, raw))
            self.info["truncated"] += sum(len(x) > 512 for x in raw)
            self.info["pairs"] += len(batch)
            tokens = self.tokenizer(premises, hypotheses, padding=True, truncation=True,
                                    max_length=512, return_tensors="pt").to(self.device)
            with torch.inference_mode():
                probabilities = self.model(**tokens).logits.float().softmax(-1).cpu().numpy()
            for pair, p in zip(batch, probabilities):
                self.cache[pair] = {label: float(p[i]) for i, label in self.labels.items()}
        return [dict(self.cache[x]) for x in pairs]


def conditioned(row):
    """R3/R6: classificador compartilhado condicionado ao alvo, sem rótulo na entrada."""
    return f"Alvo: {row['target']} Texto: {row['text']}"


def fit_head(encoder, train, dev, seed=42, cs=(.01, .1, 1., 10.)):
    """R6/R4: regressão logística L2; C escolhido exclusivamente no dev."""
    from sklearn.linear_model import LogisticRegression
    x = encoder.encode([conditioned(r) for r in train])
    d = encoder.encode([conditioned(r) for r in dev])
    candidates = []
    for c in cs:
        head = LogisticRegression(C=c, max_iter=2000, class_weight="balanced", random_state=seed)
        head.fit(x, [r["label"] for r in train])
        metric = classification_metrics([r["label"] for r in dev], head.predict(d).tolist())
        candidates.append((metric["macro_f1"], -c, head, metric))
    _, _, head, metrics = max(candidates, key=lambda t: t[:2])
    return head, {"C": head.C, "dev": metrics, "grid": list(cs)}


def finetune(encoder, train, seed=42, epochs=1, per_example=2, batch_size=8):
    """R6: SetFit adaptado ao alvo; loss cosseno, não reprodução da loss SimCSE.

    Só treino entra nos pares. Mesmo encoder/cabeça/protocolo da alternativa
    congelada; orçamento fixo de uma época por padrão, sem seleção pelo teste.
    """
    import random
    import torch
    from torch.utils.data import DataLoader
    from sentence_transformers import InputExample, losses
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    pairs = contrastive_pairs(train, seed, per_example)
    examples = [InputExample(texts=["query: " + normalize(conditioned(train[a])),
                                   "query: " + normalize(conditioned(train[b]))], label=float(y))
                for a, b, y in pairs]
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(examples, shuffle=True, batch_size=batch_size, generator=generator,
                        collate_fn=encoder.model.smart_batching_collate)
    encoder.model.float()
    loss_fn = losses.CosineSimilarityLoss(encoder.model)
    optimizer = torch.optim.AdamW(encoder.model.parameters(), lr=2e-5)
    encoder.model.train()
    observed_losses = []
    # R6: laço explícito evita dependência do Trainer; mesma loss de pares.
    for _ in range(epochs):
        for features, labels in loader:
            features = [{k: v.to(encoder.model.device) for k, v in f.items()} for f in features]
            optimizer.zero_grad()
            loss = loss_fn(features, labels.to(encoder.model.device))
            if not torch.isfinite(loss):
                raise ValueError("Loss contrastiva não finita")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(encoder.model.parameters(), 1.)
            optimizer.step()
            observed_losses.append(float(loss.detach().cpu()))
    encoder.model.eval()
    encoder.cache.clear()
    return {"seed": seed, "epochs": epochs, "learning_rate": 2e-5, "loss": "CosineSimilarityLoss",
            "loss_values": observed_losses, "optimizer": "AdamW", "weight_decay": .01, "gradient_clip": 1.,
            "pairs": [{"left": train[a]["id"], "right": train[b]["id"], "same_stance": y} for a, b, y in pairs],
            "pair_labels": dict(Counter(p[2] for p in pairs))}


def zero_shot(encoder, rows):
    """R3/R6: baseline relacional sem ajuste, margem entre templates fixos.

    Não confundir estes templates relacionais com as âncoras B0 dos eixos.
    """
    x = encoder.encode([conditioned(r) for r in rows])
    positive = encoder.encode([f"Sou favorável a {r['target']}." for r in rows])
    negative = encoder.encode([f"Sou contrário a {r['target']}." for r in rows])
    return np.sum(x * (positive - negative), axis=1)
