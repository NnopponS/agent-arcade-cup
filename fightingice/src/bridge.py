"""Local Python adapter. Only logical simulation frames advance; no network/account."""
from __future__ import annotations
import json
from contextlib import contextmanager
from pathlib import Path
import subprocess
from typing import Iterator

ACTIONS = frozenset('NEUTRAL FORWARD_WALK DASH BACK_STEP STAND_GUARD CROUCH_GUARD FOR_JUMP STAND_A STAND_B CROUCH_A CROUCH_B STAND_FA STAND_FB THROW_A STAND_D_DF_FA STAND_F_D_DFB'.split())
HERE = Path(__file__).resolve().parent.parent

class Engine:
    def __init__(self, proc: subprocess.Popen[str]):
        self.proc = proc

    def request(self, text: str) -> dict:
        if '\n' in text or '\r' in text:
            raise ValueError('multi-line request')
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(text + '\n')
        self.proc.stdin.flush()
        out = self.proc.stdout.readline()
        if not out:
            raise RuntimeError(f'No engine response to {text!r}; exit status {self.proc.poll()}')
        try:
            state = json.loads(out)
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Invalid engine output {out!r}') from e
        if not state.get('ok'):
            raise ValueError(state.get('error', 'engine refused command'))
        return state

    def start(self, frames: int=420, hp: int=400, p1: str='ZEN', p2: str='ZEN') -> dict:
        if p1 not in ('ZEN','GARNET','LUD') or p2 not in ('ZEN','GARNET','LUD'):
            raise ValueError('unrecognized native fighter')
        return self.request(f'new {frames} {hp} {p1} {p2}')

    def observe(self) -> dict:
        return self.request('observe')

    def step(self, count: int, p1: str, p2: str) -> dict:
        if p1 not in ACTIONS or p2 not in ACTIONS:
            raise ValueError('unrecognized native action')
        return self.request(f'step {count} {p1} {p2}')

    def trace(self, file: Path) -> dict:
        return self.request(f'trace {file.resolve()}')

    def capture(self, directory: Path, stride: int=4) -> dict:
        return self.request(f'capture {directory.resolve()} {stride}')

@contextmanager
def bridge(stderr: Path|None=None) -> Iterator[Engine]:
    log = open(stderr or HERE/'build'/'bridge-session.stderr.log','a',encoding='utf-8')
    try:
        proc = subprocess.Popen([str(HERE/'run-bridge.sh')], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=log, text=True, bufsize=1)
        try:
            yield Engine(proc)
        finally:
            if proc.poll() is None:
                try:
                    assert proc.stdin is not None
                    proc.stdin.write('quit\n'); proc.stdin.flush(); proc.wait(timeout=10)
                except (BrokenPipeError,subprocess.TimeoutExpired):
                    if proc.poll() is None:
                        proc.kill(); proc.wait()
    finally:
        log.close()
