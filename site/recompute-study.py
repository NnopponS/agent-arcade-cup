"""Reproduce the exploratory summary from the anonymized, downloadable CSV."""
import csv,random,statistics,sys
from pathlib import Path
source=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('study-inputs.csv')
rows=list(csv.DictReader(source.open(encoding='utf-8',newline='')))
cells=[('method','pivot'),('method','stay'),('neutral','pivot'),('neutral','stay')]
values=[]
for note,instr in cells:
    grp=[r for r in rows if (r['assigned_note'],r['opponent_instruction'])==(note,instr)]
    v=[int(r['net_hp_change_after_break'])/400 for r in grp]
    values.append(v)
    print(f'{note:>7} / {instr:5} : n={len(v):2}  mean={400*statistics.mean(v):+.4f} HP; unavailable={sum(r["assigned_note_delivered"]=="0" for r in grp)}')
def delta(v): return sum(s*statistics.mean(k) for s,k in zip((1,-1,-1,1),v))
r=random.Random(0x41524341)
scores=sorted(delta([r.choices(g,k=len(g)) for g in values]) for _ in range(4000))
print(f'Note × pivot estimate: {400*delta(values):+.4f} HP. Exploratory 95% interval: [{400*scores[99]:+.4f}, {400*scores[3899]:+.4f}].')
