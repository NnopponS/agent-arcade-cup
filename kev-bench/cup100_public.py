"""Generate a public, data-only tournament snapshot. No player assets or external network."""
import argparse
import base64
import gzip
import html
import json
from pathlib import Path
from cup100_report import action_agreement, summarize, winner_coverage

def read(p):
    return json.loads(p.read_text())

def snapshot(root,out):
    score=read(root/'comparison.json')
    roster=read(root/'manifest.json')
    progress=read(root/'progress.json')
    labels={'julia':'Julia-1 Q8','kev':'Kev 0.8B BF16','laya':'Laya Q8','qwen':'Qwen2.5-0.5B-Instruct Q4','smol':'SmolLM2-135M-Instruct Q4'}
    links={'julia':'https://huggingface.co/ggml-org/Julia-1-GGUF','kev':'https://huggingface.co/jaredpalmer/kev-0.8b',
        'laya':'https://github.com/NandhaKishorM/laya','qwen':'https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF','smol':'https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct'}
    assert set(score)==set(labels)
    results=[]
    for row in progress['rows']:
        if row['status']!='verified':continue
        r=read(root/(row['id']+'-verified.json'))
        assert r['winner']==row['winner']['id'] and r['nativeKO'] and sum(x<=0 for x in r['hp'])==1
        assert r['mode']=='untimed' and r['engineEnd']=='ko' and r['frames'][-1][1:3]==r['hp']
        results.append({k:r[k] for k in ('match','entrantIds','models','hp','winner','initial','frames','wallSeconds','attempt')})
    assert len(results)==progress['verified']
    assert not progress['champion'] or len(results)==99
    report=summarize(progress['rows'],results,labels)
    action_scores=action_agreement(score)
    report['actionAgreement']=action_scores
    report['crossModelWinnerCoverage']=winner_coverage(roster,results)
    assert report['crossModel']+report['sameModel']==len(results)
    out.mkdir(parents=True,exist_ok=True)

    out_replays=out/'cup100-replay'
    out_replays.mkdir(exist_ok=True)
    for result in results:
        f=out_replays/(result['match']+'.json')
        raw=json.dumps(result,separators=(',',':')).encode()
        f.write_text(json.dumps(base64.b64encode(gzip.compress(raw,mtime=0)).decode('ascii')))
    options=''.join(f'<option value="{html.escape(r["match"])}">{html.escape(r["match"]+" · "+" vs ".join(r["entrantIds"]))}</option>' for r in results)
    replay=Path(__file__).with_name('cup100_replay.fragment.html').read_text().replace('__OPTIONS__',options)
    paired={}
    for key,v in score.items():
        cases=list(zip(v['rows'][::2],v['rows'][1::2],strict=True))
        assert all(x['case']==y['case'] for x,y in cases)
        paired[key]=(sum(x['choice']==y['choice'] for x,y in cases),
                     sum(x['choice']==y['choice']==x['expected']==y['expected'] for x,y in cases))
    score_rows=''.join(f'<tr><th scope="row"><a href="{links[k]}">{labels[k]}</a></th><td>{v["correct"]}/{v["n"]}</td><td>{v["medianMs"]:.0f} ms</td><td>{paired[k][0]}/14</td><td>{paired[k][1]}/14</td></tr>' for k,v in score.items())
    action_keys=('DASH','STAND_B','STAND_GUARD','THROW_A')
    def ratio(model,action):
        s=action_scores[model][action]
        return f'{s["correct"]}/{s["trials"]}'
    for k,v in score.items():
        assert sum(r['correct'] for r in action_scores[k].values())==v['correct']
        assert sum(r['trials'] for r in action_scores[k].values())==v['n']
    action_rows=''.join(f'<tr><th scope="row">{labels[k]}</th>'+''.join(f'<td>{ratio(k,a)}</td>' for a in action_keys)+'</tr>' for k in labels)
    valid=lambda e:e.get('id','') if e else ''
    rows=''.join(f'<tr><th scope="row">{html.escape(row["id"])}</th><td>{html.escape(valid(row["a"]))}</td><td>{html.escape(valid(row["b"]))}</td><td>{html.escape(valid(row["winner"]) or row["status"])}</td></tr>' for row in progress['rows'])
    title=f'Champion: {progress["champion"]}' if progress['champion'] else f'{progress["verified"]} / 99 verified'
    stats_rows=''.join(f'<tr><th scope="row">{labels[k]}</th><td>{v["wins"]} / {v["losses"]}</td><td>{v["mirrors"]}</td><td>{v["byes"]}</td></tr>' for k,v in report['models'].items())
    duration=(f' Median recorded duration: {report["medianGameFrameSpan"]:,.0f} game frames.' if results else '')
    final=results[-1] if progress['champion'] else None
    final_line=''
    finding=''
    if final:
        assert final['winner']==progress['champion']
        sides=' and '.join(f'{i}: {max(0,h)} HP' for i,h in zip(final['entrantIds'],final['hp'],strict=True))
        final_line=f'<p><strong>Final:</strong> {html.escape(sides)}. <a href="?match={html.escape(final["match"],quote=True)}#cup-replay">Open the championship replay</a>.</p>'
        laya=report['crossModelWinnerCoverage']['laya']
        laya_wins=report['models']['laya']['wins']
        kev_tally=report['headToHead']['laya']['kev']
        laya_kev_bouts=kev_tally+report['headToHead']['kev']['laya']
        finding=(f'<p><strong>Key takeaway:</strong> Laya’s {laya_wins} cross-model wins came from {laya["entrants"]} distinct entrants, spanning {laya["profiles"]} prompt profiles and {laya["temperatures"]} sampling temperatures. It won {kev_tally} of {laya_kev_bouts} against Kev, even though Kev led the fixed-scenario test. The two tests use different states and menus; neither tells us what caused a specific win.</p>')
    (out/'cup100.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fresh 100-agent Cup</title><style>body{{max-width:960px;margin:auto;padding:18px;font:16px/1.55 system-ui,sans-serif;background:#f5f0e4;color:#24241c}}a{{color:#8c4812}}h1{{font:700 clamp(2.4rem,8vw,5.5rem)/1 Georgia,serif;margin:.5em 0}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:.45em;border-bottom:1px solid #d1c5ad}}.scroll{{overflow:auto}}section{{background:#fffaf0;border:1px solid #d1c5ad;border-radius:12px;padding:14px;margin:14px 0}}</style>
<main><a href="./">← Decision Lab</a><h1>Fresh 100-agent Cup</h1><strong>{html.escape(title)}</strong>{final_line}<p>Five local model checkpoints, each with the same twenty controller configurations. Both fighters choose from the same menu at the same frame; the engine waits for both before advancing. Matches have no round timer or timeout rematches. A player advances by a verified engine knockout, or by a bracket bye; a bye is not a win.</p>
<section><h2>Tournament report</h2><p>{report['crossModel']} cross-model knockouts · {report['sameModel']} same-model knockouts · {report['byeTotal']} byes.{duration}</p>{finding}<div class="scroll"><table><thead><tr><th scope="col">Checkpoint</th><th scope="col">Cross-model wins / losses</th><th scope="col">Same-model bouts</th><th scope="col">Byes</th></tr></thead><tbody>{stats_rows}</tbody></table></div><p><strong>How to read this:</strong> A champion is one controller configuration, not the average of a model family. Opponents and sample sizes differ across models, and winners play more often. Treat these bracket results as descriptive; the tactical benchmark below tests a different question.</p></section>
<section><h2>Model comparison</h2><p>Fourteen scripted scenarios, two menu orders, one prompt. Agreement is with a tactical rubric, not match win rate. Latency is on the test CPU; typed decision heads and one-token constrained generation are different readouts.</p><div class="scroll"><table><thead><tr><th>Model</th><th>Agreement</th><th>Median reply</th><th>Same choice after reversing order</th><th>Correct in both orders</th></tr></thead><tbody>{score_rows}</tbody></table></div></section>
<section><h2>Where the models differed</h2><p>In the fixed scenarios, Kev matched the expected standing punish {ratio('kev','STAND_B')} times and the expected throw {ratio('kev','THROW_A')} times. Laya matched {ratio('laya','STAND_B')} and {ratio('laya','THROW_A')}, respectively; Qwen led on the throw scenarios ({ratio('qwen','THROW_A')}). Each fixed scenario appears in two menu orders. The counts measure agreement with the expected action, not how often a move succeeds in the game.</p><div class="scroll"><table><thead><tr><th scope="col">Checkpoint</th><th scope="col">Approach</th><th scope="col">Standing punish</th><th scope="col">Guard</th><th scope="col">Throw</th></tr></thead><tbody>{action_rows}</tbody></table></div><p>Kev, Julia and Laya use typed-decision heads. Qwen and SmolLM2 are instruct baselines with a constrained option decoder. This comparison does not isolate the effect of the model from its decision decoder.</p></section>
{replay}
<section><h2>Bracket</h2><p>100 entrants · 28 byes · 99 played advances needed</p><div class="scroll"><table><thead><tr><th>Match</th><th>Entrant A</th><th>Entrant B</th><th>Winner / status</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<p><a href="./cup100-data.json" download>Download the roster and match index</a></p></main></html>''')
    (out/'cup100-data.json').write_text(json.dumps(dict(schema=1,comparison=score,roster=roster,report=report,champion=progress['champion'],planned=99,replayEncoding="gzip-base64-json",results=[{k:v for k,v in r.items() if k!="frames"}|{"replay":"cup100-replay/"+r["match"]+".json"} for r in results]),separators=(',',':')))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    snapshot(a.root,a.out)
