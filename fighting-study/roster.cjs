'use strict';
const assert=require('node:assert/strict');
const isSeat=s=>s==='A'||s==='B';
const peer=s=>s==='A'?'B':'A';
const id=(h,s)=>h+':'+s;
function auditRoster(schedule,events){
 const known=new Map(),used=new Set(),fixtureSeat=new Set();
 const matches=new Map(schedule.heats.map(x=>[x.id,x]));
 const kos=new Set([...schedule.bracket.playIn,...schedule.bracket.next.flat()].map(x=>x.id));
 let current=1,seenSeats=new Set(),fresh=0,resume=0,rehydrations=0;
 for(const e of events){
   assert.ok(isSeat(e.seat)&&typeof e.runtime==='string'&&e.runtime.length>=8,'native admission requires seat and observed runtime key');
   assert.ok(typeof e.preparedAt==='string'&&e.preparedAt.endsWith('Z')&&!Number.isNaN(Date.parse(e.preparedAt)),'UTC observation time required');
   const matching=id(e.match,e.seat);
   assert.ok(!fixtureSeat.has(matching),'duplicate admission for a match seat');
   fixtureSeat.add(matching);
   if(e.kind==='fresh'){
     const h=matches.get(e.match);
     assert.ok(h?.wave===current&&!seenSeats.has(e.seat)&&h.profiles[e.seat]===e.profile&&!known.has(e.profile),'fresh primary admission outside sequential assigned profile order');
     assert.ok(!used.has(e.runtime),'native runtime reused for fresh profile');
     used.add(e.runtime);seenSeats.add(e.seat);fresh++;
     if(seenSeats.size===2){current++;seenSeats=new Set();}
     known.set(e.profile,{profile:e.profile,firstHeat:e.match,firstSeat:e.seat,incarnations:1,appearances:1,runtime:e.runtime,retainedRounds:0,rehydratedRounds:0});
     continue;
   }
   const x=known.get(e.profile),base=e.match.replace(/-[DR]$/,'');
   if(kos.has(base))assert.ok(fresh===100,'knockout starts before all primary roster admissions');
   else assert.ok(matches.has(base)&&e.match!==base,'continuations allowed only for knockout and declared tiebreak/rematch');
   assert.ok(x,'unknown original entrant');
   if(e.kind==='retained'){
     assert.equal(e.runtime,x.runtime,'retained continuation does not name same observed native runtime');
     x.retainedRounds++;resume++;
   }else if(e.kind==='rehydrated'){
     assert.ok(!used.has(e.runtime),'rehydration must use distinct observed runtime key');
     used.add(e.runtime);x.runtime=e.runtime;x.incarnations++;x.rehydratedRounds++;rehydrations++;
   }else throw Error('unknown entrant kind');
   x.appearances++;
 }
 return {fresh,resume,rehydrations,profiles:[...known.values()]};
}
function publicRoster(audit){
 return audit.profiles.map(({profile,firstHeat,firstSeat,incarnations,appearances,retainedRounds,rehydratedRounds})=>({profile,firstHeat,firstSeat,incarnations,appearances,retainedRounds,rehydratedRounds}));
}
function damage(trace,seat){
 assert.ok(isSeat(seat),'invalid seat');
 const {initial,before,after}=trace;
 assert.ok(Number.isInteger(initial?.A)&&initial.A>0&&initial.A===initial.B,'initial HP must be the exact same positive integer for both seats');
 for(const x of [before,after])for(const s of ['A','B'])assert.ok(Number.isInteger(x?.[s])&&x[s]>=0&&x[s]<=initial[s],'HP outside native bounds');
 const foe=peer(seat);
 return ((before[foe]-after[foe])-(before[seat]-after[seat]))/initial[seat];
}
module.exports={auditRoster,publicRoster,damage};
