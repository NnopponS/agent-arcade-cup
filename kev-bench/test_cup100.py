from collections import Counter
from cup100 import manifest, slots, bracket, pick
from random import Random
m=manifest()
assert len({e['id'] for e in m})==100
assert set(Counter(e['model'] for e in m).values())=={20}
assert sum(x is None for x in slots(m))==28
assert len(bracket(m, {}))==127
assert sum(r['status']=='ready' and r['id'].startswith('R1-') for r in bracket(m,{}))==36
assert pick({'A':0.8,'B':0.2},0,Random(0))=='A'
assert pick({'A':0.8,'B':0.2},0.6,Random(0))==pick({'A':0.8,'B':0.2},0.6,Random(0))
