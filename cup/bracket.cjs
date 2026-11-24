'use strict';
const fs=require('node:fs'),{createHash}=require('node:crypto');
const h=s=>createHash('sha256').update(s).digest('hex');
function seedRank(s){
 if(s.length===1)return s;
 return seedRank(s.slice(0,s.length/2)).flatMap(n=>[n,s.length+1-n]);
}
function apply(quals,played){
 if(quals.length!==50)throw Error('50 actual eligible heats necessary');
 const eligible=new Set(), note=new Map();
 for(const [i,q] of quals.entries()){
  if(q.wave!==i+1||!/^AAC-(0[1-9]|[1-4]\d|50)[AB]$/.test(q.winner)||+q.winner.slice(4,6)!==q.wave||eligible.has(q.winner))throw Error('Bad qualification '+(i+1));
  if(!q.transcript||q.transcript.length<2||new Set(q.transcript.map(t=>t.id)).size!==2||!q.transcript.every(t=>t.text.trim()))throw Error('Verified two-sided transcript required');
  eligible.add(q.winner);note.set(q.winner,q);
 }
 const rank=Array.from(eligible).sort((x,y)=>{
   const a=note.get(x),b=note.get(y);
   return (b.grade??0)-(a.grade??0)||Number(!!b.objectiveWin)-Number(!!a.objectiveWin)||h('aac-seat-v1/'+x).localeCompare(h('aac-seat-v1/'+y));
 });
 const placements=seedRank(Array.from({length:64},(_,i)=>i+1));
 if(new Set(placements).size!==64||placements.some(v=>v<1||v>64))throw Error('Unbalanced placements');
 let cur=placements.map(i=>({id:rank[i-1]??null,known:true}));
 const rows=[];const allowed=new Set();
 for(let r=1;r<=6;r++){
  const advance=[];
  for(let i=0;i<cur.length;i+=2){
   const m='KO'+r+'-'+String(i/2+1).padStart(2,'0'),a=cur[i],b=cur[i+1];allowed.add(m);
   const row={match:m,left:a.id,right:b.id,status:'waiting',winner:null};
   if(a.known&&b.known){
    if(!a.id||!b.id){row.status='bye';row.winner=a.id??b.id}
    else if(played[m]){
     const submitted=played[m];
     if(![a.id,b.id].includes(submitted.winner)||submitted.left!==a.id||submitted.right!==b.id||!submitted.evidence||!submitted.reason)throw Error('Invalid winner/evidence '+m);
     row.status='verified';row.winner=submitted.winner;row.reason=submitted.reason;row.evidence=submitted.evidence;
    }else row.status='ready';
   }
   if(played[m]&&row.status!=='verified')throw Error('Results logged before a real match existed '+m);
   rows.push(row);advance.push({id:row.winner,known:row.status==='verified'||row.status==='bye'});
  }
  cur=advance;
 }
 if(Object.keys(played).some(k=>!allowed.has(k)))throw Error('Unknown knockout ID');
 const champion=cur[0].id,verified=rows.filter(x=>x.status==='verified').length;
 if(champion&&verified!==49)throw Error('A champion requires exactly 49 verified played knockouts');
 return {champion,verified,planned:49,seeds:rank,rows};
}
module.exports={apply,seedRank};
if(require.main===module){const r=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));console.log(JSON.stringify(apply(r.quals,r.played),null,2));}
