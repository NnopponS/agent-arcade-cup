'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {schedule}=require('./study.cjs');
const {auditRoster,publicRoster,damage}=require('./roster.cjs');
const plan=schedule(Buffer.alloc(32,5));
const seat=(n,s,k='fresh',runtime='proof_'+n+'_'+s)=>({match:'F'+String(n).padStart(3,'0'),seat:s,kind:k,profile:plan.heats[n-1].profiles[s],runtime,preparedAt:'2026-11-24T22:00:00.000Z'});
test('roster starts at first prespecified heat and eventually keeps labels but not false native identity',()=>{
 const rows=[seat(1,'A'),seat(1,'B'),seat(2,'A')];
 const k={...rows[0],match:'K001',kind:'rehydrated',runtime:'next_native_proof'};
 const full=plan.heats.flatMap(h=>['A','B'].map(x=>seat(h.wave,x)));
 const out=auditRoster(plan,[...full,k]);assert.equal(out.fresh,100);assert.equal(out.resume,0);assert.equal(out.rehydrations,1);
 assert.throws(()=>auditRoster(plan,[...rows,k]),/primary roster/i);
 assert.throws(()=>auditRoster(plan,[...full,{...k,kind:'retained'}]),/retained/i);
 assert.throws(()=>auditRoster(plan,[...rows,{...rows[1],match:'F002',seat:'B',profile:plan.heats[1].profiles.B}]),/native runtime/i);
 assert.throws(()=>auditRoster(plan,[seat(2,'A')]),/sequential/i);
 const visible=publicRoster(out);
 assert.equal(visible.find(x=>x.profile===k.profile).incarnations,2);
 assert.equal(JSON.stringify(visible).includes('proof_'),false);
});
test('damage uses authentic pre/post HP and the symmetric initial scale',()=>{
 const x={initial:{A:400,B:400},before:{A:380,B:365},after:{A:350,B:300}};
 assert.equal(damage(x,'A'),(65-30)/400);
 assert.equal(damage(x,'B'),(30-65)/400);
 assert.throws(()=>damage({...x,initial:{A:200,B:400}},'A'),/exact same/i);
 assert.throws(()=>damage({...x,after:{A:420,B:300}},'B'),/bounds/i);
});
