"""Replay real accepted contest decisions; compare canonical hashes before rendering."""
import argparse, json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root/'fightingice'/'src'))
from bridge import bridge
p=argparse.ArgumentParser()
p.add_argument('record',type=Path)
p.add_argument('trace',type=Path)
p.add_argument('--private-capture',type=Path)
a=p.parse_args()
x=json.loads(a.record.read_text())
if x.get('status')!='played' or not x.get('second') or set(x['second'])!={'A','B'}:
    raise SystemExit('needs genuine complete decisions and observed engine result')
expected=list({q['frame']:q for q in x['phaseOne']+x['phaseTwo']}.values())
with bridge() as e:
    e.start(420,400,'ZEN','ZEN')
    a.trace.parent.mkdir(parents=True,exist_ok=True)
    e.trace(a.trace)
    if a.private_capture:
        a.private_capture.mkdir(parents=True,exist_ok=True)
        e.capture(a.private_capture,4)
    warm=e.step(44,'FORWARD_WALK','FORWARD_WALK')
    if warm['nativeFrameSha256']!=x['openState']['nativeFrameSha256']:
        raise SystemExit('warmup replay diverged')
    for q in expected:
        w=q['lastWindow']; y=e.step(w['requestedFrames'],*w['tokens'])
        if (y['nativeFrameSha256'],y['frame'])!=(q['nativeFrameSha256'],q['frame']):
            raise SystemExit('engine replay diverged at frame '+str(q['frame']))
tail=expected[-1]
assert tail['terminated']
print(json.dumps({"id":x['heat']['id'],"terminal_frame":tail['frame'],"winner":tail['winner'],"p1":tail['p1']['hp'],"p2":tail['p2']['hp'],"sha256":tail['nativeFrameSha256'],"replayed_control_windows":len(expected)}))
