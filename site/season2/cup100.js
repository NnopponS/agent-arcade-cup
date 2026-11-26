'use strict';
const $=id=>document.getElementById(id);
let m, time=0, active=false, last, raf, selection=0;
let selectedId;
const seconds=f=>(f/60).toFixed(1)+' s';
const stillMotion=()=>globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches===true;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const lerp=(a,b,t)=>a+(b-a)*t;
const swing=Math.sin;
function moveVisual(action, clock, reduced){
 const gait=reduced?0:swing(clock*.29), drift=reduced?0:swing(clock*.088);
 const t=clamp(clock/14,0,1), arc=swing(Math.PI*t), extend=reduced?.65:arc;
 // [body x, visual lift, torso pitch, near arm, far arm, near leg, far leg]
 if(action.includes('GUARD'))return [0,0,-9,-94,-80,12,-9];
 if(action.includes('RECOV')||action.includes('SUFFER')||action.includes('DOWN'))return [-4,action.startsWith('AIR')?-15:2,-17-extend*13,30+18*extend,49,-23,22];
 if(action.startsWith('THROW'))return [8*extend,1,8+extend*9,-58-extend*31,-56-extend*11,-22,18];
 if(action.startsWith('STAND_F')||action.startsWith('AIR_F'))return [4,action.startsWith('AIR')?-18:0,13,-75-extend*50,-45+25*extend,-24,20];
 if(action.endsWith('_B')||action.endsWith('_DB')||action.endsWith('_UB'))return [1,action.startsWith('AIR')?-19:action.startsWith('CROUCH')?12:1,-10-extend*6,-23,-54,-25-extend*(action.startsWith('CROUCH')?59:89),11];
 if(action.endsWith('_A')||action.endsWith('_DA')||action.endsWith('_UA'))return [5*extend,action.startsWith('AIR')?-18:action.startsWith('CROUCH')?12:0,11,-53-extend*82,-32-9*extend,-17,14];
 if(action.includes('JUMP')||action.startsWith('AIR'))return [0,-16-14*extend,4,-55+10*gait,-36,-35,33];
 if(action==='LANDING')return [0,7,11,-45,-35,19,-16];
 if(action.startsWith('CROUCH'))return [0,13,12,-57,-48,-25,18];
 if(/DASH|WALK|STEP/.test(action))return [0,-Math.abs(gait)*4,action.includes('BACK')?-10:13,-33+gait*24,-34-gait*27,36*gait,-36*gait];
 return [0,-1.7*drift,drift*2,-37+2*gait,-26-3*gait,-9,9];
}
function annotateFight(){
 const end=m.elapsedFrames||1, chartX=f=>42+f/end*668, chartY=h=>83-clamp(h,0,400)/400*70;
 for(let seat=1;seat<=2;seat++){
  let d='M42 '+chartY(m.frames[0][seat]);let prev=m.frames[0][seat];
  for(const row of m.frames.slice(1)){
   const x=chartX(row[0]-m.start);
   if(row[seat]!==prev){d+='H'+x.toFixed(1)+'V'+chartY(row[seat]).toFixed(1);prev=row[seat]}
  }
  $('chart'+seat).setAttribute('d',d+'H710');
 }
 const swings=[];
 m.frames.slice(1).forEach((row,j)=>{
  for(let seat=1;seat<=2;seat++){
   const loss=Math.max(0,m.frames[j][seat])-Math.max(0,row[seat]);
   if(loss>0&&row[seat]>0)swings.push({loss,f:row[0]-m.start,seat});
  }
 });
 swings.sort((a,b)=>b.loss-a.loss||a.f-b.f);
 const picks=[];for(const hit of swings){if(picks.every(p=>Math.abs(p.f-hit.f)>=120))picks.push(hit);if(picks.length===2)break}
 const moments=$('moments');moments.replaceChildren();
 for(const e of [...picks.sort((a,b)=>a.f-b.f),{f:end}]){
  const b=document.createElement('button');b.type='button';
  b.textContent=e.loss?seconds(e.f)+' · '+m.seats[e.seat-1]+' −'+e.loss+' HP':seconds(e.f)+' · KO';
  b.onclick=()=>{stop();time=e.f;paint()};moments.append(b);
 }
}

