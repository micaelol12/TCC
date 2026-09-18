"""R4/R6/R10: cabeça linear sobre representação cruzada BGE congelada.

Adaptação, não SetFit original: representação conjunta premissa/hipótese extraída
antes de out_proj do classificador BGE; sem alterar pesos do transformer.
"""
import json
import argparse
from pathlib import Path
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from .bge_dev import BinaryNLI
from .experimentos import manifest
from .lexical_dev import topic_weights
from .nli_bilateral import hypotheses
from .protocolo import classification_metrics, connected_groups, grouped_bootstrap, write_json


def run(root):
    """R4/R6/R10: representação na GPU, classificação por tema reservado no dev."""
    import torch
    output = root / 'analises/execucoes/crossencoder_head_dev_20260917'
    if output.exists():
        raise ValueError('Use saída nova')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4);torch.cuda.reset_peak_memory_stats()
    started=time.perf_counter()
    corpus=root/'analises/dados/brmoral_20260917/corpus.jsonl'
    rows=[json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    rows=[r for r in rows if r['split'] in {'train','dev'}]
    protocol={'features':'BGE classifier out_proj input; normalized L2', 'template':'concordancia positive',
              'cs':[.01,.1,1.,10.], 'weighting':'equal topic/class mass', 'encoder_frozen':True,
              'evaluation':'dev target excluded from train', 'test_used':False}
    write_json(output/'protocol.json',protocol)
    model=BinaryNLI(str(root/'analises/modelos/bge-m3-zeroshot-v2'))
    captured=[]

    def capture(module, args):
        """R10: hook de leitura, representação do par sem gradiente ou alteração."""
        captured.append(args[0][0].detach().float().cpu().numpy())

    handle=model.model.classifier.out_proj.register_forward_pre_hook(capture)
    for i,row in enumerate(rows):
        model.predict(row['text'], hypotheses(row['target'])['concordancia'][0])
        if (i+1)%500==0:
            print(f'{i+1}/{len(rows)} representações conjuntas',flush=True)
    handle.remove()
    x=np.array(captured)
    if x.shape != (len(rows),1024) or not np.isfinite(x).all():
        raise ValueError('Representações inválidas')
    x=x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
    np.savez_compressed(output/'features.npz', features=x, ids=np.array([r['id'] for r in rows]))
    results=[]
    for target in sorted({r['target'] for r in rows}):
        ti=[i for i,r in enumerate(rows) if r['split']=='train' and r['target']!=target]
        di=[i for i,r in enumerate(rows) if r['split']=='dev' and r['target']==target]
        train=[rows[i] for i in ti]
        assert not {r['author_id'] for r in train}&{rows[i]['author_id'] for i in di}
        for c in [.01,.1,1.,10.]:
            head=LogisticRegression(C=c,max_iter=2000,random_state=13)
            head.fit(x[ti],[r['label'] for r in train],sample_weight=topic_weights(train))
            p=head.predict(x[di])
            results.extend({'id':rows[i]['id'],'target':target,'truth':rows[i]['label'],
                            'prediction':str(v),'candidate':f'C{c}'} for i,v in zip(di,p))
    metrics=[]
    for candidate in sorted({r['candidate'] for r in results}):
        s=[r for r in results if r['candidate']==candidate];topics=[]
        for target in sorted({r['target'] for r in s}):
            t=[r for r in s if r['target']==target]
            topics.append({'target':target,**classification_metrics([r['truth'] for r in t],[r['prediction'] for r in t])})
        mean=float(np.mean([r['balanced_accuracy'] for r in topics]));minimum=min(r['balanced_accuracy'] for r in topics)
        metrics.append({'candidate':candidate,'mean_topic_ba':mean,'min_topic_ba':minimum,
                        'satisfies_provisional_criterion':mean>=.75 and minimum>=.6,'topics':topics,
                        'global':classification_metrics([r['truth'] for r in s],[r['prediction'] for r in s])})
    metrics.sort(key=lambda r:(-r['mean_topic_ba'],-r['min_topic_ba']))
    write_json(output/'predictions.json',results);write_json(output/'metrics.json',metrics)
    write_json(output/'selection.json',metrics[0])
    write_json(output/'manifest.json',manifest({**protocol,'model':model.info},[corpus,Path(__file__)],started))
    print(json.dumps([{k:v for k,v in r.items() if k not in {'topics','global'}} for r in metrics],indent=2))


def evaluate_test(root):
    """R4/R6/R10: tema fora de treino e dev; escolhe C no dev dos demais temas."""
    import torch
    import joblib
    runs = root / 'analises/execucoes'
    dev_run = runs / 'crossencoder_head_dev_20260917'
    output = runs / 'crossencoder_head_test_20260917'
    if output.exists():
        raise ValueError('Use saída nova')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível')
    torch.set_num_threads(4); torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    corpus = root / 'analises/dados/brmoral_20260917/corpus.jsonl'
    rows = [json.loads(s) for s in corpus.read_text(encoding='utf-8').splitlines() if s.strip()]
    row_by_id = {r['id']:r for r in rows}
    archive = np.load(dev_run / 'features.npz', allow_pickle=False)
    ids = archive['ids'].tolist(); features = archive['features']
    source = [row_by_id[i] for i in ids]
    assert all(r['split'] in {'train','dev'} for r in source)
    protocol = {'approach': 'frozen BGE crossencoder features + logistic regression',
                'cs':[.01,.1,1.,10.], 'C_selection':'mean topic BA on dev of other topics',
                'training_and_dev_exclude_test_topic':True,'threshold':.5,
                'test_previously_inspected':True,'approach_selected_using_development':True}
    write_json(output / 'protocol.json', protocol)
    heads, selections = {}, []
    for index,target in enumerate(sorted({r['target'] for r in source})):
        ti=[i for i,r in enumerate(source) if r['split']=='train' and r['target']!=target]
        di=[i for i,r in enumerate(source) if r['split']=='dev' and r['target']!=target]
        train=[source[i] for i in ti]; candidates=[]
        for c in [.01,.1,1.,10.]:
            head=LogisticRegression(C=c,max_iter=2000,random_state=13)
            head.fit(features[ti],[r['label'] for r in train],sample_weight=topic_weights(train))
            pred=head.predict(features[di]).tolist()
            bas=[]
            for t in sorted({source[i]['target'] for i in di}):
                positions=[j for j,i in enumerate(di) if source[i]['target']==t]
                bas.append(classification_metrics([source[di[j]]['label'] for j in positions],
                                                  [pred[j] for j in positions])['balanced_accuracy'])
            candidates.append((float(np.mean(bas)),-c,head))
        score,_,head=max(candidates,key=lambda v:v[:2])
        heads[target]=head
        selections.append({'target':target,'C':head.C,'dev_mean_topic_ba':score,
                           'train_ids':[source[i]['id'] for i in ti], 'dev_ids':[source[i]['id'] for i in di]})
        joblib.dump(head,output/f'head_{index}.joblib')
    write_json(output / 'frozen_selections.json', selections)
    model=BinaryNLI(str(root/'analises/modelos/bge-m3-zeroshot-v2'))
    captured=[]

    def capture(module,args):
        """R10: mesma representação anterior, leitura sem gradiente."""
        captured.append(args[0][0].detach().float().cpu().numpy())

    handle=model.model.classifier.out_proj.register_forward_pre_hook(capture)
    test=[r for r in rows if r['split']=='test']
    for i,row in enumerate(test):
        model.predict(row['text'],hypotheses(row['target'])['concordancia'][0])
        if (i+1)%200==0: print(f'{i+1}/{len(test)} teste',flush=True)
    handle.remove()
    x=np.array(captured);x=x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
    predictions=[]
    for row,feature in zip(test,x):
        head=heads[row['target']];p=head.predict_proba(feature[None])[0]
        label=str(head.classes_[int(np.argmax(p))])
        predictions.append({'id':row['id'],'target':row['target'],'truth':row['label'],'prediction':label,
                            'probabilities':dict(zip(head.classes_,map(float,p)))})
    topics=[]
    for target in sorted(heads):
        s=[r for r in predictions if r['target']==target]
        topics.append({'target':target,**classification_metrics([r['truth'] for r in s],[r['prediction'] for r in s])})
    mean=float(np.mean([r['balanced_accuracy'] for r in topics]));minimum=min(r['balanced_accuracy'] for r in topics)
    metrics={'mean_topic_ba':mean,'min_topic_ba':minimum,'satisfies_provisional_criterion':mean>=.75 and minimum>=.6,
             'topics':topics,'global':classification_metrics([r['truth'] for r in predictions],[r['prediction'] for r in predictions])}
    old=json.loads((runs/'temas_reservados_gpu_20260917/predictions.json').read_text(encoding='utf-8'))
    intervals=[]
    for method in ['e5_tema_reservado','nli_posicao_autor']:
        previous={r['id']:r for r in old if r['method']==method}
        if set(previous)!={r['id'] for r in predictions}:
            raise ValueError('Comparador incompatível')
        intervals.append({'comparison':'crossencoder_menos_'+method,
            **grouped_bootstrap([r['truth'] for r in predictions],[r['prediction'] for r in predictions],
                                [previous[r['id']]['prediction'] for r in predictions],connected_groups(test),seed=13)})
    write_json(output/'predictions.json',predictions);write_json(output/'metrics.json',metrics)
    write_json(output/'intervals.json',intervals)
    write_json(output/'manifest.json',manifest({**protocol,'model':model.info},[corpus,Path(__file__)],started))
    print(json.dumps({k:v for k,v in metrics.items() if k!='topics'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluate-test',action='store_true')
    args=parser.parse_args()
    if args.evaluate_test:
        evaluate_test(Path.cwd())
    else:
        run(Path.cwd())
