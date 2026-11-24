"""Original motion-graphics rendering of actual FightingICE state, not its native artwork."""
import argparse,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=argparse.ArgumentParser()
P.add_argument('trace',type=Path);P.add_argument('output',type=Path)
P.add_argument('--label',default='FIXED-INPUT DEVELOPMENT DEMO')
P.add_argument('--p1',default='PLAYER 1');P.add_argument('--p2',default='PLAYER 2')
P.add_argument('--hp',type=int,default=400);P.add_argument('--fps',type=int,default=30)
P.add_argument('--phase-break',type=int,default=232)
a=P.parse_args()
frames=[json.loads(l)for l in a.trace.read_text().splitlines() if l.strip()]
if not frames or any(y['frame']!=x['frame']+1 for x,y in zip(frames,frames[1:])):raise SystemExit('missing or non-consecutive engine frames')
W,H=1280,720
bg=Image.new('RGB',(W,H));bd=ImageDraw.Draw(bg)
for y in range(H):
    t=y/H;bd.line((0,y,W,y),fill=(int(8+10*t),int(12+12*t),int(26+22*t)))
for x in range(93,1200,75):bd.line((640+(x-640)*.52,315,x,619),fill='#222947',width=1)
for y in [337,364,397,439,491,552,619]:bd.line((92,y,1188,y),fill='#222947',width=1)
bd.line((82,591,1198,591),fill='#657497',width=2)
fonts={}
def font(size,bold=True):
    pair=(size,bold)
    if pair not in fonts:fonts[pair]=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size)
    return fonts[pair]
def text(d,xy,s,size=24,fill='#e8ecfb',anchor='la',bold=True):
    d.text(xy,str(s),fill=fill,font=font(size,bold),anchor=anchor)
def mix(a,b,t):
    aa=tuple(int(a[i:i+2],16) for i in (1,3,5)); bb=tuple(int(b[i:i+2],16) for i in (1,3,5))
    return tuple(round(x*(1-t)+y*t) for x,y in zip(aa,bb))
def fighter(d,s,col,f):
    x=94+1092*s['x']/960; floor=580
    z=2.8 if s['state']=='CROUCH' else 0
    h=floor-(537-s['y'])*.9+z
    side=1 if s['isFront'] else -1
    act=s['action'];down='DOWN' in s['state'] or s['hp']<=0
    guard='GUARD' in act; attack=act.endswith(('_A','_B','FA','FB')) or act.startswith('THROW')
    walk=act in ('FORWARD_WALK','DASH','BACK_STEP')
    step=math.sin(f*.38+x*.04)*16 if walk else 0
    neon=col; shell=mix(col,'#ffffff',.77); muted=mix(col,'#0e1426',.69)
    outline=mix(col,'#162437',.52); face='#10182d'
    if down:
        d.rounded_rectangle((x-51,h-24,x+47,h+2),radius=11,fill=muted,outline=neon,width=2)
        return x,h
    d.ellipse((x-55,h-7,x+55,h+11),fill='#0a0f22')
    hip=(x-side*4,h-53)
    shoulders=(x,h-84);face_y=h-121+(8 if guard else 0)
    # Wheels and joint stops are original position cues, not a native sprite.
    for shoulder,knee,foot in [
      (hip,(x-16+step*.45,h-23),(x-22+step,h-5)),
      (hip,(x+16-step*.45,h-22),(x+24-step,h-5))]:
      d.line((shoulder,knee,foot),fill=muted,width=17)
      d.ellipse((knee[0]-8,knee[1]-8,knee[0]+8,knee[1]+8),fill=outline,outline=col,width=2)
      d.rounded_rectangle((foot[0]-14,foot[1]-7,foot[0]+17,foot[1]+6),6,fill=shell,outline=outline,width=2)
    d.rounded_rectangle((x-24,h-96,x+25,h-50),13,fill=shell,outline=outline,width=3)
    d.rounded_rectangle((x-12,h-83,x+12,h-61),6,fill=face)
    d.line((x-6,h-72,x+6,h-72),fill=neon,width=3)
    back=[(x-side*19,h-84),(x-side*33,h-69),(x-side*28,h-55)]
    if attack:
        end=48+min(16,max(0,s['remainingActionFrames']))
        fore=[(x+side*20,h-81),(x+side*36,h-77),(x+side*end,h-89)]
        d.arc((x-86,h-145,x+86,h-46),206 if side<0 else 264,315 if side<0 else 385,fill=neon,width=4)
    elif guard:fore=[(x+side*19,h-82),(x+side*37,h-68),(x+side*26,h-100)]
    else:fore=[(x+side*18,h-83),(x+side*32,h-63),(x+side*39,h-61)]
    for arm in (back,fore):
        d.line(arm,fill=muted,width=23)
        d.line(arm,fill=shell,width=13)
        px,py=arm[-1]; d.rounded_rectangle((px-10,py-9,px+10,py+9),7,fill=col,outline=outline,width=3)
    d.line((x-side*9,face_y-20,x-side*12,face_y-34),fill=shell,width=3)
    d.ellipse((x-side*12-4,face_y-38,x-side*12+4,face_y-30),fill=neon)
    d.rounded_rectangle((x-31,face_y-22,x+32,face_y+20),13,fill=shell,outline=outline,width=3)
    d.rounded_rectangle((x-25+side*2,face_y-15,x+26+side*2,face_y+11),9,fill=face)
    for i in [-1,1]:
      dx=i*10+side*3
      d.rounded_rectangle((x+dx-3,face_y-7,x+dx+3,face_y+4),2,fill=neon)
    return x,h-110