function paint(){
 const frame=m.start+Math.floor(time), samples=m.frames;
 let lo=0, hi=samples.length;
 while(lo+1<hi){const mid=(lo+hi)>>1;if(samples[mid][0]<=frame)lo=mid;else hi=mid}
 const r=samples[lo],next=samples[lo+1], reduced=stillMotion();
 const blend=next&&!reduced?clamp((frame-r[0])/(next[0]-r[0]),0,1):0;
 $('endcard').classList.toggle('show',time>=m.elapsedFrames);
 const timelineX=42+668*clamp(time/(m.elapsedFrames||1),0,1);
 $('chart-cursor').setAttribute('d','M'+timelineX.toFixed(1)+' 5V89');
 for(let i=1;i<=2;i++){
  const hp=Math.max(0,r[i]), action=r[4+i], pos=j=>lerp(r[j],next?.[j]??r[j],blend);
  const x=clamp(pos(i+2),45,915), other=pos(i===1?4:3), face=x<=other?1:-1;
  $('p'+i).value=hp;$('h'+i).textContent=hp+' HP';$('a'+i).textContent=action.replaceAll('_',' ');
  let j=lo;while(j>0&&r[0]-samples[j-1][0]<60&&samples[j-1][4+i]===action)j--;
  const phase=frame-samples[j][0],pose=moveVisual(action, phase,reduced),ko=hp===0;
  const el=$('f'+i), body=$('body'+i);
  el.setAttribute('transform','translate('+x+' 0) scale('+face+' 1)');
  body.setAttribute('transform',ko?'translate(0 221) rotate(85) scale(.76) translate(0 -148)':'translate('+pose[0]+' '+pose[1]+') rotate('+pose[2]+' 0 176)');
  for(const [type,cx,cy,deg] of [['front-arm',10,140,pose[3]+34],['back-arm',-13,138,pose[4]-26],['front-leg',-7,161,pose[5]-12],['back-leg',8,163,pose[6]+19]]){
   if(body.querySelector)body.querySelector('.'+type).setAttribute('transform','rotate('+deg+' '+cx+' '+cy+')');
  }
  $('tag'+i).setAttribute('x',x);$('tag'+i).setAttribute('y',ko?263:74+pose[1]);$('tag'+i).textContent=m.seats[i-1];
  let hit=null;for(let k=lo;k>0&&frame-samples[k][0]<=14;k--)if(samples[k][i]<samples[k-1][i]){hit=samples[k][0];break}
  const age=hit===null?15:frame-hit;
  const flare=$('flare'+i);flare.setAttribute('transform','translate('+x+' '+(ko?43:pose[1])+')');flare.style.opacity=reduced?'0':String(clamp(1-age/15,0,1));
 }
 $('stamp').textContent=seconds(time)+' / '+seconds(m.elapsedFrames);
 $('scrub').value=Math.round(time);
 $('scrub').setAttribute('aria-valuetext',seconds(time)+' of '+seconds(m.elapsedFrames));
}
function stop(){active=false;cancelAnimationFrame(raf);last=undefined;$('play').textContent='Play'}
function tick(t){
 if(!active)return;
 if(last!==undefined)time=Math.min(m.elapsedFrames,time+(t-last)*.06*Number($('rate').value));
 last=t;paint();
 if(time<m.elapsedFrames)raf=requestAnimationFrame(tick);else stop();
}
async function loadReplay(id){
 selectedId=id;
 stop();m=null;$('endcard').classList.remove('show');$('play').disabled=true;$('scrub').disabled=true;
 const seq=++selection;
 $('retry-replay').hidden=true;
 $('copy-status').textContent='';
 $('match-feed').textContent=id+' / ENGINE TELEMETRY';
 $('outcome').textContent='Loading replay…';
 $('stamp').textContent='';
 for(const seat of [1,2]){
  $('n'+seat).textContent='';
  $('h'+seat).textContent='';
  $('a'+seat).textContent='';
  $('p'+seat).value=0;
 }
 $('scrub').value=0;
 $('moments').replaceChildren();for(const n of ['chart1','chart2','chart-cursor'])$(n).setAttribute('d','');$('arena').style.visibility='hidden';
 try{
  const reply=await fetch('cup100-replay/'+id+'.json');
  if(!reply.ok)throw Error('missing');
  const file=await reply.json();
  const bytes=Uint8Array.from(atob(file),ch=>ch.charCodeAt(0));
  const data=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  if(seq!==selection)return;
  m={frames:data.frames,seats:data.entrantIds,start:data.frames[0][0],
    elapsedFrames:data.frames.at(-1)[0]-data.frames[0][0],verdict:data.winner+' won by engine KO'};
  $('arena').style.visibility='visible';annotateFight();$('winner').textContent=data.winner;
  time=0;$('scrub').max=m.elapsedFrames;$('scrub').disabled=false;
  for(let i=1;i<=2;i++)$('n'+i).textContent=m.seats[i-1];
  $('outcome').textContent=m.verdict;paint();$('play').disabled=false;
 }catch{
  if(seq!==selection)return;
  $('outcome').textContent='Could not load the replay.';
  $('retry-replay').hidden=false;
 }
}
$('play').onclick=()=>{if(!m)return;if(active){stop();return}if(time>=m.elapsedFrames)time=0;active=true;$('play').textContent='Pause';raf=requestAnimationFrame(tick)};
$('scrub').oninput=()=>{if(m){stop();time=Number($('scrub').value);paint()}};

