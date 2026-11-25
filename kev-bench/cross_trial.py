"""Real-paced FightingICE trial driven only by validated timed SystemOne choices."""
import argparse, collections, concurrent.futures, json, math, sys, time
from pathlib import Path
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fightingice'/'src'))
from bridge import bridge
OPTIONS={
 'FORWARD_WALK':'Walk toward the rival to close distance.',
 'FOR_JUMP':'Jump forwards toward the rival.',
 'DASH':'Close the distance toward the rival. Best when far from all strikes.',
 'THROW_A':'Grab a foe already guarding, only if very close.',
 'STAND_GUARD':'Guard against a close standing strike in progress.',
 'STAND_B':'Strike a nearby, open foe. Your attack hits from up to about 90 px.',
 'STAND_FB':'Use a heavier advancing strike against a nearby open foe.',
 'CROUCH_B':'Strike low against a nearby foe; do not use outside reach.'
}
def observe(s,seat):
    me,op=s[f'p{seat+1}'],s[f'p{2-seat}']
    distance=abs(me['x']-op['x'])
    return (f"Distance {distance} px. HP you {me['hp']}, rival {op['hp']}. "
        f"Energy you {me['energy']}, rival {op['energy']}. "
        f"Rival {op['action'].replace('_',' ').lower()}, {op['remainingActionFrames']} frames left. "
        f"Rival can act {op['canAct']}. You can act {me['canAct']}."), distance

def allowed_at(distance):
    if distance>120: return ('DASH','FORWARD_WALK','FOR_JUMP')
    if distance>55: return ('STAND_GUARD','STAND_B','STAND_FB','CROUCH_B')
    return ('THROW_A','STAND_GUARD','STAND_B','STAND_FB','CROUCH_B')

def decide(url,state,criteria):
    payload=json.dumps({'state':state,'questions':{'move':{'type':'choice',
        'instructions':'Choose a move now. Close large distances. At close range react to the rival attack, guard, or opening.',
        'criteria':criteria}}}).encode()
    t=time.monotonic()
    with urllib.request.urlopen(urllib.request.Request(url+'/v1/systemone',data=payload,headers={'Content-Type':'application/json'}),timeout=5) as r:
        d=json.load(r)['answers']['move']
    if d['choice'] not in criteria:raise ValueError('non-option choice')
    finished=time.monotonic()
    return d['choice'],(finished-t)*1000,finished

def main():
    p=argparse.ArgumentParser();p.add_argument('--ports',type=int,nargs=2,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--affordance',action='store_true')
    p.add_argument('--deadline-ms',type=int,default=300);p.add_argument('--hp',type=int,default=400);p.add_argument('--frames',type=int,default=3600)
    a=p.parse_args()
    if not 50<=a.deadline_ms<=2000:raise ValueError('deadline out of range')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    history=[];frames=[];clock_late=[];native_issues=[0,0];applied=collections.Counter();pending=[None,None];choices=['NEUTRAL','NEUTRAL']
    expires=[0,0];period=6
    with concurrent.futures.ThreadPoolExecutor(2) as pool,bridge(a.out.parent/'live-engine.stderr.log') as e:
        s=e.start(a.frames,a.hp);s=e.step(44,'NEUTRAL','NEUTRAL')
        start=time.monotonic()
        while not s['terminated']:
            f=s['frame']; now=time.monotonic()
            seats=(0,1) if ((f-44)//period)%2==0 else (1,0)
            for seat in seats:
                item=pending[seat]
                if item and item[0].done():
                    future,began,original_frame,initial_distance=item;pending[seat]=None
                    row={'seat':seat,'observedAtFrame':original_frame,'consideredAtFrame':f,'ageMs':round((now-began)*1000,2)}
                    try:
                        move,inference,finished=future.result();_,distance=observe(s,seat)
                        reasons=[]
                        if (now-began)*1000>a.deadline_ms:reasons.append('deadline')
                        if abs(distance-initial_distance)>85:reasons.append('drift')
                        if a.affordance and move not in allowed_at(distance):reasons.append('outside_current_menu')
                        stale=bool(reasons)
                        row.update(move=move,inferenceMs=round(inference,2),completionAgeMs=round((finished-began)*1000,2),observedDistance=initial_distance,currentDistance=distance,applied=not stale,rejectedBecause=reasons)
                        if not stale:choices[seat]=move;expires[seat]=f+12;applied[seat]+=1
                    except Exception as err:row.update(error=type(err).__name__,applied=False)
                    history.append(row)
                if not pending[seat]:
                    state,distance=observe(s,seat)
                    if a.affordance:
                        allowed=allowed_at(distance)
                        candidates=[(k,OPTIONS[k]) for k in allowed]
                    else:
                        candidates=[(k,v) for k,v in OPTIONS.items() if k not in ('FORWARD_WALK','FOR_JUMP')]
                    crit=dict(candidates[seat:]+candidates[:seat])
                    pending[seat]=(pool.submit(decide,f'http://127.0.0.1:{a.ports[seat]}',state,crit),now,f,distance)
                if f>=expires[seat]:choices[seat]='NEUTRAL'
            s=e.step(period,*choices)
            for i,n in enumerate(s['lastWindow']['nativeQueuesIssued']):native_issues[i]+=n
            frames.append([s['frame'],s['p1']['hp'],s['p2']['hp'],s['p1']['x'],s['p2']['x'],s['p1']['action'],s['p2']['action'],*choices])
            delay=start+(s['frame']-44)/60-time.monotonic()
            if delay>0:time.sleep(delay)
            clock_late.append(max(0,1000*(time.monotonic()-start-(s['frame']-44)/60)))
    hp=[s['p1']['hp'],s['p2']['hp']]
    clock_late.sort()
    r={'schema':1,'affordanceFilter':a.affordance,'clockLateP95ms':round(clock_late[math.ceil(.95*len(clock_late))-1],2),'nativeQueuesIssued':native_issues,'hp':hp,'deadlineMs':a.deadline_ms,'gameFrame':s['frame'],'nativeEndReason':s['by'],'sampleEveryFrames':period,'nativeKO':s['by']=='ko' and ((hp[0]<=0)!=(hp[1]<=0)),
       'observations':history,'samples':frames,'appliedBySeat':[applied[i] for i in (0,1)]}
    a.out.write_text(json.dumps(r,separators=(',',':')))
    print(json.dumps({k:v for k,v in r.items() if k not in ('observations','samples')},ensure_ascii=True),flush=True)
if __name__=='__main__': main()
