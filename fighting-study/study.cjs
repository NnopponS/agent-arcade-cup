'use strict';
const crypto=require('node:crypto');
const assert=require('node:assert/strict');
const seats=['A','B'];
const other=x=>x==='A'?'B':'A';
function repr(x){
 if(x===null||typeof x==='string'||typeof x==='boolean')return JSON.stringify(x);
 if(typeof x==='number'&&Number.isFinite(x))return JSON.stringify(x);
 if(Array.isArray(x))return '['+x.map(repr).join(',')+']';
 if(x&&Object.getPrototypeOf(x)===Object.prototype)return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+repr(x[k])).join(',')+'}';
 throw Error('Not a plain finite JSON value');
}
const commit=x=>crypto.createHash('sha256').update(repr(x)).digest('hex');
const validHash=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const pad=n=>String(n).padStart(3,'0');
function schedule(nonce){
 assert.ok(Buffer.isBuffer(nonce)&&nonce.length===32,'32-byte schedule nonce required');
 const rank=(name,x)=>crypto.createHmac('sha256',nonce).update(name+'\0'+String(x)).digest('hex');
 const numbers=Array.from({length:50},(_,i)=>i+1);
 const perm=(label,ns=numbers)=>ns.slice().sort((a,b)=>rank(label,a).localeCompare(rank(label,b)));
 const cells=Array.from({length:50},(_,i)=>i<13?['pivot','method']:i<25?['pivot','neutral']:i<37?['stay','method']:['stay','neutral']);
 const assignments=new Map(perm('cell').map((n,i)=>[n,cells[i]]));
 const balanced=(id)=>new Set(perm(id).slice(0,25));
 const left=balanced('focal-side'),pressure=balanced('opening-regime'),delivery=balanced('delivery-first');
 const heats=numbers.map(i=>{
   const [pivot,focalCard]=assignments.get(i);
   const focalSeat=left.has(i)?'A':'B';
   const openRegime=pressure.has(i)?'pressure':'counter';
   return {id:'F'+pad(i),wave:i,profiles:{A:'FI-'+pad(i*2-1),B:'FI-'+pad(i*2)},focalSeat,pivot,focalCard,openRegime,
    nextRegime:pivot==='stay'?openRegime:openRegime==='pressure'?'counter':'pressure',deliveryFirst:delivery.has(i)?'A':'B',methodSeat:focalCard==='method'?focalSeat:other(focalSeat),engineSeed:rank('engine',i).slice(0,16)};
 });
 const seed=perm('bracket');
 const playIn=Array.from({length:18},(_,i)=>({id:'K'+pad(i+1),source:['F'+pad(seed[i*2]),'F'+pad(seed[i*2+1])]}));
 let frontier=playIn.map(x=>x.id).concat(seed.slice(36).map(x=>'F'+pad(x))).sort((a,b)=>rank('bracket-slots',a).localeCompare(rank('bracket-slots',b)));
 const next=[];let id=19;
 while(frontier.length>1){
   const wave=Array.from({length:frontier.length/2},(_,i)=>({id:'K'+pad(id++),source:[frontier[2*i],frontier[2*i+1]]}));
   next.push(wave);frontier=wave.map(x=>x.id);
 }
 return {status:'PLAN_ONLY',design:'FIGHT-ICE/2P/v1',seedCommitment:crypto.createHash('sha256').update(nonce).digest('hex'),heats,bracket:{playIn,next}};
}
function line(x,label,min=1,max=180){
 assert.ok(typeof x==='string'&&x.length>=min&&x.length<=max&&!/[\p{Cc}\p{Cf}]/u.test(x)&&x.trim()===x,label+' must be bounded plain text');
 return x;
}
function response(x,legal,phase,expectedReplyHash=null){
 assert.ok(x&&Object.getPrototypeOf(x)===Object.prototype,'JSON object required');
 assert.ok(phase===1||phase===2,'Invalid phase');
 assert.ok(Array.isArray(x.commands)&&x.commands.length===4,'four command tokens required');
 const allowed=new Set(legal);
 for(const c of x.commands)assert.ok(typeof c==='string'&&allowed.has(c),'unknown or unauthorized command token');
 const out={commands:x.commands.slice(),said:line(x.said,'said')};
 if(phase===2){
   assert.ok(x.reply&&Object.getPrototypeOf(x.reply)===Object.prototype&&validHash(x.reply.to),'reply must reference a peer message hash');
   if(expectedReplyHash!==null)assert.equal(x.reply.to,expectedReplyHash,'reply references wrong peer line');
   out.reply={to:x.reply.to,text:line(x.reply.text,'reply text')};
   if(x.adjustment!==undefined)out.adjustment=line(x.adjustment,'adjustment');
 }
 if(x.note!==undefined)out.note=line(x.note,'strategic note',15,220);
 return out;
}
function peerLine(responses,seat){
 assert.ok(seats.includes(seat));
 const s=other(seat),body=line(responses[s]?.said,'peer line');
 return {seat:s,body,messageHash:commit({seat:s,body})};
}
const GENESIS=commit('Fighting Study ledger v1');
function chain(events){
 let prev=GENESIS;
 return events.map((event,i)=>{
   const row={...event,seq:i+1,prev};
   const rowHash=commit(row);prev=rowHash;return {...row,rowHash};
 });
}
function audit(events){
 let prev=GENESIS,state=null,closed=0,peak=0;
 const seenIds=new Set(),expired=new Set();
 for(const [i,row] of events.entries()){
   const {rowHash,...e}=row;
   assert.ok(e.seq===i+1&&e.prev===prev&&rowHash===commit(e),'event hash chain invalid');
   prev=rowHash;
   if(e.type==='open'){
     assert.ok(!state,'match overlap');
     assert.ok(typeof e.match==='string'&&/^[FK]\d{3}(?:-[DR])?$/.test(e.match)&&!seenIds.has(e.match),'match ID reused or bad');
     state={match:e.match,admissions:new Set(),phase:1,commits:{},lines:{},delivered:new Set()};
     seenIds.add(e.match);continue;
   }
   assert.ok(state&&e.match===state.match,'event lacks active matching engine session');
   if(e.type==='admit'){
     assert.ok(seats.includes(e.seat)&&!state.admissions.has(e.seat)&&state.phase===1&&!Object.keys(state.commits).length,'wrong or repeated admission');
     state.admissions.add(e.seat);peak=Math.max(peak,state.admissions.size);continue;
   }
   if(e.type==='commit'){
     assert.ok(state.admissions.size===2&&state.admissions.has(e.seat)&&e.phase===state.phase&&!state.commits[e.seat]&&validHash(e.hash),'unexpected commitment');
     if(e.phase===1)state.lines[e.seat]={said:line(e.said,'opening dialogue')};
     else {
       assert.ok(e.phase===2&&state.delivered.has(e.seat),'missing genuine peer delivery before phase two');
       assert.equal(e.replyTo,peerLine(state.lines,e.seat).messageHash,'phase-two reply does not bind to delivered peer line');
     }
     state.commits[e.seat]=e.hash;
     continue;
   }
   if(e.type==='deliver'){
     assert.ok(state.phase===2&&seats.includes(e.seat)&&!state.delivered.has(e.seat),'invalid peer delivery');
     const peer=peerLine(state.lines,e.seat);
     assert.ok(e.peer===peer.seat&&e.hash===peer.messageHash,'peer delivery did not match actual opening message');
     state.delivered.add(e.seat);continue;
   }
   if(e.type==='advance'){
     assert.ok(e.phase===state.phase&&Object.keys(state.commits).length===2&&validHash(e.engineTrace),'engine may only advance after both sealed submissions and a trace');
     state.commits={};state.phase++;continue;
   }
   if(e.type==='abort'){
     assert.ok(['timeout','invalid','engine-error','runtime-lost','double-forfeit'].includes(e.reason),'abort needs explicit reason');
     expired.add(e.match);state=null;continue;
   }
   if(e.type==='close'){
     assert.ok(state.phase===3,'both phases required before a played result can close');
     closed++;state=null;continue;
   }
   throw Error('unknown event type');
 }
 return {events:events.length,closed,maxLogicalActiveSeats:peak,open:state?.match??null,...(expired.size?{aborted:[...expired]}:{})};
}
module.exports={schedule,commit,chain,peerLine,response,audit};
