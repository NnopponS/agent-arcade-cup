'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {classify}=require('./adjudication-v1.cjs');
const {makeInvite}=require('./live.cjs'),{request}=require('./daemon-client.cjs'),{commit}=require('./study.cjs');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const idOk=/^K(?:00[1-9]|0[1-4]\d)$/;
const promptVersion=id=>Number(id.slice(1,4))>=7?'FI-KNOCKOUT-PROMPT/v2':'FI-KNOCKOUT-PROMPT/v1';
const oldOpener='Play the actual FightingICE v7.0 ZEN mirror in the two-player fresh-agent study.';
const newOpener='Play the actual FightingICE v7.0 ZEN mirror in the knockout continuation of the Agent Arcade Cup.';
const currentTask=' Your current task is only to play this match and emit the exact requested JSON.';

const cleanNote=x=>typeof x==='string'&&x.length>=20&&x.length<=200&&!/[\p{Cc}\p{Cf}\d<>{}\[\]]/u.test(x)&&!/(?:https?|token|password|api key|ignore|system prompt|filesystem|tool use)/i.test(x);
function slots(p,outcomes,id){
 assert.ok(idOk.test(id),'knockout ID invalid');
 assert.ok(p.heats.length===50&&p.heats.every(h=>Object.values(h.profiles).includes(outcomes[h.id]?.winner)),'all original heats must have authentic resolved winner before knockout');
 const fixtures=[...p.bracket.playIn,...p.bracket.next.flat()];
 const ix=fixtures.findIndex(x=>x.id===id);
 assert.ok(ix>=0&&fixtures.slice(0,ix).every(x=>outcomes[x.id]?.winner),'knockout admission outside sequential committed order');
 const rows=fixtures[ix].source.map(x=>outcomes[x]);
 assert.ok(rows.every(x=>/^FI-\d{3}$/.test(x?.winner))&&rows[0].winner!==rows[1].winner,'missing or conflicting dependency winners');return rows;
}
function resolveWinner(x){
 if(!x.phaseTwo?.at(-1)?.terminated)return null;
 const r=classify(x.phaseTwo.at(-1));
 return r.outcome==='decisive'?x.heat.profiles[r.winner]:null;
}
function results(d){
 let out={};
 for(const f of fs.readdirSync(d).filter(f=>/^[FK]\d{3}\.json$/.test(f)).sort()){
   const r=read(path.join(d,f)),k=f.slice(0,-5);
   if(r.status==='forfeit-invalid-response'){
     const q=r.fault,s=q?.winnerSeat;
     assert.ok(q?.schema==='FI-FAULT/v1'&&q.nativeVictory===false&&q.commandsIssued===0&&['A','B'].includes(s)&&q.advanced===r.heat.profiles[s]&&q.valid[s]&&r.ledger.at(-1)?.type==='abort','malformed administrative forfeit');
     out[k]={winner:q.advanced,source:k,record:r,method:'administrative-forfeit'};
     continue;
   }
   const w=resolveWinner(r);
   if(w){out[k]={winner:w,source:k,record:r};continue;}
   const dt=path.join(d,k+'-D.json');
   if(fs.existsSync(dt)){
     const r2=read(dt),v=require('./sudden-v1.cjs').verdict(d,k);
     out[k]={winner:v.advanced,source:k+'-D',record:r2,method:v.nativeVictory?'engine':'administrative-tie'};
   }
 }return out;
}
function exactInvite(run,phase,seat){
 const x=makeInvite(run,phase,seat);
 const kind=run.continuity[seat].kind;
 const noteLine=run.cards[seat].source
  ?'Your short prior strategic note (explicit memory packet): '+run.cards[seat].text
  :'No eligible prior strategic note was available.';
 x.message=('You are '+x.profile+' in the FightingICE single-elimination rounds. Runtime continuity: '+kind+'. Now independently play to win; prior research instructions do not apply here.\n'+x.message)
  .split('\n').map(l=>l.startsWith('Private tactical brief: ')?'Tournament objective: win this native round using your own legal choices.':l.startsWith('Information card: ')?noteLine:l).join('\n');
 if(promptVersion(run.heat.id)==='FI-KNOCKOUT-PROMPT/v2'){
   x.message=x.message.replace(oldOpener,newOpener).replace('Tournament objective: win this native round using your own legal choices.','Tournament objective: win this native round using your own legal choices.'+currentTask);
 }
 return x;
}
function open(d,daemon,plan,id,availability){
 const f=path.join(d,'active.json');
 assert.ok(!fs.existsSync(f)&&!fs.existsSync(path.join(d,id+'.json')),'prior session active or match ID already used');
 const rows=slots(plan,results(d),id);
 const profiles={A:rows[0].winner,B:rows[1].winner};
 const continuity={},cards={};
 for(const [idx,s] of ['A','B'].entries()){
   const x=rows[idx],old=x.record,id=profiles[s];
   const prior=Object.keys(old.heat.profiles).find(k=>old.heat.profiles[k]===id);
   const observed=availability?.[id];
   assert.ok(observed&&['retained','rehydrated'].includes(observed.kind),'observed runtime availability needed before preparing each profile');
   if(observed.kind==='retained')assert.ok(observed.runtime===old.admissions[prior].runtime,'retained runtime identity mismatch');
   continuity[s]={kind:observed.kind,previousRuntime:old.admissions[prior].runtime,expectedRuntime:observed.kind==='retained'?observed.runtime:null,source:x.source};
   const note=old.second?.[prior]?.note;
   cards[s]={kind:cleanNote(note)?'prior-own-method':'prior-method-missing',text:cleanNote(note)?note:'No eligible strategic note.',source:cleanNote(note)?id:null};
 }
 const [init,snap,confirm]=request(daemon,['new 420 400 ZEN ZEN','step 44 FORWARD_WALK FORWARD_WALK','observe']).states;
 assert.ok(init.frame===0&&snap.frame===44&&snap.nativeFrameSha256===confirm.nativeFrameSha256);
 const k=Number(id.slice(1)),heat={id,profiles,focalSeat:'A',methodSeat:'A',deliveryFirst:k%2?'A':'B',openRegime:'pressure',nextRegime:'pressure',engineSeed:commit({seed:plan.seedCommitment,id}).slice(0,16)};
 const run={heat,continuity,daemon,promptVersion:promptVersion(id),openState:snap,cards,status:'phase-one-open',openAt:new Date().toISOString(),ledger:[{type:'open',match:id}]};
 run.invites1=Object.fromEntries(['A','B'].map(s=>[s,exactInvite(run,1,s)]));write(f,run);
 return ordered(run,1);
}
function ordered(r,p){return [r.heat.deliveryFirst,r.heat.deliveryFirst==='A'?'B':'A'].map(s=>r['invites'+p][s]);}
function write(p,x){
 const t=p+'.pending';fs.writeFileSync(t,JSON.stringify(x,null,2)+'\n',{mode:0o600,flag:'wx'});fs.renameSync(t,p);
}
function prepareSecond(d){
 const f=path.join(d,'active.json'),r=read(f);
 assert.ok(r.status==='phase-two-open'&&/^K\d{3}(?:-D)?$/.test(r.heat.id));
 for(const s of ['A','B']){
  const c=r.continuity[s],actual=r.admissions[s].runtime;
  assert.ok(c.kind==='retained'?c.expectedRuntime===actual:c.previousRuntime!==actual,'actual continuation does not match its verified runtime status');
 }
 r.invites2=Object.fromEntries(['A','B'].map(s=>[s,exactInvite(r,2,s)]));write(f,r);return ordered(r,2);
}
if(require.main===module){
 const [op,d,...args]=process.argv.slice(2);
 if(op==='open'){const [daemon,plan,id,availability]=args;console.log(JSON.stringify(open(d,daemon,read(plan),id,read(availability)),null,2));}
 else if(op==='second')console.log(JSON.stringify(prepareSecond(d),null,2));
 else if(op==='standings') console.log(JSON.stringify(Object.fromEntries(Object.entries(results(d)).map(([k,v])=>[k,{winner:v.winner,source:v.source}]))));
 else throw Error('unknown operation');
}
module.exports={slots,resolveWinner,results,exactInvite,promptVersion};
