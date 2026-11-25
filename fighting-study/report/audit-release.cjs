'use strict';
// Read-only check of the retained native records. Does not spawn an agent or derive a missing response.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {audit,chain,peerLine,commit,response,schedule}=require('../study.cjs');
const {results}=require('../knockout-v1.cjs');
const {auditRoster,publicRoster}=require('../roster.cjs');
const [dir,output]=process.argv.slice(2);
assert.ok(dir&&output,'usage: audit-release.cjs <private run> <output>');
const read=(entry)=>JSON.parse(fs.readFileSync(path.join(dir,entry),'utf8'));
const manifest=read('manifest.json'),plan=read('assignment.json');
const hash=(p)=>crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,p))).digest('hex');
assert.equal(manifest.model,'gpt-6.2-sol');assert.equal(manifest.effort,'low');
assert.equal(manifest.scheduleFileHash,hash('assignment.json'));
const files=fs.readdirSync(path.join(dir,'matches')).filter(x=>/^[FK][0-9]{3}(?:-D)?\.json$/.test(x))
 .sort((a,b)=>a.slice(0,4).localeCompare(b.slice(0,4))||a.length-b.length);
const standings=results(path.join(dir,'matches'));
const entrantProfiles=new Set(),entrantRuntimes=new Set(),bracket=new Map(), rows=[], rosterEvents=[];
const report={engine:manifest.engine,engineCommit:manifest.upstreamCommit,model:manifest.model,effort:manifest.effort,
 continuity:{retained:0,rehydrated:0},auditedNativeAdditionalRounds:0,engineRecoveredRecords:0,fullNativeKnockouts:0,knockoutForfeits:0};
