"""Produce a readable, dependency-free SVG for the observed primary HP contrast."""
import argparse,json,html,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('summary',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();d=json.loads(a.summary.read_text());r=d['hp_difference_in_differences']
v=float(r['in_HP']);lo,hi=map(float,r['bootstrap_percentile_95_hp'])
assert math.isfinite(v+lo+hi) and lo<=v<=hi
extent=max(5,math.ceil(max(abs(lo),abs(hi),abs(v))/5)*5)
x=lambda t:400+290*t/extent
e='Includes zero; this pilot does not establish a benefit.' if lo<=0<=hi else 'Exploratory interval; limited to one game and one model setting.'
label=f'{v:+.2f} HP; interval {lo:+.2f} to {hi:+.2f} HP. {e}'
lines=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 254" role="img" aria-labelledby="title desc">',
'<title id="title">Estimated effect of the strategy note during a pivot</title>',f'<desc id="desc">{html.escape(label)}</desc>',
'<rect x="0" y="0" width="800" height="254" rx="14" fill="#f8fafc"/>',
'<g font-family="system-ui, sans-serif" fill="#142b48">',
'<text x="30" y="40" font-size="21" font-weight="750">Did the strategy note help against a pivot?</text>',
f'<text x="30" y="65" font-size="14">50 primary heats · {sum(z["n"] for z in d["bins"])} scored · phase-two net health contrast</text>',
'<path d="M110 151H690" stroke="#738597" stroke-width="1"/>',
f'<path d="M400 93V151" stroke="#738597" stroke-dasharray="4 4"/>',
f'<path d="M{x(lo):.1f} 119H{x(hi):.1f} M{x(lo):.1f} 109v20 M{x(hi):.1f} 109v20" stroke="#286e9d" stroke-width="3" stroke-linecap="round"/>',
f'<circle cx="{x(v):.1f}" cy="119" r="6" fill="#164a70"/>',
f'<text x="{x(v):.1f}" y="103" text-anchor="middle" font-size="16" font-weight="750">{v:+.1f}</text>']
for t in sorted(set((-extent,-extent/2,0,extent/2,extent))):
 lines.append(f'<path d="M{x(t):.1f} 151v5" stroke="#738597"/><text x="{x(t):.1f}" y="174" text-anchor="middle" font-size="12">{t:g}</text>')
lines+=['<text x="400" y="196" text-anchor="middle" font-size="13">Change in health-point advantage (HP)</text>',
f'<text x="30" y="228" font-size="14">{html.escape(e)}</text>',
'</g></svg>']
a.output.write_text('\n'.join(lines)+'\n',encoding='utf-8')
