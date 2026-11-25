"""Fail closed if the public replays cannot support the advertised KO bracket."""
import json, math, re, sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('knockout.json')
d=json.loads(p.read_text())
assert set(d)=={'schema','sampleHz','engineHz','mode','matchFrameMax','probe','winner','matches'}
assert (d['schema'],d['sampleHz'],d['engineHz'],d['matchFrameMax'])==(1,10,60,3600)
assert d['mode']=='local decision-tree models'
R=d['matches']; assert len(R)==7
names=re.compile(r'[A-Z][A-Z_0-9]{1,49}')
expected=[[0,1],[2,3],[4,5],[6,7]]
for i,m in enumerate(R):
    assert m['result']==m['engineReason']=='ko' and m['paced'] is True
    assert m['id']==('R1-'+str(i+1).zfill(2) if i<4 else 'R2-0'+str(i-3) if i<6 else 'R3-01')
    assert m['seats']==(expected+[ [R[0]['winner'],R[1]['winner']], [R[2]['winner'],R[3]['winner']], [R[4]['winner'],R[5]['winner']]])[i]
    a,b=m['hp']
    assert (a>0)!=(b>0)
    assert m['winner']==m['seats'][0 if a>0 else 1]
    assert 44<m['frame']<3600 and abs(m['wallSeconds']-(m['frame']-44)/60)<.5
    assert 0<m['inferenceP95ms']<100 and 0<m['stepP95ms']<100 and m['clockLateP95ms']<100
    assert len(m['samples'])==m['decisionsPerSide']+1 and m['samples'][0][:3]==[44,400,400]
    assert m['samples'][-1][:3]==[m['frame'],a,b]
    assert all(0<z[0]-x[0]<=6 for x,z in zip(m['samples'],m['samples'][1:]))
    for x in m['samples']:
        assert len(x)==11 and all(type(v)==int for v in x[:7]) and all(names.fullmatch(v) for v in x[7:])
    assert all(x[1]>0 and x[2]>0 for x in m['samples'][:-1])
assert d['winner']==R[-1]['winner']
assert len(d['probe'])==8 and sum(x['unguarded']!=x['guarding'] for x in d['probe'])>=6
print(f"Seven paced native knockout replays, {sum(m['decisionsPerSide'] for m in R)*2} live model choices. Champion M{d['winner']+1:02d}.")
