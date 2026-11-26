#!/usr/bin/env python3
"""Check the published benchmark observations and FightingICE replay envelopes."""
import base64
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

def check(ok, detail):
    if not ok:
        raise ValueError(detail)

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def verify(root):
    data = read(root / "cup100-data.json")
    matches = data["results"]
    check(len(data["roster"]) == 100, "Entrants")
    check(len({r["match"] for r in matches}) == len(matches) == data["planned"] == 99, "Match count")
    check(len(data["comparison"]) == 5, "Checkpoint count")
    for name, model in data["comparison"].items():
        rows = model["rows"]
        groups = Counter((r["case"], r["expected"]) for r in rows)
        check(len({r["case"] for r in rows}) == len(groups) == 14 and set(groups.values()) == {2}, name + ": pairing")
        check(sum(r["expected"] == r["choice"] for r in rows) == model["correct"], name + ": score")
        check(len(rows) == model["n"] == 28 and all(r["ms"] >= 0 for r in rows), name + ": rows")
    counts = Counter()
    for record in matches:
        mid = record["match"]
        check(record["replay"] == f"cup100-replay/{mid}.json", mid + ": path")
        replay = json.loads(gzip.decompress(base64.b64decode(read(root / record["replay"]), validate=True)))
        for key in ("match", "entrantIds", "models", "hp", "winner", "attempt"):
            check(replay[key] == record[key], f"{mid}: {key}")
        frames = replay["frames"]
        check(len(frames) >= 2 and all(a[0] < b[0] for a, b in zip(frames, frames[1:])), mid + ": frame order")
        hp = frames[-1][1:3]
        check(hp == record["hp"] and sum(x > 0 for x in hp) == 1, mid + ": terminal HP")
        check(record["entrantIds"][hp.index(max(hp))] == record["winner"], mid + ": KO")
        counts["cross" if len(set(record["models"])) == 2 else "mirror"] += 1
    check((counts["cross"], counts["mirror"]) == (71, 28) and data["report"]["byeTotal"] == 28, "Summary")
    check(next(r["winner"] for r in matches if r["match"] == "R7-01") == data["champion"], "Champion")
    print("Verified: 99 replay envelopes, 5 checkpoints, 140 decisions; champion " + data["champion"])

if __name__ == "__main__":
    verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "site/season2")
