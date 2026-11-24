#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
runtime="${FIGHTINGICE_RUNTIME:-$here/DareFightingICE-7.0}"
[[ -f "$runtime/FightingICE.jar" && -f "$runtime/data/characters/ZEN/Motion.csv" ]] || { echo "Install the official FightingICE v7.0 archives first" >&2; exit 2; }
cd "$runtime"
cp="$(find "$runtime/lib" -type f -name '*.jar' | sort | paste -sd:)"
export ALSOFT_DRIVERS="${ALSOFT_DRIVERS:-null}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$here/build/cache}"
mkdir -p "$XDG_CACHE_HOME"
exec java -Djava.awt.headless=true -cp "$runtime/FightingICE.jar:$cp" "$here/src/CupBridge.java"
