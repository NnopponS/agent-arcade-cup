#!/usr/bin/env python3
"""Allowlisted SystemOne inference benchmark, one model at a time. Python stdlib only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import time
import urllib.error
import urllib.request

GIB = 1 << 30
BUILD = "b11429"
ARCHIVE = f"llama-{BUILD}-bin-ubuntu-x64.tar.gz"
BIN_URL = f"https://github.com/ggml-org/llama.cpp/releases/download/{BUILD}/{ARCHIVE}"
BIN_SHA = "f6d25dde8f51133143d1453da4fd5f73b145127177612a283bf7995957af3392"
# Model files are addressed by immutable repository revision and SHA-256.
MODELS = {
    "julia-1-q8": (
        "Julia-1", "Q8_0", 168_166_400, 2 * GIB,
        "ff6cbbe856f1810a8b171528ea908d3b43b5742e73f0698689467559078f347d",
        "28ada03933a77bd332c197dc86fc2cb24e43b8f9",
    ),
    "laya-q8": (
        "Laya", "Q8_0", 449_397_728, 2 * GIB,
        "ac6a51fd7a7907bc9dd61e85f7e6b989f57a635e2232a8f0345f5c51ca6cb3ea",
        "f9a697b4e5a39d085bded9576a592e6850d139e7",
    ),
    "kev-0.8b-q8": (
        "Kev-0.8B", "Q8_0", 812_406_304, 3 * GIB,
        "27278f34eb3273bceea4c053dc50dd61a5161da21a718c4aacdf8fd5830771d0",
        "9231cb757e3320120077e42e52371971968f008d",
    ),
    "kev-4b-q4": (
        "Kev-4B", "Q4_K_M", 3_033_489_824, 5 * GIB,
        "33ae6b18926502b2209a1bf7d3b61a350d65938441515c686bb87d226a19eff9",
        "f4624b6bb7072f1bab726a622c1cad3f96030b9e",
    ),
}
CORPUS = Path(__file__).resolve().parents[1] / "scenarios.json"
PROMPTS = {
    "brief": "Choose the best game move now.",
    "coach": ("Pick the first applicable tactic: close the gap when out of range; "
              "block an imminent hit; throw a guarding enemy within grab range; "
              "strike exposed recovery within strike range."),
}


def download(url, path, limit, sha):
    if path.is_file() and path.stat().st_size <= limit:
        with path.open("rb") as existing:
            if hashlib.file_digest(existing, "sha256").hexdigest() == sha:
                return
    partial = path.with_suffix(path.suffix + ".part")
    try:
        subprocess.run(["curl", "--fail", "--silent", "--show-error", "--location",
                        "--proto", "=https", "--proto-redir", "=https",
                        "--connect-timeout", "20", "--max-time", "400", "--retry", "1",
                        "--max-filesize", str(limit), "--output", str(partial), url],
                       check=True, timeout=440)
        if partial.stat().st_size > limit:
            raise RuntimeError("Asset larger than its allowlisted maximum")
        with partial.open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != sha:
                raise RuntimeError("Asset SHA-256 mismatch")
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)


def ortho_cases():
    corpus = json.loads(CORPUS.read_text())
    rng = random.Random(865418)
    for name, state, reference in corpus["cases"] + corpus["counterfactuals"]:
        ordered = list(corpus["options"])
        rng.shuffle(ordered)
        for family, instructions in PROMPTS.items():
            for index, options in enumerate((ordered, list(reversed(ordered)))):
                yield (name, family, index, reference, {
                    "state": state,
                    "questions": {"move": {
                        "type": "choice",
                        "instructions": instructions,
                        "criteria": {action: corpus["options"][action] for action in options},
                    }},
                })


def evaluate(port, case):
    name, family, order, reference, message = case
    url = f"http://127.0.0.1:{port}/v1/systemone"
    req = urllib.request.Request(url, json.dumps(message).encode(),
                                 {"Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read()
    elapsed = (time.perf_counter() - start) * 1000
    answer = json.loads(body)["answers"]["move"]
    legal = message["questions"]["move"]["criteria"]
    probs = answer["probabilities"]
    if (
        answer["choice"] not in legal or set(probs) != set(legal)
        or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probs.values())
        or not math.isclose(sum(probs.values()), 1.0, abs_tol=0.001)
    ):
        raise ValueError("Invalid model output")
    return {"scenario": name, "family": family, "order": order, "reference": reference,
            "candidate_order": list(legal),
            "choice": answer["choice"], "probabilities": probs, "ms": elapsed}


def sweep(rows):
    """Resample cached distributions; this does not perform more inference or play matches."""
    out = []
    for family in PROMPTS:
        cases = [row for row in rows if row["family"] == family]
        for temp, min_margin in ((0, 0), (.35, 0), (.7, 0), (1.0, 0), (0, .1), (0, .2)):
            for seed in (865418, 865419, 865420) if temp else (865418,):
                rng = random.Random(seed)
                covered = correct = 0
                for row in cases:
                    p = row["probabilities"]
                    actions = sorted(row["candidate_order"], key=lambda k: -p[k])
                    if p[actions[0]] - p[actions[1]] < min_margin:
                        continue
                    picked = actions[0] if not temp else rng.choices(
                        actions, weights=[p[a] ** (1/temp) for a in actions])[0]
                    covered += 1
                    correct += int(picked == row["reference"])
                out.append({"family": family, "relative_temperature": temp, "min_margin": min_margin,
                            "seed": seed, "covered": covered, "correct": correct, "n": len(cases)})
    return out


def available_ram():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            host = int(line.split()[1]) * 1024
            break
    else:
        raise RuntimeError("Can't measure headroom")
    try:
        cgroup = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        if cgroup != "max":
            host = min(host, int(cgroup) - int(Path("/sys/fs/cgroup/memory.current").read_text()))
    except FileNotFoundError:
        pass
    return host


def precap(ms, p):
    return round(sorted(ms)[max(0, math.ceil(len(ms) * p) - 1)], 3)


def stop(server):
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


def benchmark(binary, key, workdir, report, threads):
    name, quant, limit, minimum_ram, sha, revision = MODELS[key]
    model_file = workdir / f"{name}-{quant}.gguf"
    report.update(weight_sha256=sha, weight_revision=revision, quantization=quant,
                  memory_available=available_ram())
    if report["memory_available"] < minimum_ram:
        report.update(status="skipped", reason="insufficient available RAM")
        return
    if shutil.disk_usage(workdir).free < limit + GIB:
        report.update(status="skipped", reason="insufficient available disk")
        return
    url = f"https://huggingface.co/ggml-org/{name}-GGUF/resolve/{revision}/{model_file.name}"
    port = 18084
    server = None
    log_path = workdir / "server.log"
    log_path.unlink(missing_ok=True)
    try:
        begun = time.perf_counter()
        download(url, model_file, limit, sha)
        report.update(download_seconds=round(time.perf_counter() - begun, 3),
                      weight_bytes=model_file.stat().st_size)
        with log_path.open("w") as log:
            started = time.perf_counter()
            server = subprocess.Popen(
                [str(binary), "-m", str(model_file), "--host", "127.0.0.1",
                 "--port", str(port), "--ctx-size", "1024", "--parallel", "1",
                 "--n-gpu-layers", "0", "--threads", str(threads), "--threads-batch", str(threads)],
                stdout=log, stderr=log,
            )
            for _ in range(120):
                if server.poll() is not None:
                    raise RuntimeError(f"Server exited: {server.returncode}")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as raw:
                        if json.load(raw).get("status") == "ok":
                            break
                except OSError:
                    pass
                time.sleep(.5)
            else:
                raise RuntimeError("Server readiness timed out")
            report["startup_seconds"] = round(time.perf_counter() - started, 3)
            cases = list(ortho_cases())
            report["first_inference"] = evaluate(port, cases[0])
            report["measurements"] = []
            # Same chronology as the local reference. The two option orders are not
            # independent fixtures, so reference match is descriptive, not a CI.
            for case in cases:
                report["measurements"].append(evaluate(port, case))
            report["summary"] = {}
            for family in PROMPTS:
                rows = [r for r in report["measurements"] if r["family"] == family]
                ms = [row["ms"] for row in rows]
                report["summary"][family] = {
                    "n": len(ms), "p50_ms": round(statistics.median(ms), 3),
                    "p95_ms": precap(ms, .95),
                    "under_100_ms": sum(x <= 100 for x in ms),
                    "under_200_ms": sum(x <= 200 for x in ms),
                    "under_500_ms": sum(x <= 500 for x in ms),
                    "reference_match": sum(row["choice"] == row["reference"] for row in rows),
                    "order_stable_of_14": sum(rows[i]["choice"] == rows[i+1]["choice"]
                                              for i in range(0, len(rows), 2)),
                    "counterfactual_correct_of_2": sum(row["choice"] == row["reference"]
                                                       for row in rows
                                                       if row["scenario"].startswith("paired-")
                                                       and row["order"] == 0),
                }
            report["policy_sweep"] = sweep(report["measurements"])
            report["status"] = "measured"
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        report.update(status="error", reason=str(exc))
        if log_path.exists():
            report["log_tail"] = log_path.read_text(errors="replace").replace(str(workdir), "<workdir>").splitlines()[-10:]
    finally:
        if server:
            stop(server)
        model_file.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workdir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--model", action="append", choices=MODELS)
    args = p.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    work = args.workdir.resolve()
    threads = min(2, os.cpu_count() or 1)
    report = {"build": BUILD, "machine": platform.platform(), "logical_cpus": os.cpu_count(),
              "threads": threads, "models": {}, "scenarios": 14,
              "workload_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest()}
    cpufile = Path("/proc/cpuinfo")
    if cpufile.exists():
        report["cpu"] = next((s.partition(":")[2].strip() for s in cpufile.read_text().splitlines()
                              if s.startswith("model name")), None)
    def save():
        temp = args.output.with_suffix(".tmp")
        temp.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        temp.replace(args.output)
    save()
    try:
        download(BIN_URL, work / ARCHIVE, 100_000_000, BIN_SHA)
        subprocess.run(["tar", "-xzf", str(work / ARCHIVE), "-C", str(work)], check=True)
        binary = next(work.rglob("llama-server"))
        for key in args.model or MODELS:
            result = report["models"][key] = {}
            benchmark(binary, key, work, result, threads)
            save()
    except (OSError, RuntimeError, subprocess.SubprocessError, StopIteration) as exc:
        report["bootstrap_error"] = str(exc)
        save()
    statuses = [row.get("status") for row in report["models"].values()]
    return int(
        "bootstrap_error" in report or "measured" not in statuses
        or any(status not in {"measured", "skipped"} for status in statuses)
    )


if __name__ == "__main__":
    raise SystemExit(main())
