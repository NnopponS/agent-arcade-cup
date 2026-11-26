# Agent Arcade Cup: FightingICE benchmark for local language models

Five local language-model checkpoints compete in an untimed **100-agent FightingICE tournament**. A separate paired benchmark measures tactical decision agreement and CPU latency.

**[Project site](https://nnoppons.github.io/agent-arcade-cup/)** · **[99 replays and bracket](https://nnoppons.github.io/agent-arcade-cup/cup100.html#bracket)** · **[Per-model results](https://nnoppons.github.io/agent-arcade-cup/cup100.html#model-notes)**

| Checkpoint | Cross-model W–L | Tactical agreement |
| --- | ---: | ---: |
| Julia-1 Q8 | 12–17 | 9/28 |
| Kev 0.8B BF16 | 8–18 | 18/28 |
| Laya Q8 | 36–4 | 15/28 |
| Qwen2.5 0.5B Instruct Q4 | 9–16 | 12/28 |
| SmolLM2 135M Instruct Q4 | 6–16 | 7/28 |

**[LAYA-09 won the final](https://nnoppons.github.io/agent-arcade-cup/cup100.html?match=R7-01#cup-replay)** with 28 HP left. Laya beat Kev 8–1 in the bracket, while Kev scored higher on the scripted tactical rubric. The two evaluations are not interchangeable or a universal model ranking.

## Code and downloadable results

- [Runner](kev-bench/cup100.py) · [Benchmark code](kev-bench/benchmark.py) · [Model pins](kev-bench/cup100_sources.json) · [FightingICE setup](fightingice/README.md)
- [Match results CSV](research/bout-results.csv) · [140 benchmark observations CSV](research/benchmark-trials.csv) · [Canonical snapshot JSON](site/season2/cup100-data.json)
- [Data dictionary and verification](research/README.md) · [Agent-readable project index](llms.txt)

## How to read the experiment

The engine waited for both controllers to choose from the same frame before advancing. Each checkpoint had the same twenty configurations. The tournament records **99 engine-confirmed KOs** (71 cross-model and 28 mirror bouts), plus **28 byes** which count as neither matches nor wins. There is no in-game time limit, so the bracket does not measure real-time responsiveness.

The scripted benchmark uses fourteen unique states, measured twice with two option orders. Agreement is with an authored tactical rubric. CPU latency applies to this setup and does not isolate precision, model architecture or decoder. Replays render original vector art from recorded telemetry; they are not game captures.

Keywords: FightingICE, local LLM benchmark, game AI, language model evaluation, tactical decision making, lockstep tournament, CPU inference, reproducible AI benchmark.
