"""Diagnósticos por construção, inspirados em CheckList (R5), sem rótulos humanos.

Templates limitam-se à declaração explícita de apoio/oposição; não invertem
rótulos de frases naturais inserindo 'não'. NLI é diagnosticado, não validado
como leitor de documentos políticos. Referências em METODOLOGIA.md.
"""
import time
from pathlib import Path

from .experimentos import controlled, manifest, nli_ablation
from .modelos import E5, NLI
from .protocolo import evidence_state, notebook_assets, write_json


def template_rows():
    """R5/R7: família agrupa versões de um mesmo alvo; expectativa explícita."""
    targets = ["reduzir a jornada semanal de trabalho", "ampliar a tributação progressiva",
               "privatizar empresas públicas", "ampliar a cooperação internacional"]
    rows = []
    for i, target in enumerate(targets):
        for label, statement in (("favor", "Somos favoráveis a"), ("against", "Somos contrários a")):
            rows.append({"id": f"template-{i}-{label}", "text": f"{statement} {target}.",
                         "target": target, "label": label, "split": "diagnostic", "family_id": f"template-{i}",
                         "label_source": "construcao_controlada", "generator": "template_declaracao_v1",
                         "template": statement + " {target}.", "source_id": f"alvo_controlado-{i}"})
    return rows


def run(root, output, device="cpu", batch_size=None, low_vram=False):
    """R5: avaliação declarativa e contexto inserido; registra erros sem reajustar."""
    import torch
    torch.set_num_threads(4)
    started = time.perf_counter()
    root, output = Path(root), Path(output)
    rows = template_rows()
    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA indisponível; use um interpretador com suporte à GPU")
        torch.cuda.reset_peak_memory_stats(device)
    e5 = E5(device=device, batch_size=batch_size, low_vram=low_vram)
    nli = NLI(device=device, batch_size=batch_size, low_vram=low_vram)
    cases = []
    for row in rows:
        hypothesis = f"Somos favoráveis a {row['target']}."
        p = nli.predict([(row["text"], hypothesis)])[0]
        state = evidence_state([{**p, "text": row["text"]}])
        expected = "favoravel" if row["label"] == "favor" else "contraria"
        cases.append({**row, "hypothesis": hypothesis, "expected": expected, "predicted": state,
                      "satisfied": state == expected, "probabilities": p})
    contexts = controlled(rows, e5, window=20, overlap=5)
    questions = [{"id": "controlled-work", "question": "Somos favoráveis a reduzir a jornada semanal de trabalho.",
                  "effect": {"econ": 10, "dipl": 0, "govt": 0, "scty": 0}}]
    ablation = nli_ablation([(r["id"], r["text"]) for r in rows[:2]], questions,
                           notebook_assets(root / "TCC.ipynb"), nli)
    write_json(output / "templates_nli.json", cases)
    write_json(output / "contextos.json", contexts)
    write_json(output / "ablacao_nli.json", ablation)
    write_json(output / "manifest.json", manifest({"experiment": "controlados", "encoder": e5.info,
                                                   "nli": nli.info, "seed": 42, "sources": ["construcao_controlada"],
                                                   "window": 20, "overlap": 5}, [root / "TCC.ipynb"], started))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--low-vram", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Saída já existe; escolha uma nova")
    run(args.root, args.output, args.device, args.batch_size, args.low_vram)
