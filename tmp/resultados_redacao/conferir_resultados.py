from pathlib import Path
from collections import Counter, defaultdict
import csv
import json
import statistics
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
AXES = ['economic', 'diplomatic', 'state', 'society']

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def compact_stats(regs):
    out = {'trechos': len(regs)}
    for name in ['latencia_jev_s', 'latencia_llm_s', 'latencia_total_s']:
        vals = [r[name] for r in regs if isinstance(r.get(name), (int, float))]
        out[name] = {'n': len(vals), 'media': statistics.mean(vals), 'mediana': statistics.median(vals), 'min': min(vals), 'max': max(vals)} if vals else None
    for name in ['chamadas_llm', 'chamadas_llm_efetivas', 'chamadas_jev', 'tentativas_jev', 'chamadas_jev_evidencias']:
        out[name] = sum(r.get(name, 0) or 0 for r in regs)
    out['trechos_com_llm'] = sum(bool(r.get('chamadas_llm')) for r in regs)
    out['eixos_encaminhados'] = sum(len(r.get('eixos_encaminhados', [])) for r in regs)
    for stage in ['eixos_jev', 'eixos']:
        counts = Counter()
        by_axis = defaultdict(Counter)
        errors = []
        citations = Counter()
        changes = Counter()
        for r in regs:
            for ax,d in r[stage].items():
                state = 'abstencao' if d.get('relevante') is None or (d.get('relevante') and d.get('nivel') is None) else 'irrelevante' if d.get('relevante') is False else 'sem_posicao' if d.get('nivel') == 0 else 'direcional'
                counts[state] += 1
                by_axis[ax][state] += 1
                if d.get('erro_llm'): errors.append(d['erro_llm'])
                if d.get('relevante') and d.get('nivel') is not None:
                    citations[str(d.get('evidencia_verificada'))] += 1
                if stage == 'eixos':
                    prev = r['eixos_jev'][ax]
                    if (d.get('relevante'), d.get('nivel')) != (prev.get('relevante'), prev.get('nivel')):
                        changes[ax] += 1
        out[stage] = {'estados': dict(counts), 'por_eixo': {k:dict(v) for k,v in by_axis.items()}, 'erros_llm': errors, 'citacoes_decisoes_relevantes':dict(citations), 'alteracoes':dict(changes)}
    return out

summary = {}
bench = ROOT/'runs/benchmark_8values/20261102T234056876423Z'
rows = [json.loads(l) for l in (bench/'benchmark.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
summary['benchmark'] = compact_stats([r['registro'] for r in rows if r.get('registro')])
summary['benchmark']['erros_lote'] = [r.get('erro') for r in rows if r.get('erro')]
details = list(csv.DictReader((bench/'benchmark_detalhes.csv').open(encoding='utf-8-sig',newline='')))
summary['metricas_benchmark'] = {}
for stage in ['eixos_jev','eixos']:
    ds = [d for d in details if d['etapa']==stage]
    relevant = [d for d in ds if d['relevância esperada']=='True']
    summary['metricas_benchmark'][stage] = {
        'pares':len(ds),'relevantes':len(relevant),
        'relevancia_acertos':sum(d['relevância correta']=='True' for d in ds),
        'direcao_acertos':sum(d['direção correta']=='True' for d in relevant),
        'conjunto_acertos':sum(d['acerto conjunto']=='True' for d in ds),
        'baseline_acertos':sum(d['referência tudo irrelevante']=='True' for d in ds),
        'matriz_relevancia':dict(Counter(('R' if d['relevância esperada']=='True' else 'I')+'_'+('R' if d['relevância prevista']=='True' else 'I' if d['relevância prevista']=='False' else 'A') for d in ds))
    }
summary['benchmark_por_eixo'] = list(csv.DictReader((bench/'benchmark_comparacao.csv').open(encoding='utf-8-sig',newline='')))

texts = ROOT/'runs/testes_textos/20261112T010422966692Z'
docs = [(p.parent.name, load(p)) for p in sorted(texts.glob('*/resultado.json'))]
regs = [r for _,d in docs for r in d['registros']]
summary['textos'] = compact_stats(regs)
summary['textos']['documentos'] = len(docs)
summary['textos']['status'] = dict(Counter(str(load(p).get('concluido')) for p in texts.glob('*/status.json')))
summary['textos']['indice_documentos'] = dict(Counter(c['eixo'] for _,d in docs for c in d['cobertura'] if c.get('índice A') is not None))
summary['textos']['grupos'] = {}
for g in ['textos_pequenos','textos_grandes']:
    gd = [(name,d) for name,d in docs if name.startswith(g)]
    summary['textos']['grupos'][g]={'documentos':len(gd),'trechos':sum(len(d['registros']) for _,d in gd)}
summary['casos_textos'] = []
for name,d in docs:
    summary['casos_textos'].append({'id':name,'texto':d['original']['texto'][:250], 'trechos':len(d['registros']), 'indices':{c['eixo']:c.get('índice A') for c in d['cobertura']}, 'sem_citacao':[(i,ax) for i,r in enumerate(d['registros']) for ax,v in r['eixos'].items() if v.get('relevante') and v.get('nivel') is not None and v.get('evidencia_verificada') is not True]})
summary['auditoria'] = dict(Counter(str(a)[:250] for r in regs for d in r['eixos'].values() for a in d.get('evidence_audit',[]) if a))
(OUT/'metricas_conferidas.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['casos_textos','auditoria','benchmark_por_eixo']},ensure_ascii=False,indent=2))
print('CASOS')
for d in summary['casos_textos']: print(json.dumps(d,ensure_ascii=False))
