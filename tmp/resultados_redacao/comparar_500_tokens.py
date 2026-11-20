from pathlib import Path
from collections import Counter
import csv
import json
import statistics
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def bench(name):
    p=ROOT/'runs/benchmark_8values'/name
    return p,[json.loads(l) for l in (p/'benchmark.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
def texts(name):
    p=ROOT/'runs/testes_textos'/name
    return p,{f.parent.name:load(f) for f in sorted(p.glob('*/resultado.json'))}
def state(d):
    if d.get('relevante') is None or (d.get('relevante') and d.get('nivel') is None):return 'abstencao'
    if not d.get('relevante'):return 'irrelevante'
    return 'sem_posicao' if d.get('nivel')==0 else 'direcional'
def stats(regs):
    out={'trechos':len(regs)}
    for key in ['chamadas_llm','chamadas_llm_efetivas','chamadas_jev','tentativas_jev','chamadas_jev_evidencias']:
        out[key]=sum(r.get(key,0) or 0 for r in regs)
    out['eixos_encaminhados']=sum(len(r.get('eixos_encaminhados',[])) for r in regs)
    out['trechos_com_llm']=sum(bool(r.get('chamadas_llm')) for r in regs)
    for key in ['latencia_jev_s','latencia_llm_s','latencia_total_s']:
        vals=[r[key] for r in regs if r.get(key) is not None]
        out[key]={'media':statistics.mean(vals),'mediana':statistics.median(vals),'min':min(vals),'max':max(vals)}
    for stage in ['eixos_jev','eixos']:
        ds=[d for r in regs for d in r[stage].values()]
        relevant=[d for d in ds if d.get('relevante') and d.get('nivel') is not None]
        out[stage]={'estados':dict(Counter(state(d) for d in ds)), 'evidencias_relevantes':dict(Counter(str(d.get('evidencia_verificada')) for d in relevant)), 'erros_llm':dict(Counter(str(d['erro_llm']) for d in ds if d.get('erro_llm')))}
    return out
def metrics(path):
    ds=list(csv.DictReader((path/'benchmark_detalhes.csv').open(encoding='utf-8-sig',newline='')))
    out={}
    for stage in ['eixos_jev','eixos']:
        selected=[r for r in ds if r['etapa']==stage]
        relevant=[r for r in selected if r['relevância esperada']=='True']
        out[stage]={'pares':len(selected),'relevantes':len(relevant),'relevancia_acertos':sum(r['relevância correta']=='True' for r in selected),'direcao_acertos':sum(r['direção correta']=='True' for r in relevant),'conjunto_acertos':sum(r['acerto conjunto']=='True' for r in selected),'matriz':dict(Counter(('R' if r['relevância esperada']=='True' else 'I')+'_'+('R' if r['relevância prevista']=='True' else 'I' if r['relevância prevista']=='False' else 'A') for r in selected))}
    return out
def diffs(a,b,p=''):
    out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:out.append({'campo':p+'.'+k,'antes':a.get(k),'depois':b.get(k)})
            else:out.extend(diffs(a[k],b[k],p+'.'+k))
    elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        for i,(x,y) in enumerate(zip(a,b)):out.extend(diffs(x,y,p+f'[{i}]'))
    elif a!=b:out.append({'campo':p,'antes':a,'depois':b})
    return out

bo,br0=bench('20261102T234056876423Z');bn,br1=bench('20261119T231821798499Z')
to,td0=texts('20261119T232249372371Z');tn,td1=texts('20261120T004756244359Z')
bregs0=[r['registro'] for r in br0 if r.get('registro')];bregs1=[r['registro'] for r in br1 if r.get('registro')]
tregs0=[r for d in td0.values() for r in d['registros']];tregs1=[r for d in td1.values() for r in d['registros']]
report={'benchmark':{'antes':stats(bregs0),'depois':stats(bregs1),'metricas_antes':metrics(bo),'metricas_depois':metrics(bn),'erros_depois':sum(bool(r.get('erro')) for r in br1),'mesmas_perguntas':load(bo/'manifesto.json')['hash_perguntas']==load(bn/'manifesto.json')['hash_perguntas']},'textos':{'antes':stats(tregs0),'depois':stats(tregs1),'documentos_antes':len(td0),'documentos_depois':len(td1),'status_depois':dict(Counter(str(load(p).get('concluido')) for p in tn.glob('*/status.json'))),'ids_iguais':td0.keys()==td1.keys(),'originais_iguais':all(td0[k]['original']==td1[k]['original'] for k in td0),'trechos_iguais':all([r['texto'] for r in td0[k]['registros']]==[r['texto'] for r in td1[k]['registros']] for k in td0)}}
report['mudancas_indices']=[]
for k in td0:
    a={r['eixo']:r.get('índice A') for r in td0[k]['cobertura']};b={r['eixo']:r.get('índice A') for r in td1[k]['cobertura']}
    for ax in a:
        if a[ax]!=b[ax]:report['mudancas_indices'].append({'id':k,'eixo':ax,'antes':a[ax],'depois':b[ax],'texto':td1[k]['original']['texto'][:250]})
report['mudancas_decisoes']={}
for label,old,new in [('benchmark',bregs0,bregs1),('textos',tregs0,tregs1)]:
    stages={}
    if len(old)!=len(new) or any(a['texto']!=b['texto'] for a,b in zip(old,new)):
        report['mudancas_decisoes'][label]={'observacao':'Segmentações diferentes; comparação por trecho não aplicada.'}
        continue
    for stage in ['eixos_jev','eixos']:
        changed=[];raw_diffs=0
        for i,(a,b) in enumerate(zip(old,new)):
            assert a['texto']==b['texto']
            raw_diffs+=a.get('resposta_jev_bruta')!=b.get('resposta_jev_bruta')
            for ax in a[stage]:
                x,y=a[stage][ax],b[stage][ax]
                if (x.get('relevante'),x.get('nivel'))!=(y.get('relevante'),y.get('nivel')):
                    changed.append({'indice':i,'eixo':ax,'antes':[x.get('relevante'),x.get('nivel')],'depois':[y.get('relevante'),y.get('nivel')],'texto':b['texto'][:170]})
        stages[stage]={'alteradas':len(changed),'detalhes':changed,'respostas_jev_brutas_distintas':raw_diffs}
    report['mudancas_decisoes'][label]=stages
report['diferencas_config_benchmark']=diffs(bregs0[0]['config'],bregs1[0]['config'])
report['diferencas_config_textos']=diffs(tregs0[0]['config'],tregs1[0]['config'])
api=load(ROOT/'app/api/analysis-config.json')
report['diferencas_api_escala']=diffs(api['escala'],tregs1[0]['config']['escala'])
report['contexto_textos_igual_api']=api['contexto_posicao_politica']==tregs1[0]['config'].get('contexto_posicao_politica')
report['contexto_benchmark_igual_api']=api['contexto_posicao_politica']==bregs1[0]['config'].get('contexto_posicao_politica')
report['segmentacao_api']=api.get('chunk_tokens')
report['segmentacao_teste']=load(tn/'protocolo.json')['preparacao_e_exibicao']['chunks']
report['indices_documentos_antes']=sum(c.get('índice A') is not None for d in td0.values() for c in d['cobertura'])
report['indices_documentos_depois']=sum(c.get('índice A') is not None for d in td1.values() for c in d['cobertura'])
out=Path(__file__).parent/'comparacao_500_tokens.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in report.items():
    if k.startswith('diferencas'):
        print(k,'TOTAL',len(v))
        for change in v:print(change['campo'], str(change['antes'])[:180],'=>',str(change['depois'])[:180])
    elif k=='mudancas_decisoes':
        print(k,v)
    else:print(k,json.dumps(v,ensure_ascii=False,indent=2))
print('REPORT',out)
