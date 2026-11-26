# Agent Arcade Cup: data and reproduction

[140 benchmark observations](benchmark-trials.csv) and [99 played bouts](bout-results.csv) are CSV exports of the [canonical snapshot](../site/season2/cup100-data.json), not new trials.

## Tactical benchmark

Fourteen scripted states appeared in two option orders with one prompt. Each checkpoint saw 28 trials. The CSV has one row per checkpoint, case and recorded order; rubric_agreement is 1 when the returned move matches the expected move. latency_ms is measured CPU reply time for this setup. Precision, runtime and decoder differ. Analyze paired menus by scenario_id; do not treat the 28 trials as 28 independent scenarios.

## Tournament and replays

100 entrants, 20 configurations per checkpoint. Both controllers observe the same engine frame and choose before the engine advances. No round timer determines a winner. A double knockout does not advance either fighter. The 28 first-round byes are excluded from wins. The bracket is not a balanced round robin.

The replay_path is relative to site/season2/. Replay files contain a JSON string with base64-encoded gzip data. Each decoded frame is [frame, hp1, hp2, x1, x2, action1, action2]. Seat order follows the engine. Negative terminal HP is retained; the viewer displays zero instead. Playback uses illustrated poses and does not include the original sprites, music or footage.

## Validate and reproduce

Run **python research/verify_public.py** from the repository root using Python 3.10 or later. The verifier checks all 99 replay envelopes, seat/result consistency, terminal KO and benchmark scoring. It does not rerun model outputs or the native game engine.

For a new run, see the [runner and benchmark source](../kev-bench/), [FightingICE setup](../fightingice/README.md), and [model source pins](../kev-bench/cup100_sources.json). Obtain models and the engine from their original distributors and review their separate terms; weights and the upstream game distribution are not bundled here.
