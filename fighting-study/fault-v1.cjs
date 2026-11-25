'use strict';
// One proven invalid response forfeits; no action or reply is invented.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {request}=require('./daemon-client.cjs'),{response,peerLine,audit,chain}=require('./study.cjs'),{tokens}=require('./native.cjs');
function adjudicate(r,rows,phase,held){
 assert.ok((phase===1&&r.status==='phase-one-open')||(phase===2&&r.status==='phase-two-open'),'phase mismatch');
 const expected=phase===1?r.openState:r.phaseOne?.at(-1);
 assert.ok(expected&&typeof expected.nativeFrameSha256==='string');assert.equal(held.frame,expected.frame);assert.equal(held.nativeFrameSha256,expected.nativeFrameSha256);
 const exact={},valid={},invalid={},admissions={};
 for(const seat of ['A','B']){
   function only(event){const es=rows.filter(x=>x.seat===seat&&x.event===event);assert.equal(es.length,1,'authentic observed receipt required');return es[0];}
   const record=only('admitted'),sent=phase===1?record:only('delivered'),final=only('phase'+phase+'-final');
   assert.ok(typeof record.runtime==='string'&&record.runtime===sent.runtime&&Date.parse(sent.timestamp)<=Date.parse(final.timestamp));
   admissions[seat]={runtime:record.runtime,admittedAt:record.timestamp,finalAt:final.timestamp};
   exact[seat]=final.raw;
   assert.ok(typeof final.raw==='string'&&final.raw.length);
   try{valid[seat]=response(JSON.parse(final.raw),tokens,phase,phase===2?peerLine(r.first,seat).messageHash:null);}
   catch{invalid[seat]='invalid-native-agent-response';}
 }
 assert.notEqual(admissions.A.runtime,admissions.B.runtime);
 assert.equal(Object.keys(valid).length,1,'only an observed single fault may use this adjudicator');
 const winnerSeat=Object.keys(valid)[0],loserSeat=Object.keys(invalid)[0];
 const ledger=[...r.ledger,...(phase===1?['A','B'].map(seat=>({type:'admit',match:r.heat.id,seat})):[]),{type:'abort',match:r.heat.id,reason:'invalid'}];
 audit(chain(ledger)); 
 return {...r,admissions:r.admissions??admissions,finishedAt:new Date().toISOString(),status:'forfeit-invalid-response',ledger,
  fault:{schema:'FI-FAULT/v1',phase,winnerSeat,loserSeat,advanced:r.heat.profiles[winnerSeat],forfeited:r.heat.profiles[loserSeat],nativeVictory:false,heldFrame:held.frame,heldFrameSha256:held.nativeFrameSha256,commandsIssued:0,fullNativeFightExecuted:false,digestLinkedPeerReplies:0,valid,invalid,exact,observed:rows}};
}
if(require.main===module){
 const [match,ph]=process.argv.slice(2),phase=Number(ph);
 assert.match(match??'',/^[FK]\d{3}$/);assert.ok(phase===1||phase===2);
 const base=path.join(__dirname,'private-run'),dir=path.join(base,'matches'),p=path.join(dir,'active.json'),out=path.join(dir,match+'.json'),r=JSON.parse(fs.readFileSync(p,'utf8'));
 assert.equal(r.heat.id,match);assert.ok(!fs.existsSync(out));
 const events=fs.readFileSync(path.join(base,match+'-tool-events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
 const held=request(r.daemon,['observe']).states[0];
 const decided=adjudicate(r,events,phase,held);
 fs.writeFileSync(p+'.pending',JSON.stringify(decided,null,2)+'\n',{mode:0o600,flag:'wx'});fs.renameSync(p+'.pending',p);fs.renameSync(p,out);
 console.log(JSON.stringify({match,status:decided.status,advanced:decided.fault.advanced,forfeited:decided.fault.forfeited,nativeVictory:false}));
}
module.exports={adjudicate};
