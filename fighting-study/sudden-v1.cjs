'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const {request}=require('./daemon-client.cjs'),{makeInvite}=require('./live.cjs'),{classify}=require('./adjudication-v1.cjs');
const other=s=>s==='A'?'B':'A';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function swapped(run){
 const h=run.heat;
 return {...h,id:h.id+'-D',profiles:{A:h.profiles.B,B:h.profiles.A},focalSeat:other(h.focalSeat),methodSeat:other(h.methodSeat),deliveryFirst:other(h.deliveryFirst)};
}
function lot(original){
 const h=original.heat;
 assert.match(h.engineSeed,/^[0-9a-f]{16}$/);
 const seed=createHash('sha256').update(h.engineSeed+'\0'+h.id+'\0administrative-double-tie').digest();
 return h.profiles[seed[0]&1?'B':'A'];
}
function launch(d,id){
 assert.match(id,/^[FK]\d{3}$/);
 const f=path.join(d,id+'.json'),target=path.join(d,id+'-D.json'),p=path.join(d,'active.json');
 assert.ok(!fs.existsSync(p)&&!fs.existsSync(target),'already active/used tiebreak attempt');
 const original=read(f);
 assert.ok(classify(original.phaseTwo.at(-1)).needsSideSwappedSuddenDeath,'not a tied native finish');
 const heat=swapped(original), cards={A:original.cards.B,B:original.cards.A};
 const [initial,opened,observe]=request(original.daemon,['new 420 400 ZEN ZEN','step 44 FORWARD_WALK FORWARD_WALK','observe']).states;
 assert.equal(initial.frame,0);assert.equal(opened.frame,44);assert.equal(opened.nativeFrameSha256,observe.nativeFrameSha256);
 const continuity=Object.fromEntries(['A','B'].map(s=>[s,{kind:'retained',expectedRuntime:original.admissions[other(s)].runtime,previousRuntime:original.admissions[other(s)].runtime,source:id}]));
 const run={heat,daemon:original.daemon,openState:opened,cards,status:'phase-one-open',openAt:new Date().toISOString(),ledger:[{type:'open',match:heat.id}],tieOrigin:id,continuity,...(original.promptVersion?{promptVersion:original.promptVersion}:{})};
 run.invites1=Object.fromEntries(['A','B'].map(seat=>{
   const x=id.startsWith('K')?require('./knockout-v1.cjs').exactInvite(run,1,seat):makeInvite(run,1,seat);
   x.message='Side-swapped sudden death after a native equal-HP finish. You are the same entrant, in the opposite seat, with reset HP and a new native match.\n'+x.message;
   return [seat,x];
 }));
 const temp=p+'.pending';fs.writeFileSync(temp,JSON.stringify(run,null,2)+'\n',{mode:0o600,flag:'wx'});fs.renameSync(temp,p);
 return [heat.deliveryFirst,other(heat.deliveryFirst)].map(s=>run.invites1[s]);
}
function verdict(d,id){
 const orig=read(path.join(d,id+'.json')),dmatch=read(path.join(d,id+'-D.json'));
 assert.equal(dmatch.tieOrigin,id);
 const pos=classify(dmatch.phaseTwo.at(-1));
 return pos.outcome==='decisive'?{advanced:dmatch.heat.profiles[pos.winner],nativeVictory:true,source:dmatch.heat.id,position:pos}:{advanced:lot(orig),nativeVictory:false,source:dmatch.heat.id,position:pos,reason:'administrative-seeded-tiebreak-after-second-tie'};
}
if(require.main===module){
 const [op,id,dir='private-run/matches']=process.argv.slice(2);
 console.log(JSON.stringify(op==='open'?launch(dir,id):op==='verdict'?verdict(dir,id):null,null,2));
}
module.exports={swapped,lot,launch,verdict};
