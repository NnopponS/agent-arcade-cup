import json,re,sys
from pathlib import Path
p=Path(sys.argv[1]);h=(p/'index.html').read_text()
assert '<html lang="en">' in h and 'Practice results only' in h
assert all((p/ref).is_file() for ref in re.findall(r'href="\./([^"?#]+)',h))
assert not any((p/n).exists() for n in ('data.json','report.md','knockout.json','replays'))
report=json.loads((p/'systemone-results.json').read_text())['models']
assert len(report)==3 and all(m['status']=='measured' and len(m['measurements'])==56 for m in report.values())
trial=json.loads((p/'live-trial.json').read_text())['trials']
assert len(trial)==3
assert any(t['nativeKO'] and (t['hp'][0]<=0)!=(t['hp'][1]<=0) for t in trial.values())
assert sum(t['nativeKO'] for t in trial.values())==1
four=json.loads((p/'kev4-feasibility.json').read_text())
assert len(four['rows'])==8 and four['summary']['under_100_ms']==0
assert 'Qualification' not in h or 'no result entered' in h
print('Decision Lab: 3 full SystemOne runs, independent Kev 4B subset and 3 expressly non-bracket trials verified.')
