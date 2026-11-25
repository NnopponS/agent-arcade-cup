"""Decision-quality exhibition: same engine frame, move menu and game time for both seats."""
import argparse
import concurrent.futures
import json
import time
from pathlib import Path

from cross_trial import OPTIONS, allowed_at, bridge, decide, observe

FORMAT = 24
SUBSTEP = 6
WARMUP = 44

def pair(pool, chooser, urls, state, tick):
    distance=observe(state,0)[1]
    actions=allowed_at(distance)
    n=tick%len(actions)
    # Rotate option order across ticks; both see the same order on any given tick.
    menu={a:OPTIONS[a] for a in actions[n:]+actions[:n]}
    pending=[pool.submit(chooser,u,observe(state,i)[0],menu.copy()) for i,u in enumerate(urls)]
    replies=[f.result() for f in pending]
    moves=[r[0] for r in replies]
    if not all(m in menu for m in moves):
        raise ValueError('Invalid response; neither input applied')
    return moves, [round(r[1],2) for r in replies], list(menu)

def advance(engine, pool, chooser, urls, state, tick):
    moves, latency, menu=pair(pool,chooser,urls,state,tick)
    record=dict(observedAtFrame=state['frame'],moves=moves,httpMs=latency,menu=menu)
    states=[]
    for _ in range(FORMAT//SUBSTEP):
        nxt=engine.step(SUBSTEP,*moves)
        states.append(nxt)
        if nxt['terminated']:
            break
    return record, states

def sample(s):
    return [s['frame'],s['p1']['hp'],s['p2']['hp'],s['p1']['x'],s['p2']['x'],s['p1']['action'],s['p2']['action']]

def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--ports',nargs=2,type=int,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--frames',type=int,default=2444)
    args=p.parse_args()
    if args.ports[0]==args.ports[1] or not WARMUP<args.frames<=3600:
        p.error('Need two endpoint ports and a valid frame cap')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    urls=[f'http://127.0.0.1:{port}' for port in args.ports]
    start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(2) as pool, bridge(args.out.parent/'lockstep-engine.log') as e:
        e.start(args.frames,400)
        state=e.step(WARMUP,'NEUTRAL','NEUTRAL')
        frames=[sample(state)]
        receipts=[]; queues=[0,0]
        while not state['terminated']:
            record,states=advance(e,pool,decide,urls,state,len(receipts))
            for s in states:
                frames.append(sample(s))
                for i,n in enumerate(s['lastWindow']['nativeQueuesIssued']):
                    queues[i]+=n
            state=states[-1]
            receipts.append(record)
            if len(receipts)%10==0:
                print(args.ports,len(receipts),state['frame'],state['p1']['hp'],state['p2']['hp'],flush=True)
    hp=[state['p1']['hp'],state['p2']['hp']]
    out=dict(schema=1,protocol='lockstep',seats=['Julia-1' if p==18085 else 'Kev 0.8B' for p in args.ports],
        gameFrame=state['frame'],framesCap=args.frames,warmup=WARMUP,decisionEveryFrames=FORMAT,
        hp=hp,nativeQueuesIssued=queues,nativeEndReason=state['by'],nativeKO=state['by']=='ko' and sum(x<=0 for x in hp)==1,
        elapsedWallSeconds=round(time.monotonic()-start,2),receipts=receipts,frames=frames)
    tmp=args.out.with_suffix('.part')
    tmp.write_text(json.dumps(out,separators=(',',':')))
    tmp.replace(args.out)
    print({k:v for k,v in out.items() if k not in ('receipts','frames')},flush=True)
if __name__=='__main__':main()
