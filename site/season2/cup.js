'use strict';
const $=id=>document.getElementById(id);
const canvas=$('canvas'),g=canvas.getContext('2d');
const matches=$('matches'),paint=['#ffb179','#a7ead5'];
let rows=[],match,position=0,last=null,playing=false,handle=0;
const player=n=>'M'+String(n+1).padStart(2,'0');
const words=s=>String(s).toLowerCase().replaceAll('_',' ');
function stop(){playing=false;last=null;cancelAnimationFrame(handle);$('play').textContent='Play';}
function card(cls,title,detail){const e=document.createElement('div'),b=document.createElement('strong');e.className=cls;b.textContent=title;e.append(b,document.createTextNode(detail));return e;}
function actor(x,y,face,action,color){
 const step=String(action).includes('DASH')||String(action).includes('WALK');
 const attack=/(?:_A|_B|THROW)/.test(action);
 const crouch=String(action).includes('CROUCH');
 const down=String(action).includes('DOWN');
 g.save();g.translate(x,y);g.scale(face,1);if(down)g.rotate(-1.27);
 g.strokeStyle=color;g.fillStyle=color;g.lineWidth=13;g.lineCap='round';
 const hip=crouch?-43:-61,arms=hip-33;
 g.beginPath();g.moveTo(0,hip);g.lineTo(0,arms);g.moveTo(0,hip);g.lineTo(step?30:17,-8);g.moveTo(0,hip);g.lineTo(step?-30:-17,-6);
 g.moveTo(0,arms);g.lineTo(attack?64:22,arms-14);g.moveTo(0,arms);g.lineTo(-23,arms+17);g.stroke();
 g.beginPath();g.arc(0,arms-31,19,0,Math.PI*2);g.fill();g.restore();
}
function sample(f){
 let lo=0,hi=match.samples.length-1;
 while(lo<hi){const m=Math.ceil((lo+hi)/2);if(match.samples[m][0]<=f)lo=m;else hi=m-1;}
 return [match.samples[lo],match.samples[Math.min(lo+1,match.samples.length-1)]];
}
function redraw(){
 if(!match)return;
 const frame=Math.max(44,Math.min(match.frame,Math.floor(position)));
 const [a,b]=sample(frame),t=b[0]>a[0]?(frame-a[0])/(b[0]-a[0]):0;
 const between=i=>a[i]+(b[i]-a[i])*t;
 g.fillStyle='#1a2828';g.fillRect(0,0,960,420);
 g.strokeStyle='#304442';g.lineWidth=1;for(let i=24;i<960;i+=31){g.beginPath();g.moveTo(i,120);g.lineTo(i,389);g.stroke();}
 g.fillStyle='#304540';g.fillRect(0,336,960,84);
 const xA=between(3), xB=between(4);
 actor(xA,336+(between(5)-537)*.65,xA<xB?1:-1,a[7],paint[0]);
 actor(xB,336+(between(6)-537)*.65,xB<xA?1:-1,a[8],paint[1]);
 const names=match.seats.map(player);
 g.font='700 24px system-ui';
 names.forEach((name,i)=>{let x=i?528:48;
  g.fillStyle='#425452';g.fillRect(x,58,384,14);g.fillStyle=paint[i];g.fillRect(x,58,Math.max(0,a[1+i])*384/400,14);
  g.fillText(name+' · '+Math.max(0,a[1+i])+' HP',x,43);
 });
 $('seek').value=String(frame);
 $('time').textContent=((frame-44)/60).toFixed(2)+' s · frame '+frame;
 $('actions').replaceChildren(...[0,1].map(i=>card('card',names[i]+' · '+Math.max(0,a[1+i])+' HP','Requested: '+words(a[9+i])+' · Executed: '+words(a[7+i]))));
}
function update(ts){if(!playing)return;if(last!==null)position+=(ts-last)*0.06*Number($('speed').value);last=ts;redraw();if(position>=match.frame)stop();else handle=requestAnimationFrame(update);}
function open(id){match=rows.find(m=>m.id===id);if(!match)return;stop();position=44;$('seek').min='44';$('seek').max=String(match.frame);$('pair').textContent=match.seats.map(player).join(' vs ')+(match.winner!==null?' · KO winner '+player(match.winner):' · Unresolved');redraw();}
matches.onchange=()=>open(matches.value);
$('play').onclick=()=>{if(playing)return stop();if(!match)return;if(position>=match.frame)position=44;playing=true;last=null;$('play').textContent='Pause';handle=requestAnimationFrame(update);};
$('reset').onclick=()=>{stop();position=44;redraw();};
$('seek').oninput=()=>{stop();position=Number($('seek').value);redraw();};
(async()=>{const r=await fetch('./knockout.json');if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(d.schema!==1||!d.matches.length)throw Error('invalid');rows=d.matches;
 for(const m of rows){const o=document.createElement('option');o.value=m.id;o.textContent=m.id+' · '+m.seats.map(player).join(' vs ');matches.append(o);}
 matches.value=rows.at(-1).id;open(matches.value);
 $('stats').append(card('metric',d.winner===null?'No champion':player(d.winner),'Champion'),card('metric',rows.filter(r=>r.result==='ko').length+' / '+rows.length,'Engine-confirmed KOs'),card('metric',Math.max(...rows.map(r=>r.inferenceP95ms)).toFixed(2)+' ms','Highest match p95, paired model inference'),card('metric','100 ms','New decision window'));
 for(const p of d.probe){if(p.unguarded===p.guarding)continue;const e=document.createElement('li');e.textContent=player(p.entrant)+': '+words(p.unguarded)+' → '+words(p.guarding)+' when the opponent guards';$('probes').append(e);}
})().catch(()=>{$('error').hidden=false;});