names=[a.p1,a.p2];col=['#68e9e0','#f6a35f'];hp_prev=[frames[0]['p1']['hp'],frames[0]['p2']['hp']];hit=[None,None]
a.output.parent.mkdir(parents=True,exist_ok=True)
enc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(a.fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)],stdin=subprocess.PIPE)
assert enc.stdin is not None
index=0
max_frame=frames[-1]['frame']
for sample in range(math.ceil(len(frames)*a.fps/60)+a.fps):
    due=min(max_frame,frames[0]['frame']+round(sample*60/a.fps))
    while index<len(frames)-1 and frames[index]['frame']<due:
        index+=1
        for side,k in enumerate(('p1','p2')):
            v=frames[index][k]['hp']
            if v<hp_prev[side]: hit[side]=(frames[index]['frame'],hp_prev[side]-v)
            hp_prev[side]=v
    r=frames[index];f=r['frame']; canvas=bg.copy();d=ImageDraw.Draw(canvas)
    text(d,(62,38),'FIGHTINGICE   //   DATA REPLAY',26)
    text(d,(1216,43),a.label,18,'#acbddf','ra')
    for i,k in enumerate(('p1','p2')):
        st=r[k];x=62 if i==0 else 755
        text(d,(x,105),names[i],24,col[i]); text(d,(x+462,106),str(st['hp'])+' HP',25,'#f4f6ff','ra')
        d.rounded_rectangle((x,143,x+462,164),radius=9,fill='#292f4e')
        val=round(462*max(0,min(1,st['hp']/a.hp)))
        if val:d.rounded_rectangle((x,143,x+val,164),radius=9,fill=col[i])
        text(d,(x,182),st['action'].replace('_',' '),18,'#c5cce3',bold=False)
        text(d,(x+460,182),f'ENERGY {st["energy"]}',17,'#9da6ce','ra',False)
    phase='WARM-UP' if f<44 else 'PHASE 1' if f<a.phase_break else 'PHASE 2'
    text(d,(640,134),f'{f:03d}',44,'#f6f7ff','mm')
    text(d,(640,176),phase,15,'#a8bee8','mm')
    for side,k in enumerate(('p1','p2')):
        x,y=fighter(d,r[k],col[side],f)
        if hit[side] and f-hit[side][0]<21:
            dy=(f-hit[side][0])*1.8
            text(d,(x,y-108-dy),'−'+str(hit[side][1]),33,'#ffda86','mm')
    if due==max_frame:
        hp=[r[k]['hp']for k in ('p1','p2')]
        verdict='TIED ON HP' if hp[0]==hp[1] else names[int(hp[1]>hp[0])]+(' WINS · KO' if min(hp)<=0 else ' WINS · TIME')
        d.rounded_rectangle((346,224,934,296),radius=18,fill='#182641',outline='#7a89a9',width=2)
        text(d,(640,260),verdict,31,'#f4f5ff','mm')
    d.rounded_rectangle((62,641,1217,686),radius=12,fill='#1d2741')
    text(d,(81,655),'ENGINE STATE REPLAY · ORIGINAL VISUALS',18,'#d0d8f3')
    text(d,(1196,655),r['nativeFrameSha256'][:10].upper()+' / FRAME CHECK',17,'#9db5d9','ra',False)
    enc.stdin.write(canvas.tobytes())
enc.stdin.close()
if enc.wait()!=0:raise SystemExit('ffmpeg encode failed')
