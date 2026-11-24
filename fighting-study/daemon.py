#!/usr/bin/env python3
"""One persistent native FightingICE JVM; immutable file-based request/result bridge."""
from pathlib import Path
import argparse
import json
import re
import selectors
import subprocess
import time

p=argparse.ArgumentParser()
p.add_argument("directory", type=Path)
p.add_argument("--bridge", type=Path, default=Path(__file__).resolve().parent.parent/"fightingice/run-bridge.sh")
a=p.parse_args()
d=a.directory.resolve()
d.mkdir(mode=0o700,parents=True,exist_ok=True)
allowed=re.compile(r"(?:new 420 400 ZEN ZEN|step (?:44|47) [A-Z_]+ [A-Z_]+|observe)")
if (d/"ready.json").exists():
    raise SystemExit("Refusing to reuse an existing daemon session directory")
def safe_write(path, record):
    tmp=path.with_suffix(".pending")
    tmp.write_text(json.dumps(record), encoding="utf-8")
    tmp.replace(path)
with (d/"engine.stderr.log").open("wb") as log, subprocess.Popen([str(a.bridge.resolve())], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1) as proc:
    selector=selectors.DefaultSelector()
    selector.register(proc.stdout,selectors.EVENT_READ)
    safe_write(d/"ready.json",{"daemon":"fightingice-persistent","startedNs":time.time_ns()})
    done=False
    while proc.poll() is None and not done:
        requests=sorted(d.glob("req.*.json"))
        progressed=False
        for req in requests:
            ticket=req.name.split(".")[1]
            assert re.fullmatch(r"[0-9a-f]{24}",ticket)
            target=d/f"res.{ticket}.json"
            if target.exists():continue
            progressed=True
            try:
                commands=json.loads(req.read_text(encoding="utf-8"))["commands"]
                if commands==["quit"]:
                    done=True
                    safe_write(target,{"terminal":True})
                    break
                if not (isinstance(commands,list) and 1<=len(commands)<=15 and all(isinstance(x,str) and allowed.fullmatch(x) for x in commands)):
                    raise ValueError("unsupported command envelope")
                receipt=[]
                for cmd in commands:
                    proc.stdin.write(cmd+"\n")
                    proc.stdin.flush()
                    if not selector.select(30):raise TimeoutError("native command timed out")
                    response=json.loads(proc.stdout.readline())
                    if not response.get("ok"):raise RuntimeError(f"native rejected a validated command: {response}")
                    receipt.append(response)
                safe_write(target,{"states":receipt})
            except Exception as error:
                safe_write(target,{"error":str(error)})
                # Native state after errors is conservatively considered unknown.
                done=True
                break
        if not progressed:time.sleep(.04)
    if proc.poll() is None:
        try:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=3)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            proc.kill()
    safe_write(d/"stopped.json",{"endedNs":time.time_ns(),"nativeExit":proc.poll()})
