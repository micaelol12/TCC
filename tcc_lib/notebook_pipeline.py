"""Carrega somente definições explicitamente exportadas pelo notebook autoritativo.

Nenhuma célula de demonstração, leitura de dados, credenciais ou chamada real é executada.
O namespace é novo a cada carregamento, inclusive para comparações simultâneas.
"""
import ast
import json
from pathlib import Path


def carregar_pipeline_notebook(caminho=None, *, namespace=None):
    caminho = Path(caminho) if caminho else Path(__file__).resolve().parents[1] / "Pipeline - Passo a Passo.ipynb"
    notebook = json.loads(caminho.read_text(encoding="utf-8"))
    ns = {"__name__": "pipeline_notebook", "__file__": str(caminho)} if namespace is None else namespace
    for cell in notebook["cells"]:
        exports = set(cell.get("metadata", {}).get("pipeline_exports", []))
        if cell["cell_type"] != "code" or not exports:
            continue
        nodes = []
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in exports:
                nodes.append(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)) and "@imports" in exports:
                nodes.append(node)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if all(isinstance(t, ast.Name) and t.id in exports for t in targets):
                    nodes.append(node)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(caminho), "exec"), ns)
    if not {"CascataJevLLM2Polos", "ESCALA_5_NIVEIS", "ESCALA_9_NIVEIS"} <= ns.keys():
        raise ValueError("Notebook sem o contrato exportado do pipeline.")
    return ns
