"""Executa APENAS as células novas; nunca roda o restante do TCC.ipynb.

Uso: .venv/Scripts/python.exe analise_jev_llm/executar_cookbooks.py [--live]
Salva outputs reais no notebook. --live habilita até 180 chamadas conforme config.
"""
import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PATH = ROOT / "TCC.ipynb"
TAG = "tcc-jev-cookbooks-v1"


def main():
    if "--live" in sys.argv:
        os.environ["TCC_COOKBOOKS_LIVE"] = "1"
    else:
        os.environ.pop("TCC_COOKBOOKS_LIVE", None)
    if "--resume" in sys.argv:
        os.environ["TCC_COOKBOOKS_OUTPUT"] = sys.argv[sys.argv.index("--resume") + 1]
    os.chdir(ROOT)
    nb = json.loads(PATH.read_text(encoding="utf-8"))
    namespace = {}
    count = 0
    for index, c in enumerate(nb["cells"]):
        if TAG not in c.get("metadata", {}).get("tags", []) or c["cell_type"] != "code":
            continue
        count += 1
        outputs, stream = [], io.StringIO()
        def flush():
            value = stream.getvalue()
            if value:
                outputs.append({"output_type": "stream", "name": "stdout", "text": value.splitlines(True)})
                print(value, end="", flush=True, file=sys.__stdout__)
                stream.seek(0)
                stream.truncate(0)
        def display(value):
            flush()
            data = {"text/plain": repr(value)}
            if hasattr(value, "_repr_html_"):
                data["text/html"] = value._repr_html_()
            outputs.append({"output_type": "display_data", "metadata": {}, "data": data})
        print(f"Célula {index}: {c['id']}", flush=True)
        try:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                exec(compile("".join(c["source"]), f"TCC.ipynb:cell-{index}", "exec"), namespace)
                # A configuração importa display; substituímos depois desse import.
                namespace["_cb_display"] = display
        except Exception as error:
            flush()
            outputs.append({"output_type": "error", "ename": type(error).__name__,
                            "evalue": "Falha na execução da célula; mensagem omitida para proteger credenciais.",
                            "traceback": []})
            print("CELL_ERROR", type(error).__name__, flush=True)
        flush()
        c["execution_count"], c["outputs"] = count, outputs
        c["metadata"]["cookbooks_execution"] = {"live": "--live" in sys.argv}
        temporary = PATH.with_suffix(".cookbooks.tmp")
        temporary.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for attempt in range(5):
            try:
                temporary.replace(PATH)
                break
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(.5)
    lab = namespace.get("cb_lab")
    if lab:
        lab.close()
        print("RESULT_DIRECTORY", lab.output)
        if any(s["status"] != "concluido" for s in lab.status):
            sys.exit(2)


if __name__ == "__main__":
    main()
