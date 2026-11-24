'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'),{commit,response,peerLine}=require('./study.cjs');
const BRIDGE=path.resolve(__dirname,'../fightingice/run-bridge.sh');
const tokens=['NEUTRAL','FORWARD_WALK','DASH','BACK_STEP','STAND_GUARD','CROUCH_GUARD','FOR_JUMP','STAND_A','STAND_B','CROUCH_A','CROUCH_B','STAND_FA','STAND_FB','THROW_A','STAND_D_DF_FA','STAND_F_D_DFB'];
const frames=Object.freeze({opening:44,perCommit:4,window:47,cap:420,hp:400});
const start=['new 420 400 ZEN ZEN','step 44 FORWARD_WALK FORWARD_WALK','observe'];
function run(commands,bridge=BRIDGE){
 const proc=spawnSync(bridge,[],{input:commands.concat('quit').join('\n')+'\n',encoding:'utf8',timeout:45000,maxBuffer:2000000});
 if(proc.error)throw proc.error;
 assert.equal(proc.status,0,'native bridge exit error: '+proc.stderr);
 const out=proc.stdout.trim().split('\n').map(JSON.parse);
 assert.equal(out.length,commands.length,'native bridge did not return exactly one response per command');
 for(const x of out)assert.ok(x?.ok&&/^[0-9a-f]{64}$/.test(x.nativeFrameSha256),'native bridge rejected a command');
 return out;
}
const opposite=s=>s==='A'?'B':'A';
function checkpoint(blocks,bridge=BRIDGE){
 assert.ok(Array.isArray(blocks)&&blocks.length<=2);
 const commands=start.slice(),next=[];
 let framesUsed=frames.opening;
 for(const block of blocks){
   const a=block.A,b=block.B;
   assert.ok(a?.commands?.length===4&&b?.commands?.length===4,'both synchronized four-window submissions required');
   for(let j=0;j<4;j++){
     assert.ok(tokens.includes(a.commands[j])&&tokens.includes(b.commands[j]),'native allowlisted literal controls required');
     commands.push('step 47 '+a.commands[j]+' '+b.commands[j]);
     framesUsed+=frames.window;next.push(framesUsed);
   }
   commands.push('observe');
 }
 const outputs=run(commands,bridge);
 assert.equal(outputs[0].frame,0);
 assert.equal(outputs[1].frame,44);
 assert.equal(outputs[1].nativeFrameSha256,outputs[2].nativeFrameSha256,'opening observation advanced or changed engine');
 let ix=0;
 for(let q=3;q<outputs.length;q++){
   const got=outputs[q],prev=outputs[q-1];
   if(commands[q]==='observe'){assert.equal(got.nativeFrameSha256,prev.nativeFrameSha256,'read-only observe changed engine');continue;}
   const expected=next[ix++];
   assert.ok(got.frame<=expected&&got.frame>=prev.frame&&(got.frame===expected||got.terminated),'native window advanced unexpectedly');
   if(prev.terminated)assert.equal(got.nativeFrameSha256,prev.nativeFrameSha256,'native terminal state advanced');
 }
 const timeline=outputs.map((state,i)=>({command:commands[i],state}));
 return {phase:blocks.length,timeline,last:timeline.at(-1).state,traceSha256:commit(timeline)};
}
function playerObservation(state,seat){
 assert.ok(seat==='A'||seat==='B');
 const actor=(s)=>s==='A'?state.p1:state.p2;
 const self=actor(seat),other=actor(opposite(seat));
 const visible=(x)=>({hp:x.hp,energy:x.energy,height:x.y,vxTowardOther:x.vx*(x.isFront?1:-1),verticalVelocity:x.vy,state:x.state,action:x.action,remainingActionFrames:x.remainingActionFrames,canAct:x.canAct});
 return {frame:state.frame,framesLeft:state.framesLeft,distancePx:Math.abs(self.x-other.x),self:visible(self),opponent:visible(other),terminated:state.terminated};
}
function decisionPair(first,second,raw){
 assert.ok(raw&&raw.A&&raw.B);
 return Object.fromEntries(['A','B'].map(seat=>[seat,response(raw[seat],tokens,first?1:2,first?null:peerLine(second,seat).messageHash)]));
}
module.exports={tokens,frames,run,checkpoint,playerObservation,decisionPair};
