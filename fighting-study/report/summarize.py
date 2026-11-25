"""Export minimum privacy-scoped data from real current FightingICE cutoff. No artificial fills."""
import argparse,csv,json,re,statistics,random
from pathlib import Path
def build(src:Path,dst:Path):
    totals={};public=[];profiles=set();observed=[]
    for p in sorted(src.iterdir()):
        if not re.fullmatch(r'F(00[1-9]|0[1-4]\d|050)\.json',p.name):continue
        x=json.loads(p.read_text()); h=x['heat']; obs={'heat':h['id'],'status':x['status'],'A':h['profiles']['A'],'B':h['profiles']['B']}
        if x['status']!='played':
            observed.append(obs);continue
        a,b=set(x['first']),set(x['second'])
        if a!={'A','B'} or b!={'A','B'}:raise ValueError('incomplete played record')
        if not all(len(x[q][s]['commands'])==4 for q in ['first','second'] for s in ['A','B']):raise ValueError('action count')
        if any(h['profiles'][k] in profiles for k in ('A','B')):raise ValueError('duplicate fresh entrant identifier')
        profiles.update(h['profiles'].values())
        phase=[x['openState'],x['phaseOne'][-1],x['phaseTwo'][-1]]
        hp=[[q['p1']['hp'],q['p2']['hp']]for q in phase]
        obs.update({'phaseFrames':[q['frame']for q in phase],'rawHP':hp,'terminal':phase[-1]['terminated'],'nativeWinner':phase[-1]['winner'],'nativeReason':phase[-1]['by'],'engineHash':phase[-1]['nativeFrameSha256'],
        'opening':{k:{'line':x['first'][k]['said'],'actions':x['first'][k]['commands']} for k in ['A','B']},
        'reply':{k:{'peerLineSHA256':x['second'][k]['reply']['to'],'text':x['second'][k]['reply']['text'],'actions':x['second'][k]['commands']} for k in ['A','B']},
        'receivedCard':{s:x['cards'][s]['kind']for s in ['A','B']},'assignedStimulus':h['pivot'],
        'assignedFocalCard':h['focalCard'],'focalSeat':h['focalSeat'],'unusedFinalActions':x['phaseTwoUnused']})
        public.append(obs); observed.append(obs)
        q=h['focalSeat']; i=['A','B'].index(q)
        if x['phaseTwoUnused'] or phase[-1]['frame']<=phase[1]['frame']:continue
        try:
            c=x['cards'][q]['kind']
        except KeyError:continue
        ck=h['focalCard']; pivot=h['pivot']; clamp=lambda k:min(400,max(0,k))
        start=hp[1]; finish=hp[-1]; delta=((clamp(finish[i])-clamp(finish[1-i]))-(clamp(start[i])-clamp(start[1-i])))/400
        cell=totals.setdefault((ck,pivot),{'values':[],'delivered_values':[],'unavailable':0});cell['values'].append(delta)
        if c!=ck:cell['unavailable']+=1
        else:cell['delivered_values'].append(delta)
    dst.mkdir(parents=True,exist_ok=True)
    (dst/'observed-heats.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in observed),encoding='utf-8')
    s={'source':'current FightingICE primary rounds only','completed_primary_heats':len(public),'recorded_fresh_played_profiles':len(profiles),'recorded_nonplayed':len(observed)-len(public),'bins':[]}
    for (card,pivot),v in sorted(totals.items()):
        mean=statistics.mean(v['values'])
        s['bins'].append({'assigned_card':card,'assigned_stimulus':pivot,'n':len(v['values']),'method_card_unavailable_or_not_delivered':v['unavailable'],'mean_focal_net_phase2_hp_per400':mean})
    order=[('method','pivot'),('method','stay'),('neutral','pivot'),('neutral','stay')]
    sign=(1,-1,-1,1)
    if all(k in totals and len(totals[k]['values'])>=2 for k in order):
        cells=[totals[k]['values'] for k in order]
        effect=lambda cell:sum(t*statistics.mean(v) for t,v in zip(sign,cell))
        rng=random.Random(0x41524341)
        draws=sorted(effect([rng.choices(v,k=len(v)) for v in cells]) for _ in range(4000))
        sens=[totals[k]['delivered_values'] for k in order]
        s['hp_difference_in_differences']={'fraction_of_initial_HP':effect(cells),
          'in_HP':400*effect(cells),'bootstrap_percentile_95_hp':[draws[99]*400,draws[3899]*400],
          'delivered_card_sensitivity_HP':400*effect(sens) if all(sens) else None,
          'method':'Exploratory stratum bootstrap over primary heats; ignores note lineage dependence. No confirmatory p-value.'}
    s['limits']='Card assignment not receipt; treatment is tactic instruction, not perfectly controlled opponent behavior. No overarching causal claim. Behavioral family mapping is exploratory; no measurement from responses that never reached game.'
    (dst/'summary.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
    return s
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('matches',type=Path);p.add_argument('out',type=Path);a=p.parse_args();print(json.dumps(build(a.matches,a.out)))
