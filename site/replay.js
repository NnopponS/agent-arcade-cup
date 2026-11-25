'use strict';
(() => {
  const clockAdvance = (frame, elapsed, speed, stepHz, end) => Math.min(end, frame + Math.max(0, elapsed)*speed*stepHz/1000);
  function windowAt(windows, frame) {
    let i = 0;
    while (i+1 < windows.length && windows[i+1][0] < frame) i++;
    return i;
  }
  function keyLabel(mask) {
    const keys = [[64,'←'],[8,'↑'],[16,'→'],[32,'↓'],[1,'A'],[2,'B'],[4,'C']];
    return keys.filter(([bit])=>mask&bit).map(([,key])=>key).join(' ') || '–';
  }
  function fighterAt(row, seat) {
    const i = 7*seat;
    return {hp:row[i],energy:row[i+1],x:row[i+2],y:row[i+3],action:row[i+4],state:row[i+5],front:!!row[i+6],keys:row[14+seat]};
  }
  if (typeof module === 'object' && module.exports) {
    module.exports = {clockAdvance,windowAt,keyLabel,fighterAt};
    return;
  }

  const shell = document.getElementById('match-replay');
  const $ = id => document.getElementById('replay-'+id);
  const canvas = $('canvas'), g = canvas.getContext('2d');
  const speed = $('speed'), range = $('seek');
  const speeds = new Set([.25,.5,1,1.5,2,4]);
  const packCache = new Map();
  let catalogPromise, match, data, number = 0, max = 0, clock = 0, last = 0, frameHandle = 0, playing = false, revision = 0;
  const palettes = [
    {dark:'#6a2d21', mid:'#c9603a', light:'#ffd4b1', glow:'#ffc57c'},
    {dark:'#173c37', mid:'#439283', light:'#c3f5db', glow:'#8ef3c5'}
  ];
  const boardTitles = {'2048':'2048', sliding:'Sliding Puzzle', lights:'Lights Out', battleship:'Battleship'};
  const actionWords = {
    NEUTRAL:'ยืน', FORWARD_WALK:'เดินหน้า', STAND:'ยืน', BACK_STEP:'ถอย', DASH:'พุ่ง',
    STAND_GUARD:'ยืนป้องกัน', CROUCH_GUARD:'ย่อป้องกัน', AIR_GUARD:'ป้องกันกลางอากาศ',
    FOR_JUMP:'กระโดดไปหน้า', BACK_JUMP:'กระโดดถอย', JUMP:'กระโดด',
    CROUCH_A:'โจมตีต่ำ A', CROUCH_B:'โจมตีต่ำ B', STAND_A:'โจมตี A', STAND_B:'โจมตี B',
    STAND_FA:'โจมตีหน้า A', STAND_FB:'โจมตีหน้า B', THROW_A:'จับทุ่ม',
    STAND_D_DF_FA:'ท่าพิเศษ A', STAND_F_D_DFB:'ท่าพิเศษ B',
    STAND_RECOV:'ฟื้นจากการโจมตี', CROUCH_RECOV:'ฟื้นจากการโจมตี', AIR_RECOV:'ฟื้นกลางอากาศ',
    CROUCH:'ย่อตัว', LANDING:'ลงพื้น', CHANGE_DOWN:'ล้ม', DOWN:'ล้ม', RISE:'ลุกขึ้น'
  };
  function status(text, show = true) {
    $('status').textContent = text;
    $('status').hidden = !show;
  }
  function getJson(path) {
    return fetch(path,{credentials:'omit',referrerPolicy:'no-referrer'})
      .then(r=>{if(!r.ok) throw new Error('replay HTTP '+r.status);return r.json();});
  }
  function catalog() {
    catalogPromise ||= getJson('./replays/index.json').then(x=>{
      if(x?.schema!==1 || x.meta?.fixed_hz!==60 || !x.files) throw new Error('replay index');
      return x.files;
    }).catch(error=>{catalogPromise=undefined;throw error;});
    return catalogPromise;
  }
  function pack(name) {
    if(!/^pack-\d{2}\.json$/.test(name)) throw new Error('replay pack name');
    if(!packCache.has(name)) {
      if(packCache.size>=5) packCache.delete(packCache.keys().next().value);
      packCache.set(name,getJson('./replays/'+name).catch(err=>{packCache.delete(name);throw err;}));
    }
    return packCache.get(name);
  }
  async function unpack(text) {
    if(typeof text!=='string' || text.length>44800) throw new Error('replay size');
    if(typeof DecompressionStream!=='function') throw new Error('browser compression support');
    const buf=Uint8Array.from(atob(text),c=>c.charCodeAt(0));
    return new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  }
  function validate(m,x) {
    if(m.series==='fighting') {
      if(x?.e!==60 || !Array.isArray(x?.m) || !Array.isArray(x?.z) || !Array.isArray(x?.c) || !x.c.length ||
        !Array.isArray(x?.f) || x.f.length!==m.frame+1 || x.f.some(r=>!Array.isArray(r)||r.length!==17) ||
        x.f.at(-1)[0]!==m.score[0] || x.f.at(-1)[7]!==m.score[1]) throw new Error('fight trace');
      return x.f.length-1;
    }
    if(!Object.hasOwn(boardTitles,x?.g) || !m.moves || !['a','b'].every((s,i)=>
      Array.isArray(x[s]?.s) && x[s].s.length===m.moves[i]+1 && Array.isArray(x[s]?.i) && x[s].i.length===m.moves[i]
    )) throw new Error('pilot replay');
    return Math.max(...m.moves);
  }
  function canvasSize() {
    if (!g || $('surface').hidden) return;
    const box=canvas.getBoundingClientRect();
    const w = Math.max(1,Math.round(box.width*Math.min(devicePixelRatio||1,2)));
    const h = Math.max(1,Math.round(box.height*Math.min(devicePixelRatio||1,2)));
    if(canvas.width!==w || canvas.height!==h) { canvas.width=w; canvas.height=h; }
  }
  const paint = (fill,x,y,w,h) => {g.fillStyle=fill;g.fillRect(x,y,w,h);};
  const line = (color,width,points) => {
    g.strokeStyle=color;g.lineWidth=width;g.lineCap='round';g.lineJoin='round';
    g.beginPath();g.moveTo(...points[0]);points.slice(1).forEach(p=>g.lineTo(...p));g.stroke();
  };
  const circle = (x,y,rx,ry,fill) => {g.beginPath();g.ellipse(x,y,rx,ry,0,0,Math.PI*2);g.fillStyle=fill;g.fill();};
  const shape = (fill,points) => {g.beginPath();g.moveTo(...points[0]);points.slice(1).forEach(p=>g.lineTo(...p));g.closePath();g.fillStyle=fill;g.fill();};
  function rect(fill,x,y,w,h,r) {
    g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=fill;g.fill();
  }
  function txt(label,x,y,sz,color,align='left',weight=700) {
    g.fillStyle=color;g.font=weight+' '+sz+'px system-ui,sans-serif';g.textAlign=align;g.textBaseline='middle';g.fillText(label,x,y);
  }
  const fieldX = x => 16+x*.966;
  const groundY=349;
  const fieldY = y => groundY+(y-537)*.68;
  function arenaBackground() {
    const wall=g.createLinearGradient(0,0,0,390);
    wall.addColorStop(0,'#201d1e');wall.addColorStop(.58,'#302928');wall.addColorStop(1,'#635144');
    paint(wall,0,0,960,430);
    g.save();g.globalAlpha=.21;
    shape('#ba8958',[[115,0],[177,0],[495,353],[290,353]]);
    shape('#8ca995',[[793,0],[855,0],[690,352],[485,352]]);
    g.restore();
    for(let i=0;i<13;i++) {
      const x=18+i*76;
      line('#574537',1,[[x,0],[x,262]]);
      if(i<12) paint('#352c29',x+5,226,63,16+(i%3)*7);
    }
    paint('#392f2b',0,251,960,13);
    paint('#494138',0,278,960,2);
    const floor=g.createLinearGradient(0,269,0,430);
    floor.addColorStop(0,'#5f5445');floor.addColorStop(1,'#1e221e');
    paint(floor,0,269,960,161);
    for(let i=0;i<13;i++)line('#72604b',1,[[480+(i-6)*60,270],[480+(i-6)*133,430]]);
    for(const y of [277,288,308,339,381,420])line('#72604b',1,[[0,y],[960,y]]);
    line('#bb975f',2,[[18,349],[942,349]]);
    g.save();g.globalAlpha=.18;g.beginPath();g.ellipse(480,369,143,20,0,0,Math.PI*2);g.strokeStyle='#f3d4a1';g.lineWidth=2;g.stroke();g.restore();
    txt('ARCADE CUP',35,76,28,'#b69a73','left',760);
    txt('REPLAY ARENA',37,103,15,'#d3b896','left',630);
  }
  function pose(actor, seat, action, state, hit) {
    const t=number, theme=palettes[seat];
    const walking=/WALK|DASH|BACK_STEP/.test(action), guard=/GUARD/.test(action), low=/CROUCH/.test(state)||/CROUCH/.test(action);
    const air=state==='AIR'||/JUMP/.test(action), hurt=/RECOV|DAMAGE|DOWN|HIT/.test(action), punch=/_(A|B)$|_F[AB]$|D_DF|D_DFB|THROW/.test(action)&&!guard;
    const stride=walking ? Math.sin(t*.27)*22 : 0, torso=low?28:hurt?12:0;
    const centerY=fieldY(actor.y);
    g.save();g.translate(fieldX(actor.x),centerY);g.scale(actor.front?1:-1,1);
    const lean=hurt?-21:walking?10:punch?17:0;
    const hip=[lean, -52+torso*.55], shoulder=[lean+3,-105+torso], helmet=[lean+7,-128+torso];
    const frontKnee=[28+stride,-26+(air?-17:0)], backKnee=[-23-stride,-26+(air?-13:0)];
    const frontFoot=[36+stride,air?-18:0], backFoot=[-27-stride,air?-15:0];
    const elbow1=[guard?41:29, -82 + torso], hand1=[guard?49:punch?91:41, guard?-113+torso:punch?-94+torso:-94+torso];
    const elbow2=[-18, -79+torso], hand2=[guard?36:17, -105+torso];
    const limb=(points,inner=theme.mid)=>{line('#191b19',20,points);line(inner,13,points);line(theme.light,2,points);};
    limb([hip,backKnee,backFoot],theme.dark);limb([shoulder,elbow2,hand2],theme.dark);
    limb([hip,frontKnee,frontFoot]);line('#181817',9,[frontFoot,[frontFoot[0]+11,frontFoot[1]]]);line('#181817',9,[backFoot,[backFoot[0]+11,backFoot[1]]]);
    shape('#171a17',[[shoulder[0]-24,shoulder[1]-7],[shoulder[0]+25,shoulder[1]-5],[hip[0]+22,hip[1]+8],[hip[0]-24,hip[1]+8]]);
    shape(hit?'#fff2bd':theme.mid,[[shoulder[0]-19,shoulder[1]-2],[shoulder[0]+18,shoulder[1]-1],[hip[0]+17,hip[1]+1],[hip[0]-18,hip[1]+2]]);
    line(theme.light,4,[[shoulder[0]-13,shoulder[1]+3],[hip[0]+11,hip[1]-5]]);
    limb([shoulder,elbow1,hand1]);circle(...hand1, 9,9,theme.glow);
    circle(...helmet, 18,19,'#171a19');circle(...helmet,14,15,hit?'#fff3ad':theme.mid);
    line(theme.glow,5,[[helmet[0]+2,helmet[1]-2],[helmet[0]+13,helmet[1]-3]]);
    if(guard)line(theme.glow,4,[[52,-107+torso],[63,-89+torso],[55,-68+torso]]);
    g.restore();
  }
  function recentHit(data, frame, seat) {
    const key=seat*7;
    for(let rewind=0;rewind<9&&frame>rewind;rewind++) {
      const t=frame-rewind;
      const damage=data.f[t-1][key]-data.f[t][key];
      if(damage>0) return {damage,age:rewind};
    }
    return null;
  }
  function fightCanvas() {
    arenaBackground();
    const row=data.f[number], fighters=[fighterAt(row,0),fighterAt(row,1)];
    for(const [i,p] of fighters.entries()){
      g.save();g.globalAlpha=.49;circle(fieldX(p.x),groundY+4,40,8,'#161916');g.restore();
      const act=data.m[p.action], hit=recentHit(data,number,i);
      pose(p,i,act,data.z[p.state],hit&&hit.age<3);
      if(hit) {
        const x=fieldX(p.x),y=fieldY(p.y)-100;
        g.save();g.globalAlpha=(9-hit.age)/9;
        circle(x,y,14+hit.age*2,14+hit.age*2,'#ffc66a');
        for(let a=0;a<7;a++) {
          const theta=a*Math.PI*2/7+2, mid=13+hit.age*2;
          line('#ffd580',3,[[x+Math.cos(theta)*mid,y+Math.sin(theta)*mid],[x+Math.cos(theta)*(mid+14),y+Math.sin(theta)*(mid+14)]]);
        }
        txt('−'+hit.damage,x,y-24-hit.age*3,23,'#fff4d2','center',840);g.restore();
      }
    }
    for(const [owner,left,top,right,bottom] of row[16]){
      const x=fieldX((left+right)/2), y=fieldY((top+bottom)/2-45);
      const rx=Math.max(10,(right-left)*.47), ry=Math.max(6,(bottom-top)*.31);
      const flare=g.createRadialGradient(x,y,2,x,y,Math.max(rx,12));
      flare.addColorStop(0,'#fffadd');flare.addColorStop(.4,palettes[owner].glow);flare.addColorStop(1,'transparent');
      circle(x,y,rx+8,ry+6,flare);circle(x,y,rx*.47,ry*.53,'#fff5d3');
    }
    if(number>=max) {
      rect('#f5e8cb',218,141,524,100,12);
      txt(match.winner?'WINNER  '+match.winner:'DRAW',480,169,30,'#3a3229','center',800);
      txt(fighters.map(p=>p.hp).join('  :  ')+'  HP',480,208,23,'#725433','center',700);
    }
  }
  const tileColors=['#ded0b8','#ecd9aa','#e6bf7c','#efae69','#e09062','#c26f45','#aa6240','#87774a','#74613d','#6b5240','#534935','#3a533f'];
  function puzzleCanvas() {
    paint('#302e28',0,0,960,430);
    const mode=data.g;
    for(const [i,key] of ['a','b'].entries()){
      const s=data[key].s[Math.min(number,data[key].s.length-1)];
      const [n,,cells]=s, x=52+464*i, y=51, unit=320/n;
      rect('#3f3b32',x-11,y-11,342,342,13);
      for(let k=0;k<cells.length;k++) {
        const c=k%n,r=Math.floor(k/n),v=cells[k];
        let color,label='',text='#292416';
        if(mode==='2048'){color=tileColors[Math.min(tileColors.length-1,v?Math.log2(v):0)];label=v||'';if(v>=32)text='#fff6e2';}
        if(mode==='sliding'){color=v?tileColors[Math.floor(v/2)%10+1]:'#282b25';label=v||'';if(v>=11)text='#fff6e2';}
        if(mode==='lights'){color=v?'#f8d36d':'#235044';label=v?'●':'·';text=v?'#50370c':'#a7d8c7';}
        if(mode==='battleship'){color=['#294a53','#658a8e','#bc7557','#773529'][v];label=['','·','×','●'][v];text='#fff4dc';}
        const atX=x+c*unit, atY=y+r*unit;
        rect(color,atX+2,atY+2,unit-4,unit-4,Math.min(9,unit*.18));
        if(label) txt(label,atX+unit/2,atY+unit/2,unit*(String(label).length>2?.35:.58),text,'center');
      }
      txt(key.toUpperCase()+'  ·  '+boardTitles[mode], x+160,400,26,'#f5e7cb','center',790);
    }
    line('#e8bf73',1,[[445,63],[445,352]]);
  }
  function formatTime(frame) {return (frame/60).toFixed(2)+' วิ';}
  function poseLabel(name) {
    return name ? (actionWords[name] ? actionWords[name]+' · '+name : name.replaceAll('_',' ')+' · '+name) : '–';
  }
  function pilotMove(choice, mode, n) {
    const direction={up:'↑ บน',down:'↓ ล่าง',left:'← ซ้าย',right:'→ ขวา'};
    if(choice===undefined) return '–';
    if(Object.hasOwn(direction,choice)) return direction[choice];
    return mode==='battleship'
      ? String.fromCharCode(65+Math.floor(choice/n))+((choice%n)+1)
      : 'แถว '+(Math.floor(choice/n)+1)+' · ช่อง '+((choice%n)+1);
  }
  function details() {
    const isFight=match.series==='fighting';
    const row=isFight?data.f[number]:null, ci=isFight?windowAt(data.c,number):0;
    for(const [i,key] of ['a','b'].entries()){
      $(key+'-name').textContent=(i?'B  ':'A  ')+(i?match.b:match.a);
      const bar=$(key+'-hp');
      bar.hidden=!isFight;
      if(isFight){
        const p=fighterAt(row,i);
        bar.value=p.hp;
        $(key+'-score').textContent=p.hp+' / 400 HP';
        $(key+'-action').textContent=poseLabel(data.m[p.action]);
        $(key+'-order').textContent=number===0?'–':data.m[data.c[ci][i+1]];
        $(key+'-keys').textContent=keyLabel(p.keys);
      } else {
        const seq=data[key], step=Math.min(number,seq.s.length-1), [n,score,cells]=seq.s[step];
        $(key+'-score').textContent=data.g==='2048'?score+' คะแนน'
          :data.g==='battleship'?cells.filter(x=>x>=2).length+' โดนเป้า · '+score+' ลำจม'
          :score+' ครั้ง';
        $(key+'-action').textContent=pilotMove(seq.i[step-1],data.g,n);
        $(key+'-order').textContent='–';
        $(key+'-keys').textContent='–';
      }
    }
    range.value=String(number);
    const shown=isFight ? 'เฟรม '+number+' / '+max+' · '+formatTime(number)+' / '+formatTime(max) : 'ตา '+number+' / '+max;
    $('time').textContent=shown;
    range.setAttribute('aria-valuetext',shown);
    $('prev').disabled=number===0; $('next').disabled=number===max;
    $('result').textContent=number!==max?'':match.winner?'ผู้ชนะ: '+match.winner:'ผลเสมอ';
  }
  function render(force=false) {
    if(!data || !g || $('surface').hidden) return;
    const next=Math.min(max,Math.floor(clock+1e-7));
    if(next===number&&!force)return;
    number=next;
    canvasSize();
    g.setTransform(canvas.width/960,0,0,canvas.height/430,0,0);
    if(match.series==='fighting')fightCanvas();else puzzleCanvas();
    details();
  }
  function stop() {
    playing=false; last=0; cancelAnimationFrame(frameHandle);
    $('play').textContent='▶ เล่น';
    $('play').setAttribute('aria-pressed','false');
  }
  function seek(value) {clock=Math.max(0,Math.min(max,value));last=0;render(true);}
  function step(ms) {
    if(!playing || !data) return;
    if(last) {
      const rate = speeds.has(+speed.value)?+speed.value:1;
      clock=clockAdvance(clock,Math.min(80,ms-last),rate,match.series==='fighting'?60:8,max);
    }
    last=ms;render();
    if(clock>=max)stop();else frameHandle=requestAnimationFrame(step);
  }
  function toggle() {
    if(!data) return;
    if(playing){stop();return;}
    if(clock>=max)seek(0);
    playing=true;last=0;
    $('play').textContent='Ⅱ พัก';
    $('play').setAttribute('aria-pressed','true');
    frameHandle=requestAnimationFrame(step);
  }
  $('play').addEventListener('click',toggle);
  $('prev').addEventListener('click',()=>{stop();seek(number-1);});
  $('next').addEventListener('click',()=>{stop();seek(number+1);});
  $('restart').addEventListener('click',()=>{stop();seek(0);});
  range.addEventListener('input',()=>{stop();seek(+range.value);});
  speed.addEventListener('change',()=>{last=0;});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  if(typeof ResizeObserver==='function')new ResizeObserver(()=>render(true)).observe(canvas);
  else window.addEventListener('resize',()=>render(true));

  function clear() {
    ++revision; stop(); data=null; match=null; number=clock=max=0;
    shell.hidden=true; $('surface').hidden=true; $('type').textContent='';
  }
  async function show(m) {
    clear();
    const run=revision;
    shell.hidden=false;
    if(m.result==='forfeit') {status('แมตช์นี้ไม่มีรีเพลย์ เพราะเป็นผลแพ้ผ่าน ไม่ใช่ไฟต์ที่เล่นครบ');return;}
    status('กำลังโหลดรีเพลย์…');
    try {
      const files=await catalog();
      if(run!==revision)return;
      if(!Object.hasOwn(files,m.id)) {status('แมตช์นี้ไม่มีรีเพลย์ในคลังสาธารณะ');return;}
      const packed=await pack(files[m.id]);
      const value=await unpack(packed[m.id]);
      if(run!==revision)return;
      max=validate(m,value); data=value; match=m;
      const isFight=m.series==='fighting';
      $('type').textContent=isFight?'FIGHTINGICE 7.0 · NATIVE TRACE AT 60 FPS':'PILOT · RECORDED BOARD STATES';
      $('description').textContent=isFight
        ?'ภาพสนามและหุ่นวาดใหม่จากตำแหน่ง ท่าที่เกิดจริง และปุ่มที่เอนจินอ่าน ไม่ใช่ฟุตเทจหรือตัวเกม FightingICE ต้นฉบับ'
        :'ภาพกระดานวาดจากสถานะจริงหลังแต่ละตาของการทดสอบบอตรอบนำร่อง ความเร็วที่ 1× คือ 8 ตาต่อวินาทีเพื่อการรับชม ไม่ใช่เวลาที่บอตใช้แข่งจริง';
      $('caption-order').hidden=!isFight; $('meta-order').hidden=!isFight;
      range.max=String(max);
      status('',false);$('surface').hidden=false;
      seek(0);
    }catch(error){
      if(run!==revision)return;
      status(error?.message==='browser compression support'
        ?'เบราว์เซอร์นี้ยังอ่านรีเพลย์ไม่ได้ ลอง Chrome, Firefox หรือ Safari รุ่นล่าสุด ผลการแข่งขันยังอ่านได้ด้านล่าง'
        :'โหลดรีเพลย์ไม่สำเร็จ ลองเปิดแมตช์นี้ใหม่ ผลการแข่งขันยังอ่านได้ด้านล่าง');
    }
  }
  window.CupReplay=Object.freeze({show,clear});
})();
