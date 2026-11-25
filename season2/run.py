"""FightingICE performance pilot: six-frame model updates and KO-only adjudication."""
import argparse,collections,json,math,random,statistics,sys,time
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fightingice'/'src'))
from bridge import bridge
HZ=60
WINDOW=6
LIMIT=3600

def features(own,other):
    dx=other['x']-own['x']
    d=abs(dx)
    orient=1 if dx>0 else -1
    a=other['action']
    return [d, own['y']-other['y'], other['vx']*orient,own['hp']-other['hp'],own['energy'],
        other['remainingActionFrames'], int(other['canAct']), int('GUARD' in a),int('JUMP' in a),
        int(a not in ['STAND','NEUTRAL','FORWARD_WALK','DASH','BACK_STEP','CROUCH'] and 'GUARD' not in a and 'JUMP' not in a and 'RECOV' not in a and 'DOWN' not in a),
        min(own['x'],960-own['x'])]

def coach(v,style,r):
    d,y,vr,hp,en,locked,ready,guard,jump,attack,edge=v
    ranges=[78,105,65,118,85,98,110,76]
    near=ranges[style]
    if d>175:
        return 'FOR_JUMP' if style in (3,5) and d>265 and r.random()<.41 else 'DASH'
    if d>near+30:
        return 'FORWARD_WALK' if style in (1,2) else 'DASH'
    if y>40 or jump:
        return 'STAND_B' if style in (0,3,6) else 'STAND_FA'
    if guard and d<83:
        return 'THROW_A' if r.random()<.85 else 'CROUCH_B'
    if attack and d<105 and locked>6 and r.random()<[.25,.40,.12,.21,.52,.31,.26,.08][style]:
        return 'CROUCH_GUARD' if style in (1,4,5) else 'STAND_GUARD'
    if en>=30 and r.random()<[.20,.14,.32,.25,.09,.26,.38,.12][style]:
        return 'STAND_D_DF_FA'
    if d>72:
        return ['STAND_FB','STAND_FA','CROUCH_B','STAND_FB','STAND_B','STAND_FA','STAND_FB','STAND_FA'][style]
    return [
        ('CROUCH_B','STAND_FB','STAND_A'),('STAND_B','STAND_FA','CROUCH_A'),
        ('CROUCH_A','CROUCH_B','STAND_B'),('STAND_FB','STAND_B','CROUCH_A'),
        ('STAND_A','CROUCH_B','STAND_B'),('CROUCH_B','STAND_FA','STAND_A'),
        ('STAND_FB','CROUCH_B','STAND_B'),('CROUCH_B','STAND_A','STAND_B')
    ][style][0 if r.random()<.65 else 1 if r.random()<.63 else 2]

def make_model(style):
    r=random.Random(8931+style); X=[]; y=[]
    for i in range(7000):
        v=[r.randrange(20,390), r.randrange(-10,95) if i%5==0 else 0,r.randrange(-14,15),r.randrange(-399,400),
           r.randrange(0,100),r.randrange(1,50),r.randrange(2),int(i%5==0),int(i%7==0),int(i%3==0),r.randrange(0,481)]
        X.append(v); y.append(coach(v,style,r))
    model=DecisionTreeClassifier(max_depth=11,min_samples_leaf=12,random_state=style).fit(X,y)
    return model.tree_, model.classes_.tolist()

def infer(model,x):
    t,labels=model
    i=0
    while t.feature[i]>=0:
        i=t.children_left[i] if x[t.feature[i]]<=t.threshold[i] else t.children_right[i]
    return labels[max(range(len(labels)),key=lambda n:t.value[i,0,n])]

def pct(x,q):
    a=sorted(x);return round(a[min(len(a)-1,max(0,math.ceil(len(a)*q)-1))],4) if a else 0

def fight(engine,models,a,b,mid,real=False):
    s=engine.start(LIMIT,400)
    s=engine.step(44,'NEUTRAL','NEUTRAL')
    started=time.monotonic()
    timing=[]; rounds=[]; pace=[]; counters=[collections.Counter(),collections.Counter()]
    samples=[[44,s['p1']['hp'],s['p2']['hp'],s['p1']['x'],s['p2']['x'],s['p1']['y'],s['p2']['y'],s['p1']['action'],s['p2']['action'],'NEUTRAL','NEUTRAL']]
    while not s['terminated']:
        frame=s['frame']
        before=time.perf_counter_ns()
        x=[features(s['p1'],s['p2']),features(s['p2'],s['p1'])]
        chosen=[infer(models[a],x[0]),infer(models[b],x[1])]
        inference=(time.perf_counter_ns()-before)/1e6
        timing.append(inference)
        for m,other,chosen_action,c in zip([models[a],models[b]],[s['p2'],s['p1']],chosen,counters):
            c[chosen_action]+=1
        s=engine.step(WINDOW,*chosen)
        step_ms=(time.perf_counter_ns()-before)/1e6
        rounds.append(step_ms)
        samples.append([s['frame'],s['p1']['hp'],s['p2']['hp'],s['p1']['x'],s['p2']['x'],s['p1']['y'],s['p2']['y'],s['p1']['action'],s['p2']['action'],*chosen])
        if real:
            ideal=started+(s['frame']-44)/HZ
            delay=ideal-time.monotonic()
            if delay>0:time.sleep(delay)
            pace.append(max(0,(time.monotonic()-ideal)*1000))
    wall=time.monotonic()-started
    hp=[s['p1']['hp'],s['p2']['hp']]
    winner=([a,b][0 if hp[0]>hp[1] else 1] if s['by']=='ko' and ((hp[0]<=0) != (hp[1]<=0)) else None)
    return {'id':mid,'seats':[a,b],'result':'ko' if winner is not None else 'unfinished','winner':winner,
      'hp':hp,'frame':s['frame'],'engineReason':s['by'],'decisionsPerSide':len(timing),
      'inferenceP95ms':pct(timing,.95),'stepP95ms':pct(rounds,.95),
      'clockLateP95ms':pct(pace,.95) if real else None,'paced':real,'wallSeconds':round(wall,3),
      'moves':[dict(c) for c in counters],'samples':samples}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--paced',action='store_true')
    p.add_argument('--pilot',action='store_true')
    a=p.parse_args();models=[make_model(i) for i in range(8)]
    baseline=[70,0,0,0,50,24,0,0,0,0,220]
    probes=[]
    for i,m in enumerate(models):
        g=baseline.copy();g[7]=1
        probes.append({'entrant':i,'unguarded':infer(m,baseline),'guarding':infer(m,g)})
    records=[]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with bridge(a.out.parent/'engine.stderr.log') as e:
        def run(j,k,code):
            r=fight(e,models,j,k,code,a.paced)
            records.append(r)
            print(json.dumps({x:y for x,y in r.items() if x not in ('samples','moves')}),flush=True)
            return r['winner']
        if a.pilot: winner=run(0,4,'P01')
        else:
            entrants=list(range(8));rnd=0
            while len(entrants)>1:
                rnd+=1
                results=[run(j,k,f'R{rnd}-{i+1:02d}') for i,(j,k) in enumerate(zip(entrants[::2],entrants[1::2]))]
                if any(j is None for j in results):break
                entrants=results
            winner=entrants[0] if len(entrants)==1 else None
    a.out.write_text(json.dumps({'schema':1,'sampleHz':10,'engineHz':HZ,'mode':'local decision-tree models','matchFrameMax':LIMIT,'probe':probes,'winner':winner,'matches':records},separators=(',',':')))
if __name__=='__main__':main()