let authentic=0, opening=0;
for(const f of files){
 const x=read('matches/'+f),id=x.heat.id;
 if(x.status==='forfeit-invalid-response'){
   assert.equal(id,f.slice(0,-5));assert.match(id,/^K\d{3}$/);
   const q=x.fault, validation=audit(chain(x.ledger));
   assert.equal(validation.closed,0);assert.deepEqual(validation.aborted,[id]);
   assert.equal(q.fullNativeFightExecuted,false);assert.equal(q.nativeVictory,false);
   assert.equal(q.heldFrameSha256,(q.phase===1?x.openState:x.phaseOne.at(-1)).nativeFrameSha256);
   report.knockoutForfeits++;
   for(const s of ['A','B']){
      const a=x.admissions[s],kind=x.continuity[s].kind;
      assert.ok(Object.hasOwn(report.continuity,kind));
      report.continuity[kind]++;
      rosterEvents.push({profile:x.heat.profiles[s],match:id,seat:s,kind,runtime:a.runtime,preparedAt:a.admittedAt});
      if(s===q.winnerSeat)assert.deepEqual(response(JSON.parse(q.exact[s]),manifest.legal,q.phase,q.phase===2?peerLine(x.first,s).messageHash:null),q.valid[s]);
      else assert.throws(()=>response(JSON.parse(q.exact[s]),manifest.legal,q.phase,q.phase===2?peerLine(x.first,s).messageHash:null));
   }
   rows.push({id,A:x.heat.profiles.A,B:x.heat.profiles.B,reason:'invalid-submission-forfeit',
                          frameAtAbort:q.heldFrame,engineSHA256AtAbort:q.heldFrameSha256,forfeited:q.forfeited});
   continue;
 }
 assert.equal(id,f.slice(0,-5)); assert.equal(audit(chain(x.ledger)).closed,1,'Invalid ledger '+id);
 if(f.includes('-D'))report.auditedNativeAdditionalRounds++;
 if(x.engineRecovery)report.engineRecoveredRecords++;
 const tr=x.phaseTwo.at(-1);
 assert.ok(tr.terminated&&/^[a-f0-9]{64}$/.test(tr.nativeFrameSha256),'Missing terminal proof '+id);
 assert.ok(x.admissions.A.runtime!==x.admissions.B.runtime,'One runtime used for both seats');
 for(const s of ['A','B']){
   assert.equal(x.admissions[s].runtime,x.phaseTwoObservations[s].runtime,'Runtime substituted within match');
   const digest=peerLine(x.first,s).messageHash;
   assert.equal(x.second[s].reply.to,digest,'Reply digest mismatch');
   assert.deepEqual(response(JSON.parse(x.rawFirst[s]),manifest.legal,1,null),x.first[s]);
   assert.deepEqual(response(JSON.parse(x.rawSecond[s]),manifest.legal,2,digest),x.second[s]);
   if(/^F\d{3}$/.test(id)){
     assert.ok(!entrantProfiles.has(x.heat.profiles[s])&&!entrantRuntimes.has(x.admissions[s].runtime),'Duplicate primary seat');
     entrantProfiles.add(x.heat.profiles[s]);entrantRuntimes.add(x.admissions[s].runtime);
   }
   if(/^K\d{3}$/.test(id)){
     assert.ok(Object.hasOwn(report.continuity,x.continuity[s].kind),'Unknown continuity '+id);
     report.continuity[x.continuity[s].kind]++;
   }
   assert.equal(commit(x.first[s]),x.ledger.find(e=>e.type==='commit'&&e.seat===s&&e.phase===1)?.hash);
   assert.equal(commit(x.second[s]),x.ledger.find(e=>e.type==='commit'&&e.seat===s&&e.phase===2)?.hash);
   const kind=/^F\d{3}$/.test(id)?'fresh':x.continuity[s]?.kind||x.continuity.kind;
   rosterEvents.push({profile:x.heat.profiles[s],match:id,seat:s,kind,
                      runtime:x.admissions[s].runtime,preparedAt:x.admissions[s].admittedAt});
 }
 if(/^F\d{3}$/.test(id)){opening++;authentic+=2;}
 if(/^K\d{3}$/.test(id))report.fullNativeKnockouts++;
 rows.push({id,A:x.heat.profiles.A,B:x.heat.profiles.B,A_HP:tr.p1.hp,B_HP:tr.p2.hp,frame:tr.frame,reason:tr.by,engineSHA256:tr.nativeFrameSha256});
}
for(const h of plan.heats){
 const r=standings[h.id];
 if(!r)continue;
 assert.ok(Object.values(h.profiles).includes(r.winner),'Invalid primary advancement');
 bracket.set(h.id,r.winner);
}
let knockout=0;
for(const fixture of [...plan.bracket.playIn,...plan.bracket.next.flat()]){
 const r=standings[fixture.id];
 if(!r)continue;
 const f=read(`matches/${fixture.id}.json`);
 assert.deepEqual(fixture.source.map(x=>bracket.get(x)),[f.heat.profiles.A,f.heat.profiles.B],'Broken bracket dependency '+fixture.id);
 assert.ok(Object.values(f.heat.profiles).includes(r.winner),'Wrong knockout winner');
 bracket.set(fixture.id,r.winner);knockout++;
}
report.evidence={verified_admissions:entrantProfiles.size,qualifying_two_speaker:opening,knockouts_verified:knockout,
                  champion:bracket.get('K049')??null};
report.authenticatedPrimaryReplies=authentic;
report.profiles=publicRoster(auditRoster(plan,rosterEvents));
const bySource=Object.fromEntries(Object.values(standings).map(x=>[x.source,x]));
report.results=rows.map(x=>bySource[x.id]?{...x,advanced:bySource[x.id].winner,decision:bySource[x.id].method||'engine'}:x);
if(bracket.has('K049')){
 assert.equal(opening,50);assert.equal(entrantProfiles.size,100);assert.equal(knockout,49);
 const last=standings.K049;
 report.final={id:last.source,A:last.record.heat.profiles.A,B:last.record.heat.profiles.B,
               winner:last.winner,decision:last.method||'engine'};
 const reveal=fs.readFileSync(path.join(dir,'nonce.hex'),'utf8').trim();
 assert.match(reveal,/^[a-f0-9]{64}$/);
 assert.deepEqual(schedule(Buffer.from(reveal,'hex')),plan);
 report.schedule={nonceHex:reveal,commitment:plan.seedCommitment,assignment:plan};
}
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({evidence:report.evidence,authentic,continuity:report.continuity,rematches:report.auditedNativeAdditionalRounds}));
