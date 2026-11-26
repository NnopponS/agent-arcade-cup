# Agent Arcade Cup

Five local language-model checkpoints control 100 fighters in an untimed FightingICE knockout bracket. A separate scripted benchmark measures how often each checkpoint selects the expected move and how long it takes to reply on CPU.

**[Search 99 replays](https://nnoppons.github.io/agent-arcade-cup/cup100.html#bracket)** · **[Watch the final](https://nnoppons.github.io/agent-arcade-cup/cup100.html?match=R7-01#cup-replay)** · **[Compare models](https://nnoppons.github.io/agent-arcade-cup/cup100.html#model-notes)** · **[Decision Lab](https://nnoppons.github.io/agent-arcade-cup/#decision-lab)**

Search the replay library by match ID, fighter ID, or model name. Use the timeline or HP highlights to jump to a moment, and copy the replay link to share a match. The illustrated replays use recorded engine telemetry and do not include original game footage.

## What the results show

**LAYA-09 won the final with 28 HP left.** Laya won eight of nine Cup bouts against Kev. Kev matched more expected decisions in the scripted benchmark.

| Checkpoint | Cross-model wins / losses | Tactical agreement |
| --- | ---: | ---: |
| Julia-1 Q8 | 12 / 17 | 9/28 |
| Kev 0.8B BF16 | 8 / 18 | 18/28 |
| Laya Q8 | 36 / 4 | 15/28 |
| Qwen2.5 0.5B Instruct Q4 | 9 / 16 | 12/28 |
| SmolLM2 135M Instruct Q4 | 6 / 16 | 7/28 |

- **Cup.** Both fighters choose from the same engine frame before play advances. The 99 KOs include 71 cross-model and 28 same-model bouts. The 28 byes are neither bouts nor wins. There is no round timer, so the Cup does not measure real-time responsiveness.
- **Scripted benchmark.** Each checkpoint gets 14 states in two option orders. Agreement measures a tactical rubric, not win rate. The CPU timings do not isolate model architecture, precision, or decoding.

## Data and code

| I want to… | Start here |
| --- | --- |
| Analyze the published results | [99 bouts (CSV)](research/bout-results.csv) · [140 benchmark observations (CSV)](research/benchmark-trials.csv) · [Snapshot (JSON)](site/season2/cup100-data.json) |
| Read the data and replay format | [Data dictionary and verification](research/README.md) |
| Reproduce an experiment | [FightingICE setup](fightingice/README.md) · [Model pins](kev-bench/cup100_sources.json) · [Cup runner](kev-bench/cup100.py) · [Benchmark code](kev-bench/benchmark.py) |
| Work on the public site | [Pages preview and tests](site/README.md) |

To validate the published snapshot without installing FightingICE or downloading models:

```sh
python3 research/verify_public.py
```
