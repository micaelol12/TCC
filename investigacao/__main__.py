"""CLI do protocolo (R4: execução/configuração explícitas; ver METODOLOGIA.md)."""
import argparse
import json
from pathlib import Path
import time

from .experimentos import apply_frozen, controlled, diagnostic, external, manifest, robustness, sabia_agreement
from .dados import import_ustancebr, import_brmoral
from .modelos import E5, NLI
from .protocolo import notebook_assets, write_json


def main():
    """R4: entrada reproduzível; cada comando escreve em diretório novo."""
    p = argparse.ArgumentParser(description="Investigação de similaridade semântica sem nova anotação manual")
    p.add_argument("command", choices=["assets", "diagnostic", "external", "documents", "controlled", "prepare-ustancebr", "prepare-brmoral"])
    p.add_argument("--baselines-only", action="store_true", help="Comparação parcial externa: sem ajuste e encoder congelado")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--corpus", type=Path)
    p.add_argument("--metadata", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--hydrated", type=Path)
    p.add_argument("--selected-run", type=Path, help="Execução externa confiável com seleção congelada")
    p.add_argument("--text", type=Path)
    p.add_argument("--sabia", type=Path, help="JSON com items e config fixa")
    p.add_argument("--device", default="cpu")
    p.add_argument("--batch-size", type=int, help="Limita os lotes de inferência E5/NLI")
    p.add_argument("--low-vram", action="store_true", help="Mantém apenas um modelo por vez na GPU")
    p.add_argument("--download", action="store_true", help="Permite baixar modelos fora do cache")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--question-limit", type=int, help="Smoke test; não representa o instrumento completo")
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--seeds", nargs="+", type=int, default=[13, 42, 77])
    args = p.parse_args()
    if args.output.exists():
        p.error("Diretório de saída já existe; escolha outro para preservar a execução")
    if args.command in {"external", "controlled"} and not args.corpus:
        p.error("--corpus é obrigatório")
    if args.command == "external" and not args.metadata:
        p.error("--metadata é obrigatório")
    if args.command == "documents" and not args.text:
        p.error("--text é obrigatório (UTF-8)")
    if args.question_limit is not None and args.question_limit < 1:
        p.error("--question-limit deve ser positivo")
    if args.batch_size is not None and args.batch_size < 1:
        p.error("--batch-size deve ser positivo")
    if args.command == "external" and not args.baselines_only and (args.low_vram or args.batch_size is not None):
        p.error("--low-vram/--batch-size são opções de inferência; não reduzem a memória de treinamento")
    if args.command == "assets":
        write_json(args.output / "assets.json", notebook_assets(args.root / "TCC.ipynb"))
        return
    if args.command == "prepare-brmoral":
        if not args.archive:
            p.error("--archive é obrigatório")
        import_brmoral(args.archive, args.output, args.seeds[0])
        return
    if args.command == "prepare-ustancebr":
        if not args.archive or not args.hydrated:
            p.error("--archive e --hydrated são obrigatórios")
        import_ustancebr(args.archive, args.hydrated, args.output, args.seeds[0])
        return
    import torch
    torch.set_num_threads(args.threads)
    if args.device.startswith("cuda"):
        if not torch.cuda.is_available():
            p.error("CUDA indisponível neste interpretador; não haverá fallback silencioso para CPU")
        torch.cuda.reset_peak_memory_stats(args.device)
    started = time.perf_counter()
    if args.command == "external":
        external(args.corpus, args.metadata, args.output, args.seeds, args.device, not args.download,
                 baselines_only=args.baselines_only, batch_size=args.batch_size, low_vram=args.low_vram)
        return
    encoder = E5(device=args.device, local_only=not args.download, batch_size=args.batch_size, low_vram=args.low_vram)
    if args.command == "diagnostic":
        diagnostic(args.root, args.output, encoder)
        return
    if args.command == "controlled":
        rows = [json.loads(s) for s in args.corpus.read_text(encoding="utf-8").splitlines() if s.strip()]
        write_json(args.output / "contextos.json", controlled(rows, encoder))
        inputs = [args.corpus]
        config = {"command": args.command, "encoder": encoder.info}
    else:
        nli = NLI(device=args.device, local_only=not args.download, batch_size=args.batch_size, low_vram=args.low_vram)
        qpath = args.root / "content/questions.json"
        questions = json.loads(qpath.read_text(encoding="utf-8"))
        if args.question_limit:
            questions = questions[:args.question_limit]
        result = robustness(args.text.read_text(encoding="utf-8"), questions, encoder, nli, top_k=args.top_k)
        write_json(args.output / "documento.json", result)
        if args.selected_run:
            write_json(args.output / "transferencia_externa.json", apply_frozen(
                result["base"]["items"], args.selected_run, args.device,
                batch_size=args.batch_size, low_vram=args.low_vram))
        inputs = [qpath, args.text]
        if args.sabia:
            ref = json.loads(args.sabia.read_text(encoding="utf-8"))
            if ref.get("document_sha256") != result["base"]["document_sha256"]:
                raise ValueError("Comparador Sabiá não identifica o mesmo documento por hash")
            write_json(args.output / "sabia_concordancia.json", sabia_agreement(result["base"]["items"], ref["items"], ref["config"]))
            inputs.append(args.sabia)
        config = {"command": args.command, "encoder": encoder.info, "nli": nli.info,
                  "question_limit": args.question_limit, "top_k": args.top_k,
                  "partial_instrument": args.question_limit is not None, "model_selection": "baseline_exploratorio_sem_selecao_externa"}
    write_json(args.output / "manifest.json", manifest(config, inputs, started))


if __name__ == "__main__":
    main()