const pageSize = 12;
const filterForm = $('bracket-filters');
const search = $('bout-search');
const round = $('bout-round');
const entryType = $('bout-type');
const showMore = $('show-more');
const archive = [...document.querySelectorAll('#bracket tbody tr')].map(row => {
  const id = row.cells[0].textContent.trim();
  const replay = row.querySelector('th a');
  return {
    id,
    row,
    replay,
    round: id.split('-')[0],
    type: replay ? 'played' : 'bye',
    searchText: [id, row.cells[1].textContent, replay ? row.cells[2].textContent : ''].join(' ').toLowerCase(),
  };
});
const replayIds = new Set(archive.filter(entry => entry.replay).map(entry => entry.id));
let visibleLimit = pageSize;

function renderArchive() {
  const tokens = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const matches = archive.filter(entry =>
    (entryType.value === 'all' || entryType.value === entry.type) &&
    (round.value === 'all' || round.value === entry.round) &&
    tokens.every(token => entry.searchText.includes(token))
  );
  const visible = new Set(matches.slice(0, visibleLimit));
  for (const entry of archive) entry.row.hidden = !visible.has(entry);
  $('bracket-table').hidden = matches.length === 0;
  $('no-matches').hidden = matches.length !== 0;
  $('filter-count').textContent = `${visible.size} of ${matches.length} ${matches.length === 1 ? 'entry' : 'entries'}`;
  const remaining = matches.length - visible.size;
  showMore.hidden = remaining === 0;
  showMore.textContent = `Show ${Math.min(pageSize, remaining)} more`;
  return matches;
}

filterForm.addEventListener('submit', event => event.preventDefault());
filterForm.addEventListener('reset', event => {
  event.preventDefault();
  search.value = '';
  round.value = 'all';
  entryType.value = 'played';
  visibleLimit = pageSize;
  renderArchive();
  search.focus();
});
filterForm.addEventListener('input', () => {
  visibleLimit = pageSize;
  renderArchive();
});
showMore.addEventListener('click', () => {
  const previousLimit = visibleLimit;
  visibleLimit += pageSize;
  const next = renderArchive()[previousLimit];
  if (!next) return;
  const target = next.replay || next.row.cells[0];
  if (!next.replay) target.tabIndex = -1;
  target.focus();
});

function replayHref(id) {
  return `?match=${id}#cup-replay`;
}

function selectReplay(id) {
  document.querySelectorAll('a[href^="?match="]').forEach(link => {
    if (link.getAttribute('href') === replayHref(id)) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
  $('copy-replay').disabled = false;
  if (selectedId !== id) loadReplay(id);
}

function syncReplayRoute() {
  const id = new URLSearchParams(location.search).get('match');
  selectReplay(replayIds.has(id) ? id : 'R7-01');
}

document.addEventListener('click', event => {
  if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  const link = event.target.closest('a[href^="?match="]');
  if (!link || link.target || link.hasAttribute('download')) return;
  const id = new URL(link.href).searchParams.get('match');
  if (!replayIds.has(id)) return;
  event.preventDefault();
  if (location.href !== link.href) history.pushState(null, '', link.href);
  selectReplay(id);
  $('cup-replay').scrollIntoView();
  $('replay-title').focus({preventScroll: true});
});
window.addEventListener('popstate', syncReplayRoute);
$('retry-replay').addEventListener('click', () => loadReplay(selectedId));
$('copy-replay').addEventListener('click', async () => {
  const id = selectedId;
  const url = new URL(replayHref(id), location.href).href;
  let message = 'Replay link copied.';
  try {
    await navigator.clipboard.writeText(url);
  } catch {
    message = 'Copy this replay link from the address bar.';
    if (selectedId === id && location.href !== url) history.replaceState(null, '', url);
  }
  if (selectedId === id) $('copy-status').textContent = message;
});

renderArchive();
filterForm.hidden = false;
document.querySelector('.replay-actions').hidden = false;
syncReplayRoute();
