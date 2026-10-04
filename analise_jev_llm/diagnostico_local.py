"""Diagnóstico das funções originais do notebook, sem importar clientes ou chamar APIs."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
nb = json.loads((ROOT / "TCC.ipynb").read_text(encoding="utf-8"))
names = {
    "Result", "DecisaoEixo", "ResultadoProposta", "MAPA_SCORES_8VALUES",
    "EIXOS_8VALUES", "dividir_texto_em_chunks_caracteres",
    "_normalizar_distribuicao", "_extrair_decisao_jev",
    "_extrair_probabilidade_noul", "_extrair_decisao_jev_noul",
    "_decisao_fallback", "calcular_valor_esperado",
    "derivar_result_8values", "_agregar_resultados",
    "_converter_values_para_previsoes_benchmark", "_SCORE_TO_BENCHMARK_AXIS",
}
nodes = []
for i in (7, 294, 296):
    tree = ast.parse("".join(nb["cells"][i]["source"]))
    for node in tree.body:
        name = getattr(node, "name", None)
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in names:
            nodes.append(node)
ns = {"BaseModel": BaseModel}
exec("from typing import Literal\nfrom collections.abc import Mapping", ns)
module = ast.parse("from __future__ import annotations")
module.body.extend(nodes)
exec(compile(ast.fix_missing_locations(module), "funcoes_originais_notebook", "exec"), ns)
for name in ("Result", "DecisaoEixo", "ResultadoProposta"):
    ns[name].model_rebuild(_types_namespace=ns)

findings = {}
long_chunk = ns["dividir_texto_em_chunks_caracteres"]("x" * 3001, 1500)
assert len(long_chunk[0]) == 3001
findings["limite_caracteres"] = {"limite": 1500, "maior_chunk": len(long_chunk[0])}

def result_with_score(score):
    return SimpleNamespace(scores=SimpleNamespace(
        equality=score, peace=score, liberty=score, progress=score))

fallback = ns["_decisao_fallback"]("economico", 52.0)
converted = ns["_converter_values_para_previsoes_benchmark"](result_with_score(52.0))
assert fallback.classificacao == "neutro"
assert converted["economic"]["relevancia"]["choice"] == "A"
findings["limiares_distintos"] = {
    "score": 52, "classe_fallback": fallback.classificacao,
    "relevancia_adaptador_sem_descarte": converted["economic"]["relevancia"]["choice"],
}

axes = {axis: ns["_decisao_fallback"](axis, 52.0)
        for axis, _, _ in ns["MAPA_SCORES_8VALUES"].values()}
record = ns["ResultadoProposta"](proposta="teste sintético", eixos=axes, eixos_jev=axes)
with_drop = ns["_agregar_resultados"]([record], True)
without_drop = ns["_agregar_resultados"]([record], False)
assert with_drop.equality == 50 and without_drop.equality == 52
findings["descarte_troca_score"] = {
    "com_descarte": with_drop.equality, "sem_descarte": without_drop.equality,
}

uncertain = ns["DecisaoEixo"](eixo="economico", classificacao="igualdade", confianca=0,
    distribuicao={"igualdade": .5, "mercado": .5, "neutro": 0}, metodo="jev_system_one")
absent = ns["DecisaoEixo"](eixo="economico", classificacao="neutro", confianca=1,
    distribuicao={"igualdade": 0, "mercado": 0, "neutro": 1}, metodo="jev_system_one")
scores = [ns["calcular_valor_esperado"](d, "igualdade", "mercado") for d in (uncertain, absent)]
assert scores == [50, 50]
findings["perda_informacao"] = {"empate_polos": scores[0], "irrelevante": scores[1]}

noul = ns["_extrair_decisao_jev_noul"]("economico", SimpleNamespace(noul=.8),
    SimpleNamespace(choice="igualdade", confidence=.5,
                    probabilities={"igualdade": .75, "mercado": .25}), .5)
choice_confidence = (max(noul.distribuicao.values()) - 1/3) / (1 - 1/3)
assert abs(noul.confianca - .75) < 1e-9
assert abs(choice_confidence - .4) < 1e-9
findings["escalas_confianca"] = {
    "distribuicao": noul.distribuicao, "confianca_noul_notebook": noul.confianca,
    "formula_choice_documentacao_atual": round(choice_confidence, 6),
}

bad = ns["_decisao_fallback"]("economico", 120)
assert bad.confianca > 1 and min(bad.distribuicao.values()) < 0
findings["schema_sem_limites"] = bad.model_dump()

mapping_answer = ns["_extrair_decisao_jev"]("economico", {
    "choice": "igualdade", "confidence": .8,
    "probabilities": {"igualdade": .9, "mercado": .1}})
assert mapping_answer.classificacao == "neutro" and mapping_answer.distribuicao == {}
findings["dict_nao_suportado_pelo_extrator"] = mapping_answer.model_dump()

questions_path = ROOT / "tcc" / "questions.json"
if questions_path.exists():
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    positive = [q["id"] for q in questions if 10 in q["effect"].values()]
    absolute = [q["id"] for q in questions if any(abs(v) == 10 for v in q["effect"].values())]
    findings["filtro_efeitos"] = {
        "total": len(questions), "com_positivo_10": len(positive),
        "com_magnitude_10": len(absolute),
        "ids_excluidos_pelo_sinal": sorted(set(absolute) - set(positive)),
    }

print(json.dumps(findings, ensure_ascii=False, indent=2))
