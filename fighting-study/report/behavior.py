"""Exploratory, literal command diagnostics. Neither prompts nor raw strategy notes are exported."""
from collections import Counter, defaultdict
from pathlib import Path
import argparse,json,re,statistics

def turnover(a,b):
    """Share of four requested tokens replaced, accounting for repeated moves."""
    if len(a)!=4 or len(b)!=4:
        raise ValueError("Expected four tokens per decision")
    return 1-sum((Counter(a)&Counter(b)).values())/4

# Coarse, retrospective proxy for the counterpart's observable assigned style.
# Not the protocol's not-yet-frozen response-family mapping.
TOWARD={'FORWARD_WALK','DASH','FOR_JUMP'}
AWAY_OR_GUARD={'BACK_STEP','STAND_GUARD','CROUCH_GUARD'}

def spacing(tokens):
    return (sum(x in TOWARD for x in tokens)-sum(x in AWAY_OR_GUARD for x in tokens))/4

def mean(xs):
    return statistics.mean(xs) if xs else None

def report(source):
    diag=[]; changes=defaultdict(list); assigned=defaultdict(Counter); seen=set()
    for p in sorted(source.iterdir()):
        if not re.fullmatch(r'[FK](?:00[1-9]|0[1-4][0-9]|050)\.json',p.name): continue
        r=json.loads(p.read_text()); h=r['heat']
        if h['id'] in seen: raise ValueError('Duplicate match')
        seen.add(h['id'])
        if r['status']!='played' or r['phaseTwoUnused']:continue
        if h['id'][0]=='K':
            for seat in ('A','B'):
                a=r['first'][seat]['commands']; b=r['second'][seat]['commands']
                changes[r['continuity'][seat]['kind']].append(turnover(a,b))
            continue
        g=h['focalSeat']; o='A' if g=='B' else 'B'
        g1,g2=(r[phase][g]['commands'] for phase in ('first','second'))
        o1,o2=(r[phase][o]['commands'] for phase in ('first','second'))
        pivot=h['pivot']; delta=spacing(o2)-spacing(o1)
        target=1 if h['nextRegime']=='pressure' else -1
        assigned[pivot]['scored']+=1
        assigned[pivot]['observed_spacing_index_changed']+=int(delta!=0)
        if pivot=='pivot':
            assigned[pivot]['observed_shift_toward_assigned_direction']+=int(target*delta>0)
        diag.append({'id':h['id'],'noteAssigned':h['focalCard'],'noteDelivered':r['cards'][g]['kind'],
                     'opponentInstruction':pivot,'focalSeat':g,'focalTokenTurnover':turnover(g1,g2),'counterpartSpacingDelta':delta})
    primary={}
    for card in ('method','neutral'):
        for pivot in ('pivot','stay'):
            values=[x['focalTokenTurnover'] for x in diag if x['noteAssigned']==card and x['opponentInstruction']==pivot]
            primary[f'{card}/{pivot}']={'n_heats':len(values),'mean_focal_token_turnover':mean(values)}
    return {'status':'exploratory, not a frozen response-family measure',
       'definition':'Token turnover = one minus fraction of tokens shared between unordered per-phase multisets; a permutation alone is not scored as a change.',
       'counterpart_spacing_proxy':'(forward walk + dash + forward jump − backstep − guards) / four; neutral, attacks and projectiles contribute zero. Counts requested tokens, not physical receipts.',
       'assignment_is_not_compliance':dict(assigned),
       'primary_cells':primary,
       'knockout_continuity':{k:{'scored_seats':len(v),'mean_token_turnover':mean(v)} for k,v in sorted(changes.items())},
       'continuity_limit':'Knockout continuity depends on runtime availability and progression, is not randomized, and repeated profile appearances are not independent; no causal or memory-recovery claim.',
       'rows':diag}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('matches',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();a.output.write_text(json.dumps(report(a.matches),indent=2)+'\n')
