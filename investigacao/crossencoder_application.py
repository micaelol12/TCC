"""R4/R5/R6/R10: congela cabeça conjunta e transfere para diagnósticos/documento.

Sem validar intensidade, sem usar documento como gabarito, sem calibração nova.
"""
from collections import Counter
import json
from pathlib import Path
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from .bge_dev import BinaryNLI
from .experimentos import manifest
from .lexical_dev import topic_weights
from .protocolo import write_json
from .transferencia_8values import cases, summarize


def run(root):
    """R4/R6/R10: C vem de dev; cabeça final usa treino, nunca teste/documentos."""
    import joblib
    import torch
    output=root/'analises/execucoes/crossencoder_application_20260917'
    if output.exists():raise ValueError('Use saída nova')
    if not torch.cuda.is_available():raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4);torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
    runs=root/'analises/execucoes';dev_run=runs/'crossencoder_head_dev_20260917'
    selected=json.loads((dev_run/'selection.json').read_text(encoding='utf-8'))
    c=float(selected['candidate'][1:])
    corpus=root/'analises/dados/brmoral_20260917/corpus.jsonl'
    rows=[json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    by_id={r['id']:r for r in rows};cache=np.load(dev_run/'features.npz',allow_pickle=False)
    indices=[i for i,key in enumerate(cache['ids']) if by_id[str(key)]['split']=='train']
    train=[by_id[str(cache['ids'][i])] for i in indices]
    protocol={'C':c,'training_ids':[r['id'] for r in train],'confidence':.7,'intensity_inferred':False,
              'use':'exploratory transfer','hypothesis':'O autor concorda com a seguinte afirmação: {question}'}
    write_json(output/'protocol.json',protocol)
    head=LogisticRegression(C=c,max_iter=2000,random_state=13)
    head.fit(cache['features'][indices],[r['label'] for r in train],sample_weight=topic_weights(train))
    joblib.dump(head,output/'head.joblib')
    model=BinaryNLI(str(root/'analises/modelos/bge-m3-zeroshot-v2'));captured=[]

    def capture(module,args):
        """R10: mesma representação conjunta, somente leitura."""
        captured.append(args[0][0].detach().float().cpu().numpy())

    handle=model.model.classifier.out_proj.register_forward_pre_hook(capture)

    def predict(text,target):
        """R4/R10: par textual, normalização e cabeça idênticos à avaliação natural."""
        captured.clear()
        model.predict(text,f'O autor concorda com a seguinte afirmação: {target}')
        x=captured[0];x=x/max(float(np.linalg.norm(x)),1e-12)
        p=head.predict_proba(x[None])[0];label=str(head.classes_[int(np.argmax(p))])
        return {'prediction':label,'state':('favoravel' if label=='favor' else 'contraria') if max(p)>=.7 else 'incerta',
                'score':float(p[list(head.classes_).index('favor')]),'probabilities':dict(zip(head.classes_,map(float,p)))}

    qpath=root/'content/questions.json';questions=json.loads(qpath.read_text(encoding='utf-8'))
    controlled=[{**r,'method':'crossencoder_head',**predict(r['text'],r['target'])} for r in cases(questions)]
    write_json(output/'controlled_predictions.json',controlled)
    write_json(output/'controlled_metrics.json',summarize(controlled))
    docpath=runs/'documento_6x1_brmoral_gpu_20260917/documento.json'
    document=json.loads(docpath.read_text(encoding='utf-8'))['base'];items=[]
    for item in document['items']:
        evidence=[{**e,'external_stance':predict(e['text'],item['question'])} for e in item['evidence']]
        signs={e['external_stance']['state'] for e in evidence}&{'favoravel','contraria'}
        state='sem_evidencia' if not evidence else 'conflito' if len(signs)>1 else next(iter(signs),'incerta')
        items.append({'question_id':item['question_id'],'question':item['question'],'state':state,
                      'response':None,'evidence':evidence,'label_source':'sem_rotulo'})
    handle.remove()
    write_json(output/'document_transfer.json',{'items':items,'counts':dict(Counter(i['state'] for i in items)),
               'exploratory':True,'document_sha256':document['document_sha256'],'no_intensity_scale':True})
    write_json(output/'manifest.json',manifest({**protocol,'model':model.info},[corpus,qpath,docpath,Path(__file__)],started))
    print(json.dumps(summarize(controlled)[0],indent=2));print(Counter(i['state'] for i in items))


if __name__=='__main__':
    run(Path.cwd())
