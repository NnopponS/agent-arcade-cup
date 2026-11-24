# Agent Arcade Cup

**100 browser games started it. Can a fresh AI player inherit a strategy without inheriting a conversation?**

A research-style extension of [100 Games](https://github.com/NnopponS/100-games), by Worapon Sangsasri. This repo is private while the study runs.

## Primary study: fresh-agent tournament

**Status: in progress.** Target: 50 sequential waves, two newly spawned agents per wave, 100 unique agent profiles. This is not the same as running two programs 100 times.

- The agents themselves answer the same hard puzzle in each wave. The preset pool is Connect Four forced-win positions, shortest-path 4×4 Sliding Puzzle, and minimum-move 5×5 Lights Out.
- Fresh runtimes do not inherit the parent conversation. One seat is assigned a narrowly scoped prior strategy note; the paired control receives a neutral note. Any first-title bootstrap or unusable note is logged.
- A separate experimental factor varies whether a fresh runtime receives a predecessor's public alias or a new alias. Identity labels are not evidence of hidden platform memory.
- Each observable submission is independently scored. Paired wins, ties, failures, timeouts, note provenance, lifecycle status, and family-level outcomes will be reported.
- “Retired” means a run has ended before the next two begin. It does not mean deleting platform records. No hidden reasoning, credentials, or unrelated conversation is part of the research data.

### Frozen input commitments

```text
a6aa2cee8bff02c2000b741dc93cc0c164b11909e68c99776125c67804886b7f  primary/evidence/challenges.json
08be7455b71e26dadfd4f7660470a5a16a62ff39bda4e0add3bee050106c467b  primary/evidence/grading-key.json
d0cb5d5ac3e1b61d636ab415dab9ef637feac4fe6ae088736622c17bcf07091d  lifecycle/persona-schedule-commitment.json
```

## Engineering pilot: two independently authored strategy bots

A separate 100-round paired pilot debugged native game engines, result recording and the replay pipeline. Its fixed bots played 2048, Sliding Puzzle, Lights Out and Battleship. Recorded result: **Keystone 24 · Lantern 29 · Ties 47**. The run includes 11 rounds affected by an action watchdog; excluding those rounds gives 19 · 26 · 44 respectively. These are not fresh-agent outcomes or a model comparison.

See [fresh-agent methodology](primary/README.md), [lifecycle protocol](lifecycle/protocol.md), and [pilot verification](arena/evidence/verified-summary.json).
