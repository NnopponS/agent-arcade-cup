'use strict';
// A turn coordinator for authentic retained-agent dialogue. This does not call or simulate any contestant.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const p=require('../primary/src/puzzles.cjs');
const logdir=process.env.AAC_CUP_LOG||path.join(__dirname,'observed');
const hash=(s)=>crypto.createHash('sha256').update(s).digest();
const isID=s=>/^AAC-(0[1-9]|[1-4]\d|50)[AB]$/.test(s||'');
const isMatch=s=>/^(Q(0[1-9]|[1-4]\d|50)|KO[1-6]-(0[1-9]|[12]\d|3[0-2]))$/.test(s||'');
const show=b=>Array.from({length:6},(_,i)=>b.slice(i*7,i*7+7).join(' ')).join('\n')+'\n0 1 2 3 4 5 6';
const finish=x=>x.winner||x.finishingReason;
function origin(id) {
 let s=hash('aac-open-play-board-2026-v1/'+id).readUInt32BE();
 const rng=()=>((s=(Math.imul(1664525,s)+1013904223)>>>0)/4294967296);
 for(let j=0;j<16000;j++){
   let b=Array(42).fill('.'),t='X',moves=[],n=28;
   for(let i=0;i<n;i++){
     const opts=[0,1,2,3,4,5,6].map(c=>p.drop(b,c,t)).filter(x=>x&&!p.wins(x,t));
     if(!opts.length)break;
     const win=opts[Math.floor(rng()*opts.length)];b=win.board;t=p.other(t);moves.push(win.c);
   }
   if(moves.length===n&&!p.winningMoves(b,'X',2).length&&!p.winningMoves(b,'O',1).length&&p.winningMoves(b,'X',3).length===1)
     return {opening:moves,board:b};
 }
 throw Error('Generator could not certify a valid opening '+id);
}
function file(m){if(!isMatch(m))throw Error('Unknown match format');return path.join(logdir,m+'.json');}
function save(m){fs.mkdirSync(logdir,{recursive:true});const f=file(m.id);fs.writeFileSync(f+'.tmp',JSON.stringify(m,null,2)+'\n');fs.renameSync(f+'.tmp',f);}
function start(id,a,b){
 if(!isID(a)||!isID(b)||a===b)throw Error('Need two distinct observed fresh IDs');
 if(fs.existsSync(file(id)))throw Error('Match already exists; no rerolls');
 const swap=hash('aac-open-seats-2026-v1/'+id)[0]%2===1;
 const {opening,board}=origin(id);
 const m={id,phase:'open play (never part of sealed inference)',players:{X:swap?b:a,O:swap?a:b},opening,board,turn:'X',turns:[],maxTurns:14,startedAt:new Date().toISOString()};
 save(m);return m;
}
function load(id){return JSON.parse(fs.readFileSync(file(id),'utf8'));}
function turn(m,id,rec){
 if(finish(m))throw Error('Finished match');
 if(m.players[m.turn]!==id)throw Error('Only the assigned player may move');
 if(!rec||typeof rec.line!=='string'||rec.line.trim().length<2||rec.line.length>160)throw Error('One authentic player line is required');
 const next=p.drop(m.board,rec.column,m.turn);
 const line=rec.line;
 const e={author:id,side:m.turn,submittedColumn:rec.column,line,before:m.board,after:next?.board??null,legal:!!next,observedAt:new Date().toISOString()};
 m.turns.push(e);
 if(next){
   m.board=next.board;
   if(p.wins(next,m.turn)){m.winner=id;m.finishingReason='four connected';}
   else if(!m.board.includes('.'))m.finishingReason='filled board; tiebreak required';
 }else{
   m.winner=m.players[p.other(m.turn)];m.finishingReason='illegal move';
 }
 if(!finish(m))m.turn=p.other(m.turn);
 if(m.turns.length>=m.maxTurns&&!finish(m))m.finishingReason='ply cap; tiebreak required';
 if(finish(m))m.endedAt=new Date().toISOString();
 save(m);return m;
}
function invite(m){
 if(finish(m))return null;
 const id=m.players[m.turn],opponent=m.players[p.other(m.turn)];
 const last=m.turns.at(-1);
 return {id,opponent,prompt:`You are continuing as actual entrant ${id}. This is OPEN TOURNAMENT PLAY, not the frozen research question. CONNECT FOUR: cols 0–6, rows top to bottom, lowest open cell, four in a row wins. You are '${m.turn}'. Current board:\n${show(m.board)}\n${last?`Actual opposing entrant ${opponent} said: ${JSON.stringify(last.line)} and played column ${last.submittedColumn}.\nReply to their actual line as part of your short in-character dialogue.`:'Open with one short line to your opponent. Do not fabricate their response.'}\nPlay your best legal move. Reply exactly as JSON {"column":2,"line":"one original English line to the opponent"} (replace both example fields). No tools or private reasoning needed.`};
}
module.exports={origin,start,load,turn,invite,show,finish};
if(require.main===module){
 const [cmd,id,x,y]=process.argv.slice(2);
 const m=cmd==='start'?start(id,x,y):cmd==='turn'?turn(load(id),x,JSON.parse(y)):load(id);
 console.log(JSON.stringify({state:m,next:invite(m)},null,2));
}
