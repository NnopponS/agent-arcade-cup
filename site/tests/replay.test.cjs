'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const core=require('../replay.js');
test('advancing a 60 Hz replay at 0.25× and 4× keeps the exact underlying clock',()=>{
  assert.equal(core.clockAdvance(0,1000,.25,60,420),15);
  assert.equal(core.clockAdvance(0,1000,4,60,420),240);
  assert.equal(core.clockAdvance(80,2000,4,60,420),420);
});
test('command presented for a recorded step describes the input responsible for the current frame',()=>{
  const windows=[[0,1,2],[44,3,4],[91,5,6]];
  assert.equal(core.windowAt(windows,44),0);
  assert.equal(core.windowAt(windows,45),1);
  assert.equal(core.windowAt(windows,91),1);
  assert.equal(core.windowAt(windows,92),2);
});
test('actual key masks do not turn an idle frame into an attack',()=>{
  assert.equal(core.keyLabel(0),'–');
  assert.equal(core.keyLabel(1|4|16|32),'→ ↓ A C');
});
test('on a champion terminal frame HP displays the native result, not the order of winner names',()=>{
  const f=[367,44,300,537,3,0,1,372,120,900,537,2,0,0,0,0,[]];
  assert.deepEqual(core.fighterAt(f,1),{hp:372,energy:120,x:900,y:537,action:2,state:0,front:false,keys:0});
});
