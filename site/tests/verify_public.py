"""Run on every deploy. Validate structure and no raw evidence exposed."""
from collections import Counter
from pathlib import Path
import csv,json,re
p=Path(__file__).resolve().parents[1]
x=json.loads((p/'data.json').read_text()); assert set(x)=={'schema','summary','matches'}
rows=x['matches']; assert len(rows)==len({m['id'] for m in rows})==x['summary']['rows']==204
assert Counter((m['series'],m['result']) for m in rows)=={('fighting','engine'):89,('fighting','tie'):5,('fighting','forfeit'):10,('pilot','pilot'):100}
for m in rows:
 assert set(m)==set('id series stage game result a b winner score scoreUnit reason rematchOf frame checkpoints moves'.split())
 assert re.fullmatch(r'[FK]\d{3}(?:-D)?|B\d{3}',m['id'])
 assert all(re.fullmatch(r'FI-\d{3}|[AB]',m[k]) for k in ('a','b'))
 assert m['winner'] in (None,m['a'],m['b'])
 assert m['reason'] in (None,'time','invalid-submission-forfeit')
 assert m['game'] in ('FightingICE','2048','Lights Out','Sliding Puzzle','Battleship')
 assert m['stage'] in ('qualifier','knockout','pilot')
 assert m['rematchOf'] is None or re.fullmatch(r'[FK]\d{3}',m['rematchOf'])
 for c in m['checkpoints']: assert set(c)=={'frame','a','b'} and all(type(v)==int for v in c.values())
 if m['result']=='forfeit': assert m['score'] is None and not m['checkpoints']
f=next(m for m in rows if m['id']=='K049'); assert f['score']==[367,372] and f['winner']=='FI-005'
assert sum(len(m['checkpoints']) for m in rows)==846
with (p/'match-index.csv').open() as fh: assert [r['match_id'] for r in csv.DictReader(fh)]==[m['id'] for m in rows]
with (p/'study-inputs.csv').open() as fh:
 rows=list(csv.DictReader(fh)); assert len(rows)==50 and all(re.fullmatch(r'F\d{3}',r['heat_id']) for r in rows)
with (p/'retired-puzzle-archive.csv').open() as fh: assert Counter(r['paired_grade'] for r in csv.DictReader(fh))=={'bothCorrect':19,'incomplete':1}
for f in ('data.json','report.json','report.md','match-index.csv','study-inputs.csv','retired-puzzle-archive.csv'):
 b=(p/f).read_text()
 assert not re.search(r'(/workspace/|/home/agent|nonceHex|rawFirst|rawSecond|runtimeId|thread_id|conversationId|api[_-]key\s*[:=]|ghp_\w+)',b,re.I),f
print('Published projection verified: 204 rows, 846 HP checkpoints, 50 study inputs.')
