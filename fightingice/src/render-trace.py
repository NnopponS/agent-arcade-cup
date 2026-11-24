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
def fighter(d,s,col,f):
    x=94+1092*s['x']/960; floor=580
    baseline=floor-(537-s['y'])*.9
    turn=1 if s['isFront'] else -1
    isdown='DOWN' in s['state'] or s['hp']<=0
    isguard='GUARD' in s['action']; isattack=s['action'].endswith(('_A','_B','FA','FB')) or s['action'].startswith('THROW')
    iswalk=s['action'] in ('FORWARD_WALK','DASH','BACK_STEP')
    low=23 if s['state']=='CROUCH' else 0
    progress=(math.sin(f*.47+ x*.1) if iswalk else 0)
    head_y=baseline-112+low
    chest=(x,head_y+32); pelvis=(x-turn*7,head_y+70)
    if isdown:
        d.rounded_rectangle((x-36,baseline-19,x+38,baseline),radius=9,fill=col);return x,baseline
    d.ellipse((x-32,baseline-6,x+32,baseline+8),fill='#171831')
    d.line([chest,pelvis],fill=col,width=15)
    d.ellipse((x-16,head_y-6,x+16,head_y+26),fill=col,outline='#f2f4ff',width=2)
    d.line([pelvis,(x-22+progress*16,baseline-22),(x-31+progress*23,baseline)],fill=col,width=9)
    d.line([pelvis,(x+14-progress*16,baseline-23),(x+22-progress*23,baseline)],fill=col,width=9)
    if isattack:
        d.line([chest,(x+turn*25,head_y+43),(x+turn*(49+ min(14,s['remainingActionFrames'])),head_y+38)],fill=col,width=9)
        d.arc((x-65,head_y+2,x+65,head_y+87),210 if turn<0 else 260,300 if turn<0 else 390,fill='#e5e7ff',width=3)
    elif isguard:
        d.line([chest,(x+turn*25,head_y+40),(x+turn*34,head_y+20)],fill=col,width=9)
        d.arc((x-52,head_y-2,x+52,head_y+86),115 if turn<0 else 293,240 if turn<0 else 425,fill=col,width=3)
    else:d.line([chest,(x+turn*24,head_y+39),(x+turn*39,head_y+54)],fill=col,width=9)
    d.line([chest,(x-turn*17,head_y+43),(x-turn*25,head_y+58)],fill=col,width=8)
    return x,head_y+48
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
    text(d,(62,38),'FIGHTINGICE / ENGINE TELEMETRY',26)
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
    text(d,(81,655),'ORIGINAL VECTOR REPLAY FROM RECORDED ENGINE STATE',18,'#d0d8f3')
    text(d,(1196,655),r['nativeFrameSha256'][:10].upper()+' / FRAME CHECK',17,'#9db5d9','ra',False)
    enc.stdin.write(canvas.tobytes())
enc.stdin.close()
if enc.wait()!=0:raise SystemExit('ffmpeg encode failed')
