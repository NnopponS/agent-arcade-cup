'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const s=require('./study.cjs');
const seal=(event)=>s.commit(event);
test('preregistered schedule 50 pairs, 100 profiles, four independent cells and both sides',()=>{
 const data=s.schedule(Buffer.alloc(32,44));
 assert.equal(data.heats.length,50);
 assert.equal(new Set(data.heats.flatMap(h=>Object.values(h.profiles))).size,100);
 assert.deepEqual(Object.values(data.heats.reduce((r,x)=>(r[x.pivot+':'+x.focalCard]=(r[x.pivot+':'+x.focalCard]??0)+1,r),{})).sort((a,b)=>a-b),[12,12,13,13]);
 assert.equal(data.heats.filter(x=>x.focalSeat==='A').length,25);
 assert.equal(data.heats.filter(x=>x.openRegime==='pressure').length,25);
 assert.equal(data.heats.filter(x=>x.deliveryFirst==='A').length,25);
 assert.equal(data.bracket.playIn.length+data.bracket.next.reduce((n,r)=>n+r.length,0),49);
 assert.deepEqual(data,s.schedule(Buffer.alloc(32,44)));
});
test('checked literal actions never generate unstated tactics and commands cannot tie to unknown tokens',()=>{
 const legal=['GUARD','DASH','CHECK'];
 assert.deepEqual(s.response({commands:['DASH','CHECK','GUARD','GUARD'],said:'I expect to hold range.'},legal,1),{commands:['DASH','CHECK','GUARD','GUARD'],said:'I expect to hold range.'});
 assert.throws(()=>s.response({commands:['DASH','','GUARD','GUARD'],said:'hello'},legal,1),/unknown/i);
 assert.throws(()=>s.response({commands:['DASH','GUARD','GUARD','GUARD'],said:'hello'},legal,2),/reply/i);
});
test('turn-two opponent dialogue carries a hash of actual prior message, never the hidden rival plan',()=>{
 const messages={A:{said:'I prefer distance.',commands:['GUARD']},B:{said:'Come closer, then.',commands:['DASH']}};
 const result=s.peerLine(messages,'A');
 assert.equal(result.body,'Come closer, then.');
 assert.equal(result.messageHash,seal({seat:'B',body:'Come closer, then.'}));
 assert.equal(Object.hasOwn(result,'commands'),false);
});
test('reject corrupted, overlapping, phantom and unauthorized protocol events',()=>{
 const e=(type,d)=>({type,match:'F001',...d});
 const game=[e('open',{}),e('admit',{seat:'A'}),e('admit',{seat:'B'}),e('commit',{seat:'A',phase:1,hash:seal('ax'),said:'A opens.'}),e('commit',{seat:'B',phase:1,hash:seal('bx'),said:'B opens.'}),e('advance',{phase:1,engineTrace:seal('p1')}),e('deliver',{seat:'A',peer:'B',hash:seal({seat:'B',body:'B opens.'})}),e('deliver',{seat:'B',peer:'A',hash:seal({seat:'A',body:'A opens.'})}),e('commit',{seat:'A',phase:2,hash:seal('a2'),replyTo:seal({seat:'B',body:'B opens.'})}),e('commit',{seat:'B',phase:2,hash:seal('b2'),replyTo:seal({seat:'A',body:'A opens.'})}),e('advance',{phase:2,engineTrace:seal('p2')}),e('close',{})];
 const log=s.chain(game);
 assert.deepEqual(s.audit(log),{events:12,closed:1,maxLogicalActiveSeats:2,open:null});
 assert.throws(()=>s.audit(s.chain([...game.slice(0,2),{type:'open',match:'F002'}])),/overlap/i);
 const wrong=structuredClone(game); wrong[6].hash=seal('forgery');assert.throws(()=>s.audit(s.chain(wrong)),/peer/i);
 const g=structuredClone(game);g[9].replyTo=seal('wrong quote');assert.throws(()=>s.audit(s.chain(g)),/reply/i);
 const changed=structuredClone(log);changed[5].engineTrace=seal('bad');assert.throws(()=>s.audit(changed),/chain/i);
 const duplicated=structuredClone(game);duplicated[2].seat='A';assert.throws(()=>s.audit(s.chain(duplicated)),/admission/i);
 const missing=structuredClone(game);missing.splice(9,1);assert.throws(()=>s.audit(s.chain(missing)),/both/i);
});
