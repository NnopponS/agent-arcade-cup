"""Fresh 100-entrant FightingICE tournament, verified engine KO only."""
import argparse
import concurrent.futures as cf
import fcntl
import hashlib
import json
import math
import random
import statistics
import time
import urllib.request
from pathlib import Path

from cross_trial import OPTIONS, allowed_at, bridge, observe
from lockstep_trial import sample

MODELS={'julia':(18085,'systemone'),'kev':(18086,'systemone'),'laya':(18088,'systemone'),'qwen':(18089,'completion'),'smol':(18090,'completion')}
PACE=24
STARTS=(0,18,36,0)
SEED=9252026
LABELS='ABCDE'
PROFILES=(
    'Balance attack and defense. At long range move toward the rival.',
    'Prefer pressure while an opponent cannot act. Close distance first when out of reach.',
    'Prefer defense when a hit is imminent, then strike an exposed rival.',
    'Favor low attacks and punish guarded opponents with a grab when very near.',
    'Prioritize landing strong attacks only when the rival is within reach.',
)
TEMPERATURES=(0,0.2,0.45,0.7)

def manifest():
    return [dict(id=f'{key.upper()}-{i+1:02}',model=key,profile=PROFILES[i//4],temperature=TEMPERATURES[i%4])
            for key in MODELS for i in range(20)]
def seeding(n):
    return [1] if n==1 else [j for i in seeding(n//2) for j in (i,n+1-i)]
def slots(entrants):
    order=list(entrants);random.Random(SEED).shuffle(order)
    return [order[i-1] if i<=len(order) else None for i in seeding(128)]
def bracket(entrants,results):
    cur=slots(entrants);rows=[]
    for rung in range(1,8):
        nxt=[]
        for i in range(0,len(cur),2):
            p,q=cur[i:i+2];mid=f'R{rung}-{1+i//2:02d}'
            if p is False or q is False: stat,winner='waiting',False
            elif p is None or q is None: stat,winner='bye',p or q
            elif mid in results:
                evidence=results[mid]
                if sorted(x['id'] for x in (p,q))!=sorted(evidence['entrantIds']) or not evidence['nativeKO'] or sum(x<=0 for x in evidence['hp'])!=1:
                    raise ValueError(f'Invalid winner evidence: {mid}')
                expected=evidence['entrantIds'][0 if evidence['hp'][1]<=0 else 1]
                if expected!=evidence['winner']:raise ValueError(f'Invalid winner identity: {mid}')
                stat,winner='verified',next(x for x in (p,q) if x['id']==expected)
            else:stat,winner='ready',False
            rows.append(dict(id=mid,a=p,b=q,status=stat,winner=winner))
            nxt.append(winner)
        cur=nxt
    if {r['id'] for r in rows if r['status']=='verified'}!=set(results):raise ValueError('Invalid bracket receipts')
    return rows

def request(port,path,body):
    raw=json.dumps(body).encode()
    with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=raw,headers={'Content-Type':'application/json'}),timeout=25) as f:
        return json.load(f)
def weights(key,state,menu,profile):
    port,kind=MODELS[key]
    if kind=='systemone':
        result=request(port,'/v1/systemone',dict(state=state,questions={'move':{'type':'choice','criteria':menu,'instructions':'Choose one legal move now. '+profile}}))
        w=result['answers']['move']['probabilities']
    else:
        mapping=dict(zip(LABELS,menu));letters=list(mapping)
        prompt='Game: FightingICE, choose a move now. '+profile+'\n'+state+'\n'+ '\n'.join(f'{i}. {a}: {menu[a]}' for i,a in mapping.items())+'\nAnswer:'
        result=request(port,'/completion',dict(prompt=prompt,n_predict=1,temperature=1,n_probs=len(menu),
            grammar='root ::= ['+''.join(letters)+']',cache_prompt=True,post_sampling_probs=True,
            samplers=['temperature'],seed=SEED))
        win=result['content'].strip()
        if win not in mapping: raise ValueError('Out-of-menu letter')
        w={mapping[row['token']]:float(row['prob']) for row in
            result['completion_probabilities'][0]['top_probs'] if row['token'] in mapping}
    if set(w)!=set(menu) or not any(w.values()) or any(not math.isfinite(p) or p<0 for p in w.values()):
        raise ValueError((key,'invalid choice weights'))
    return w
def pick(w,temp,rng):
    if not temp:return max(w,key=w.get)
    base=max(w.values())
    return rng.choices(list(w),[(p/base)**(1/temp) for p in w.values()])[0]
def write(p,d):
    tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(d,separators=(',',':'),ensure_ascii=True))
    tmp.replace(p)
def simulate(mid, players, n, root, preflight=False):
    if n%2:players=players[::-1]
    rng=[random.Random(f'{SEED}/{mid}/{n}/{p["id"]}') for p in players]
    offset=random.Random(f'{SEED}/{mid}/{n}/menu').randrange(20)
    receipts=[];samples=[];cap=700 if preflight else 0;started=time.monotonic()
    ids=[p['id'] for p in players]
    cp=root/f'{mid}-no-clock-{n}-checkpoint.json'
    prefix=None
    if not preflight:
        for path in (cp,root/f'{mid}-attempt-0.json') if n==0 else (cp,):
            if path.exists():
                prefix=json.loads(path.read_text())
                if prefix['entrantIds']!=ids:raise ValueError('Players changed during restoration')
                break
    with cf.ThreadPoolExecutor(2) as pool,bridge(root/'engine.log') as engine:
        engine.start(cap,400)
        s=engine.step(44,'NEUTRAL','NEUTRAL')
        walk=STARTS[n%len(STARTS)]
        if walk:
            s=engine.step(walk,'FORWARD_WALK','FORWARD_WALK')
            s=engine.step(12,'NEUTRAL','NEUTRAL')
        assert s['p1']['hp']==s['p2']['hp']==400
        initial=sample(s)
        samples.append(initial)
        def advance(moves,end):
            nonlocal s
            while not s['terminated'] and s['frame']<end:
                s=engine.step(min(6,end-s['frame']),*moves)
                samples.append(sample(s))
        def evidence():
            hp=[s['p1']['hp'],s['p2']['hp']]
            ko=s['by']=='ko' and sum(x<=0 for x in hp)==1
            return dict(match=mid,attempt=n,entrantIds=ids,models=[p['model'] for p in players],
                mode='timed-exhibition' if preflight else 'untimed',engineEnd=s['by'],nativeKO=ko,hp=hp,
                initial=initial,wallSeconds=round(time.monotonic()-started,2),
                winner=ids[0 if hp[1]<=0 else 1] if ko else None,receipts=receipts,frames=samples)
        if prefix:
            last=prefix['frames'][-1][0]
            for row in prefix['receipts']:
                if s['frame']!=row[0] or s['terminated']:raise ValueError('Checkpoint frame mismatch')
                for i,p in enumerate(players):
                    if p['temperature']:rng[i].random()
                advance(row[1:3],min(row[0]+PACE,last))
                receipts.append(row)
            if samples!=prefix['frames']:raise ValueError('Checkpoint state replay mismatch; not advancing')
            print('RESUMED',mid,s['frame'],s['p1']['hp'],s['p2']['hp'],flush=True)
        while not s['terminated']:
            texts=[observe(s,i) for i in range(2)]
            actions=allowed_at(texts[0][1]);j=(offset+len(receipts))%len(actions)
            menu={a:OPTIONS[a] for a in actions[j:]+actions[:j]}
            def choose(i):
                t=time.monotonic()
                w=weights(players[i]['model'],texts[i][0],menu,players[i]['profile'])
                return pick(w,players[i]['temperature'],rng[i]),round(1000*(time.monotonic()-t),2)
            futures=[pool.submit(choose,i) for i in range(2)]
            decisions=[f.result() for f in futures]
            moves=[d[0] for d in decisions]
            receipts.append([s['frame'],*moves,*[d[1] for d in decisions],list(menu)])
            advance(moves,s['frame']+PACE)
            if not preflight and len(receipts)%8==0:write(cp,evidence())
        return evidence()

def compare(root):
    d=json.loads(Path(__file__).with_name('scenarios.json').read_text())
    models={}
    for model in MODELS:
        rows=[]
        for key,state,want in d['cases']+d['counterfactuals']:
            for criteria in [d['options'],dict(reversed(list(d['options'].items())))]:
                t=time.monotonic()
                w=weights(model,state,criteria,PROFILES[0])
                rows.append(dict(case=key,expected=want,choice=pick(w,0,None),ms=round((time.monotonic()-t)*1000,2)))
        models[model]=dict(n=len(rows),correct=sum(x['choice']==x['expected'] for x in rows),
            medianMs=statistics.median(x['ms'] for x in rows),rows=rows)
        write(root/'comparison.json',models)
        print('MEASURED',model,models[model]['correct'],len(rows),flush=True)
    return models

def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('out',type=Path);args=p.parse_args()
    root=args.out;root.mkdir(parents=True,exist_ok=True)
    with (root/'run.lock').open('w') as lk:
        fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
        results={r['match']:r for path in root.glob('R*-verified.json') if (r:=json.loads(path.read_text()))}
        players=manifest();write(root/'manifest.json',players)
        probe=root/'comparison.json'
        if not probe.exists() or set(json.loads(probe.read_text()))!=set(MODELS):compare(root)
        for i,key in enumerate(list(MODELS)[1:]):
            f=root/f'preflight-{key}.json'
            if not f.exists():
                v=simulate('PREFLIGHT-'+key,[players[0],next(p for p in players if p['model']==key)],i%3,root,preflight=True)
                write(f,v);print('PREFLIGHT',key,v['engineEnd'],v['hp'],flush=True)
        while True:
            rows=bracket(players,results)
            status=dict(verified=len(results),planned=99,champion=(rows[-1]['winner'] or {}).get('id'),rows=rows)
            write(root/'progress.json',status)
            if status['champion']:
                assert len(results)==99
                break
            match=next((x for x in rows if x['status']=='ready'),None)
            if not match:break
            mid=match['id'];print('START_NO_CLOCK',mid,match['a']['id'],match['b']['id'],flush=True)
            n=0
            while True:
                f=root/f'{mid}-no-clock-{n}-result.json'
                v=json.loads(f.read_text()) if f.exists() else simulate(mid,[match['a'],match['b']],n,root)
                if not f.exists():write(f,v)
                if v['nativeKO']:
                    write(root/f'{mid}-verified.json',v);results[mid]=v
                    print('KO',mid,v['winner'],v['hp'],flush=True);break
                if not (v['engineEnd']=='ko' and all(h<=0 for h in v['hp'])):
                    raise RuntimeError('Untimed match unexpectedly stopped without a KO')
                print('DOUBLE_KO',mid,n,flush=True);n+=1
if __name__=='__main__':main()
