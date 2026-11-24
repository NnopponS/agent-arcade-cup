'use strict';
const assert=require('node:assert/strict');
function classify(state){
 assert.equal(state.terminated,true,'terminal native state required');
 const A=state.p1?.hp,B=state.p2?.hp;
 assert.ok(Number.isInteger(A)&&Number.isInteger(B),'native integer HP required');
 const rawHp={A,B},nativeWinner=state.winner;
 if(A<=0&&B<=0)return {outcome:'tied',reason:'double-ko',needsSideSwappedSuddenDeath:true,rawHp,nativeWinner};
 if(A===B||nativeWinner==='tie')return {outcome:'tied',reason:'equal-hp',needsSideSwappedSuddenDeath:true,rawHp,nativeWinner};
 const winner=A>B?'A':'B';
 assert.equal(nativeWinner,winner==='A'?'p1':'p2','engine winner disagrees with terminal HP');
 return {outcome:'decisive',winner,reason:A<=0||B<=0?'ko':'time',needsSideSwappedSuddenDeath:false,rawHp,nativeWinner};
}
function normalizedDamage({initial,before,after},seat){
 assert.ok(seat==='A'||seat==='B');
 assert.ok(Number.isInteger(initial.A)&&initial.A>0&&initial.A===initial.B,'symmetric initial integer HP required');
 const guard=x=>{assert.ok(Number.isInteger(x)&&x<=initial.A,'out-of-bounds native HP');return Math.max(0,x);};
 const foe=seat==='A'?'B':'A';
 return ((guard(before[foe])-guard(after[foe]))-(guard(before[seat])-guard(after[seat])))/initial[seat];
}
module.exports={classify,normalizedDamage};
