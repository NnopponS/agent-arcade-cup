"""Eight real Kev-4B Q4 decisions with the same task, explicitly a feasibility subset."""
import importlib.util,json,subprocess,time,urllib.request
from pathlib import Path
p=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runner',p/'hosted'/'benchmark.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
name,quant,limit,ram,sha,rev=m.MODELS['kev-4b-q4']
w=p/'verified-cache'/f'{name}-{quant}.gguf'
assert w.stat().st_size==limit and m.available_ram()>ram
with w.open('rb') as f:assert m.hashlib.file_digest(f,'sha256').hexdigest()==sha
out=p/'kev4-feasibility.json'
port=18086
with (p/'verified-cache'/'kev4-feasibility.stderr.log').open('w') as log:
    s=subprocess.Popen([str(p/'local-gguf'/'llama-b11429'/'llama-server'),'-m',str(w),'--host','127.0.0.1',
        '--port',str(port),'--parallel','1','--ctx-size','1024','--n-gpu-layers','0',
        '--threads','2','--threads-batch','2'],stdout=log,stderr=log)
    try:
        for _ in range(150):
            if s.poll() is not None:raise RuntimeError('server exited')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as raw:
                    if json.load(raw).get('status')=='ok': break
            except OSError:pass
            time.sleep(.4)
        else:raise RuntimeError('failed readiness')
        cases=[r for r in m.ortho_cases() if r[0] in {'far-west','close-block-a','incoming-a','punish-a'} and r[1]=='brief']
        assert len(cases)==8
        m.evaluate(port,cases[0]);rows=[]
        for case in cases:
            rows.append(m.evaluate(port,case))
            d={'model':'Kev-4B','quantization':'Q4_K_M','weights_sha256':sha,'runtime':'llama.cpp b11429','threads':2,
               'scope':'4 shared scenarios with 2 option orders and brief prompt only','rows':rows}
            if len(rows)==8:
                d['summary']={'n':len(rows),'p95_ms':m.precap([r['ms'] for r in rows],.95),
                   'reference_match':sum(r['choice']==r['reference'] for r in rows),'under_100_ms':sum(r['ms']<=100 for r in rows)}
            out.write_text(json.dumps(d,separators=(',',':')))
        print(d['summary'],flush=True)
    finally:m.stop(s)
