"""Independently recompute published estimates using only the sanitized study rows."""
import argparse,collections,json,random,statistics
from pathlib import Path
P=argparse.ArgumentParser(description=__doc__);P.add_argument('observed',type=Path);P.add_argument('summary',type=Path,nargs='?');A=P.parse_args()
cells=collections.defaultdict(list); delivered=collections.defaultdict(list); seen=set()
for row in A.observed.read_text().splitlines():
    x=json.loads(row)
    assert x['heat'] not in seen;seen.add(x['heat'])
    if x['status']!='played' or x['unusedFinalActions'] or x['phaseFrames'][-1]<=x['phaseFrames'][-2]:continue
    idx='AB'.index(x['focalSeat'])
    def net(pair):
        return (min(400,max(0,pair[idx]))-min(400,max(0,pair[1-idx])))/400
    g=x['assignedFocalCard'],x['assignedStimulus']; value=net(x['rawHP'][-1])-net(x['rawHP'][-2])
    cells[g].append(value)
    if x['receivedCard'][x['focalSeat']]==g[0]:delivered[g].append(value)
out={'scored_cells':[{ 'card':k[0],'instruction':k[1],'n':len(v),'average_HP':400*statistics.mean(v),'unavailable':len(v)-len(delivered[k])} for k,v in sorted(cells.items())]}
order=[('method','pivot'),('method','stay'),('neutral','pivot'),('neutral','stay')]; signs=[1,-1,-1,1]
delta=lambda vv:sum(s*statistics.mean(b) for s,b in zip(signs,vv))
values=[cells[k] for k in order]
if all(len(b)>=2 for b in values):
    r=random.Random(0x41524341)
    results=sorted(delta([r.choices(b,k=len(b)) for b in values]) for _ in range(4000))
    out['effect_HP']=400*delta(values);out['interval_HP']=[400*results[99],400*results[3899]]
if A.summary:
    q=json.loads(A.summary.read_text())
    for a,b in zip(out['scored_cells'],q['bins'],strict=True):
        assert (a['card'],a['instruction'],a['n'],a['unavailable'])==(b['assigned_card'],b['assigned_stimulus'],b['n'],b['method_card_unavailable_or_not_delivered'])
        assert abs(a['average_HP']-400*b['mean_focal_net_phase2_hp_per400'])<1e-9
    if 'hp_difference_in_differences' in q:
        expected=q['hp_difference_in_differences']
        assert abs(out['effect_HP']-expected['in_HP'])<1e-9
        assert all(abs(a-b)<1e-9 for a,b in zip(out['interval_HP'],expected['bootstrap_percentile_95_hp'],strict=True))
print(json.dumps(out,indent=2))
