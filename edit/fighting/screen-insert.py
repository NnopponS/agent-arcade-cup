"""Map an authentic telemetry replay into our original tracked 3D arena screen.

Input corners per source frame are [TL, TR, BR, BL], in output pixel coordinates.
The tool writes an editable silent 1080×1920 plate for the shot assembly. No
third-party game sprites, logos or audio are needed.
"""
import argparse,json,subprocess as sp
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('plate',type=Path);p.add_argument('insert',type=Path);p.add_argument('corners',type=Path);p.add_argument('output',type=Path)
p.add_argument('--fps',type=int,default=24);p.add_argument('--width',type=int,default=1080);p.add_argument('--height',type=int,default=1920)
a=p.parse_args(); W,H,FPS=a.width,a.height,a.fps; vw,vh=960,540
raw=json.loads(a.corners.read_text())
origin=(raw.get('resolution') or raw.get('delivery_size')) if isinstance(raw,dict) else None
corner_fps=(raw.get('source_fps') or FPS) if isinstance(raw,dict) else FPS
coords=raw.get('frames',raw.get('corners')) if isinstance(raw,dict) else raw
if isinstance(coords,dict):coords=[coords[k] for k in sorted(coords,key=int)]
if not isinstance(coords,list) or not coords:raise SystemExit('Projection table missing frames')
def dec(path,w,h):
 return sp.Popen(['ffmpeg','-v','error','-nostdin','-threads','2','-filter_threads','1','-i',str(path),'-vf',f'fps={FPS},scale={w}:{h}','-f','rawvideo','-pix_fmt','rgb24','-threads:v','1','-'],stdout=sp.PIPE)
def read(z,w,h):
 if z is None:return None
 q=z.stdout.read(w*h*3)
 return Image.frombytes('RGB',(w,h),q) if len(q)==w*h*3 else None
def quad(f):
 f=f.get('corners',f.get('quad')) if isinstance(f,dict) else f
 if not isinstance(f,list) or len(f)!=4:raise ValueError('each frame needs four corners')
 g=[tuple(p) for p in f]
 if origin and max(abs(x) for p in g for x in p)>2:
  g=[(x*W/origin[0],y*H/origin[1]) for x,y in g]
 elif max(abs(x) for p in g for x in p)<2:
  g=[(x*W,y*H) for x,y in g]
 return g
def coeff(dst):
 M=[];b=[]
 for (x,y),(u,v) in zip(dst,[(0,0),(vw,0),(vw,vh),(0,vh)]):
  M.extend(((x,y,1,0,0,0,-u*x,-u*y),(0,0,0,x,y,1,-v*x,-v*y)));b.extend((u,v))
 return np.linalg.solve(np.array(M),np.array(b)).tolist()
a.output.parent.mkdir(parents=True,exist_ok=True)
plate=dec(a.plate,W,H); src=dec(a.insert,vw,vh)
enc=sp.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s',f'{W}x{H}','-r',str(FPS),'-pix_fmt','rgb24','-i','-','-c:v','libx264','-threads','3','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)],stdin=sp.PIPE)
last=None; count=0
try:
 while (background:=read(plate,W,H)) is not None:
  frame=read(src,vw,vh)
  last=frame if frame else last
  if last is None:raise ValueError('insert has no frame')
  phase=min(len(coords)-1,count*corner_fps/FPS); lower=int(phase); upper=min(len(coords)-1,lower+1); weight=phase-lower
  f=[((1-weight)*x+weight*z,(1-weight)*y+weight*w) for (x,y),(z,w) in zip(quad(coords[lower]),quad(coords[upper]))]
  stencil=Image.new('L',(W,H));st=ImageDraw.Draw(stencil);st.polygon(f,fill=255)
  warp=last.transform((W,H),Image.Transform.PERSPECTIVE,coeff(f),Image.Resampling.BICUBIC)
  background.paste(warp,(0,0),stencil.filter(ImageFilter.GaussianBlur(.6)))
  outline=ImageDraw.Draw(background,'RGB')
  outline.line([*f,f[0]],fill='#8cc8ec',width=max(1,round(W*.0018)))
  enc.stdin.write(background.tobytes());count+=1
finally:
 for q in (plate,src):
  if q.stdout:q.stdout.close()
  if q.poll() is None:q.terminate()
 enc.stdin.close()
if enc.wait() or count==0:raise SystemExit('Plate encode failed')
print(json.dumps({"frames":count,"duration":round(count/FPS,3),"output":str(a.output)}))
