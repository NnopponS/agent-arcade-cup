#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 1 ]]; then
  echo "Usage: bash site/season2/stage-pages.sh OUTPUT_DIR" >&2
  exit 2
fi

out=$1
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
season="$root/site/season2"
mkdir -p -- "$out"
if [[ -n $(find "$out" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
  echo "Output directory must be empty: $out" >&2
  exit 2
fi

touch "$out/.nojekyll"
cp "$season/decision-lab-expanded.html" "$out/index.html"
cp "$season/home.css" "$out/"
cp "$root/kev-bench/scenarios.json" "$out/"
cp "$season/"{benchmark,systemone-results,live-trial,kev4-feasibility}.json "$out/"
cp "$season/head-to-head"{.html,-data.json} "$out/"
cp "$season/fair"{.html,-data.json} "$out/"
cp "$season/cup100"{.html,.css,.js,-data.json} "$out/"
cp -R "$season/cup100-replay" "$out/"

python3 "$season/verify-expanded.py" "$out"
python3 "$root/research/verify_public.py" "$out"
python3 - "$out" <<'PY'
import json
from pathlib import Path
import sys

site = Path(sys.argv[1])

def read(name):
    return json.loads((site / name).read_text(encoding="utf-8"))

models = read("benchmark.json")["models"]
assert len(models) == 2 and all(len(m["rows"]) == 56 for m in models.values())
matches = read("fair-data.json")["matches"]
lockstep = [m for m in matches if m["protocol"] == "lockstep"]
assert len(matches) == 4 and len(lockstep) == 2
assert all(m["stats"][0]["accepted"] == m["stats"][1]["accepted"] for m in lockstep)
matches = read("head-to-head-data.json")["matches"]
assert len(matches) == 4 and all(len(set(m["seats"])) == 2 and m["frames"] for m in matches)
assert any(m["nativeKO"] for m in matches)
PY
