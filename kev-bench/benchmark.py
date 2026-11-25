"""Same match-situation benchmark for official Kev and its unadapted Qwen base."""
from dataclasses import replace
from pathlib import Path
import argparse, gc, json, math, os, random, statistics, time
import torch
from kev.api import SystemOneRequest
from kev.checkpoint import Checkpoint, LoadOptions
from kev.serve import Server

options_path=Path(__file__).with_name('scenarios.json')
data=json.loads(options_path.read_text())
cases=data['cases']+data['counterfactuals']
base_revision='dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68'
random_seed=865418
FAMILIES=('brief','coach')
TOKENS=('A','B','C','D')
def p95(values):
    return round(sorted(values)[max(0,math.ceil(.95*len(values))-1)],2)
def timing(rows):
    ms=[r['wallMs'] for r in rows]
    return {'n':len(rows),'top1':sum(r['choice']==r['expected'] for r in rows),'p50ms':round(statistics.median(ms),2),
        'p95ms':p95(ms),'under100ms':sum(x<=100 for x in ms),'under500ms':sum(x<=500 for x in ms)}
def settings(family):
    if family=='brief':return 'Choose the best game move now.', ''.join(())
    return ('Pick the first applicable tactic: close the gap when out of range; block an imminent hit; '
        'throw a guarding enemy within grab range; strike exposed recovery within strike range.', '')
def specs():
    rng=random.Random(random_seed)
    for row in cases:
        o=list(data['options']); rng.shuffle(o)
        yield row,o
def add(rows,name,state,expected,family,order_index,order,fn):
    q,_=settings(family)
    start=time.perf_counter()
    d=fn(state,q,{k:data['options'][k] for k in order})
    elapsed=(time.perf_counter()-start)*1000
    assert set(d)==set(order) and all(math.isfinite(v) and v>=0 for v in d.values())
    pick=max(order,key=d.get)
    rows.append({'scenario':name,'family':family,'order':order_index,'options':order,'expected':expected,
        'choice':pick,'wallMs':round(elapsed,2),'probabilities':d})

def score(name,fn,rows):
    for (tag,state,expected),order in specs():
        for fam in FAMILIES:
            for order_index,o in enumerate([order,list(reversed(order))]):
                add(rows,tag,state,expected,fam,order_index,o,fn)
    output={}
    for f in FAMILIES:
        rs=[r for r in rows if r['family']==f]
        summary=timing(rs)
        summary['orderStableOf14']=sum(rs[i]['choice']==rs[i+1]['choice'] for i in range(0,len(rs),2))
        summary['counterfactualCorrectOf2']=sum(r['choice']==r['expected'] for r in rs if r['scenario'].startswith('paired-') and r['order']==0)
        output[f]=summary
    print(json.dumps({'model':name,'summary':output}),flush=True)
    return output

def variant(rows,seed,temperature,margin):
    r=random.Random(seed); n=0;correct=0;hist={}
    for row in rows:
        ps=row['probabilities']
        ordered=sorted(ps,key=lambda k:-ps[k])
        if ps[ordered[0]]-ps[ordered[1]] < margin:continue
        pred=ordered[0] if temperature==0 else r.choices(ordered,[max(ps[x],1e-12)**(1/temperature) for x in ordered])[0]
        n+=1;correct+=pred==row['expected'];hist[pred]=hist.get(pred,0)+1
    return {'seed':seed,'sampleTemperature':temperature,'minMargin':margin,'covered':n,'correct':correct,'moves':hist}

def main():
    p=argparse.ArgumentParser();p.add_argument('pack',type=Path);p.add_argument('out',type=Path);p.add_argument('--threads',type=int,default=3);a=p.parse_args()
    torch.set_num_threads(a.threads);torch.set_num_interop_threads(1)
    baseline=a.pack/'hf'/'hub'/'models--Qwen--Qwen3.5-0.8B-Base'/'snapshots'/base_revision
    result={'schema':1,'latencyScope':'CPU wall time per decision, output decoding included; warm-up excluded','seed':random_seed,
       'scenarios':len(cases),'fixedOptions':list(data['options']),'threads':a.threads,'models':{}}
    ck=Checkpoint(str(a.pack/'kev-0.8b'))
    tok,m=ck.load('cpu',replace(LoadOptions.from_env(),dtype=torch.bfloat16,backend='torch'))
    srv=Server(ck,tok,m,'cpu',release_date='2026-09-24')
    def kev(state,question,choices):
        req=SystemOneRequest.model_validate({'state':state,'questions':{'move':{'type':'choice','instructions':question,'criteria':choices}}})
        return srv.answer(req)['answers']['move']['probabilities']
    try:
        kev('Rival far away. Choose a move.','Choose action.',data['options'])
        rows=[]
        result['models']['kev-0.8b']={'temperature':m.head.temperature,'summary':score('kev-0.8b',kev,rows),'rows':rows}
        result['models']['kev-0.8b']['sweep']=[variant(rows,random_seed+s,t,mg) for s,t,mg in [(0,0,0),(1,.35,0),(2,.7,0),(3,1,0),(0,0,.10),(0,0,.20)]]
        a.out.write_text(json.dumps(result,separators=(',',':')))
    finally:srv.close()
    del srv,m,tok,ck;gc.collect()
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    qtok=AutoTokenizer.from_pretrained(str(baseline),local_files_only=True)
    qmod=Qwen3_5ForConditionalGeneration.from_pretrained(str(baseline),local_files_only=True,dtype=torch.bfloat16).eval()
    ids=[qtok.encode(x,add_special_tokens=False) for x in TOKENS]
    assert all(len(x)==1 for x in ids) and len(set(x[0] for x in ids))==len(TOKENS)
    ids=torch.tensor([x[0] for x in ids])
    def qwen(state,question,choices):
        options='\n'.join(f'{s}. {k}: {v}' for s,(k,v) in zip(TOKENS,choices.items()))
        doc=f'Game: FightingICE.\nState: {state}\nQuestion: {question}\n{options}\nAnswer:'
        with torch.inference_mode():
            t=qtok(doc,return_tensors='pt')
            out=qmod(**t,logits_to_keep=1,use_cache=False).logits[0,-1,ids].float().softmax(-1).tolist()
        return dict(zip(choices,out))
    qwen('Rival far away.','Choose action.',data['options'])
    rows=[]
    result['models']['qwen3.5-base-0.8b']={'summary':score('qwen3.5-base-0.8b',qwen,rows),'rows':rows}
    a.out.write_text(json.dumps(result,separators=(',',':')))
if __name__=='__main__':main()
