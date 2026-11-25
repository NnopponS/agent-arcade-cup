#!/usr/bin/env bash
set -euo pipefail
bench="$(cd "$(dirname "$0")" && pwd)"
root="$bench/julia-trial-cache"
mkdir -p "$root"
port=18085
binary="$bench/local-gguf/llama-b11429/llama-server"
target="$root/Julia-1-Q8_0.gguf"
python - "$target" "$bench" <<'PY'
import importlib.util, pathlib, sys
target,bench=map(pathlib.Path,sys.argv[1:])
s=importlib.util.spec_from_file_location('download_model',bench/'hosted/benchmark.py'); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
name,quant,limit,ram,sha,rev=m.MODELS['julia-1-q8']
assert m.available_ram()>ram
m.download(f'https://huggingface.co/ggml-org/{name}-GGUF/resolve/{rev}/{target.name}',target,limit,sha)
PY
"$binary" -m "$target" --host 127.0.0.1 --port "$port" --ctx-size 1024 --parallel 2 --n-gpu-layers 0 --threads 3 --threads-batch 3 > "$root/server.log" 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT
for _ in {1..80}; do
 if curl -fsS --max-time 1 "http://127.0.0.1:$port/health" 2>/dev/null |grep -q '"ok"'; then break; fi
 kill -0 "$server"; sleep .3
done
python "$bench/live_trial.py" --ports "$port" "$port" --deadline-ms 300 --frames "${TRIAL_FRAMES:-1800}" --out "${TRIAL_OUTPUT:-$bench/julia-live-affordance.json}" --affordance
