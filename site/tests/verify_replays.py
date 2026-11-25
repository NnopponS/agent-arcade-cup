"""Fail closed unless every browser replay matches the archive's public evidence."""
import base64, gzip, json, re
from pathlib import Path
import sys

site=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
list_rows=json.loads((site/'data.json').read_text())['matches']
game=set()
root=site/'replays'
found={}
catalog=json.loads((root/'index.json').read_text())
assert set(catalog)=={'schema','meta','files'} and catalog['schema']==1
meta=catalog['meta']
assert set(meta)=={'engine','fixed_hz','frames','barrier_hashes','pilot'}
assert meta['engine']=='FightingICE 7.0' and meta['fixed_hz']==60 and meta['barrier_hashes']==1034
MATCH=r'(?:[FK]\d{3}(?:-D)?|B\d{3})'
FORBIDDEN=re.compile(r'(/workspace/|/home/agent|nonceHex|rawFirst|rawSecond|runtimeId|thread_id|conversationId|api[_-]key\s*[:=]|ghp_\w+|fleetCommit|nativeFrameSha256|sha256)',re.I)
for f in root.glob('pack-*.json'):
    packed=json.loads(f.read_text()); assert isinstance(packed,dict)
    assert f.stat().st_size<=45000, f
    assert set(packed)=={k for k,v in catalog['files'].items() if v==f.name}
    for key, blob in packed.items():
        assert re.fullmatch(MATCH,key) and key not in found
        text=gzip.decompress(base64.b64decode(blob,validate=True)).decode()
        assert not FORBIDDEN.search(text),key
        found[key]=json.loads(text)
assert set(found)==set(catalog['files'])
assert all(re.fullmatch(r'pack-\d{2}\.json',v) for v in catalog['files'].values())
fighters=puzzles=frames=0
for row in list_rows:
    k=row['id']; obj=found.pop(k,None)
    if row['result']=='forfeit': assert obj is None;continue
    assert obj is not None,k
    if row['series']=='fighting':
        assert set(obj)=={'e','m','z','f','c'} and obj['e']==60
        actions,states,records=obj['m'],obj['z'],obj['f']
        assert len(actions)==len(set(actions)) and all(re.fullmatch(r'[A-Z][A-Z_0-9]{1,50}',x) for x in actions)
        assert len(states)==len(set(states)) and all(re.fullmatch(r'[A-Z_]{2,15}',x) for x in states)
        assert len(records)==row['frame']+1 and row['frame']==420
        assert 0<len(obj['c'])<=9 and all(len(v)==3 and all(type(w)==int for w in v) and 0<=v[0]<len(records) and max(v[1:])<len(actions) for v in obj['c'])
        for r in records:
            assert len(r)==17 and all(type(v)==int for v in r[:16]) and all(0<=v<=127 for v in r[14:16]) and all(len(q)==5 and all(type(w)==int for w in q) and q[0] in (0,1) for q in r[-1]),k
            for i in (0,7):
                assert 0<=r[i]<=400 and 0<=r[i+4]<len(actions) and 0<=r[i+5]<len(states) and r[i+6] in (0,1),k
        for c in row['checkpoints']:
            assert (records[c['frame']][0],records[c['frame']][7])==(c['a'],c['b']), (k,c)
        assert [records[-1][0],records[-1][7]]==row['score'],k
        fighters+=1;frames+=len(records)
    elif row['series']=='pilot':
        assert set(obj)=={'g','a','b'}
        assert obj['g'] in ('2048','sliding','lights','battleship')
        game.add(obj['g'])
        for j,name in enumerate('ab'):
            s=obj[name]
            assert set(s)=={'s','i'} and len(s['s'])==row['moves'][j]+1 and len(s['i'])==row['moves'][j]
            assert all(isinstance(v,list) and len(v)==3 and type(v[0])==int and v[0]>0 and len(v[2])==v[0]**2 for v in s['s'])
            assert all(type(v)==int or v in ('up','down','left','right') for v in s['i'])
            if obj['g']=='2048':
                assert s['s'][-1][1]==row['score'][j]
        puzzles+=1
assert not found and fighters==94 and puzzles==meta['pilot']==100 and frames==meta['frames']==39574
assert game=={'2048','sliding','lights','battleship'}
print(f'Public replay verified: {fighters} native rematches, {frames} exact sampled frames, {puzzles} pilot pairs, no forfeit replays.')
