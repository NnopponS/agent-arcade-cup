# Agent Arcade Cup

**100 browser games started it. Can a fresh AI player inherit a strategy without inheriting a conversation?**

A research-style extension of [100 Games](https://github.com/NnopponS/100-games), by Worapon Sangsasri. This repo is private while the study runs.

## Current tournament: FightingICE

**Status: live qualification underway. No tournament champion yet.** The new Cup uses the [official FightingICE engine](https://github.com/TeamFightingICE/FightingICE), pinned to v7.0. A calibration-only test recorded a full headless native fight with simultaneous, explicit two-seat control, verified a side mirror, and established that changing a command changed native HP. Calibration is not part of the 100-profile study.

The new experiment concerns what players do when an opponent changes tactics, and whether bounded strategy notes help them adapt. Wording, outcomes and uncertainty will be tied to observable native decisions, never to claimed hidden memory. The 50 opening heats and the 49 played knockouts are separate from the old puzzles below. Audio/voice and video production has its own evidence and release gate.

## Retired puzzle study: fresh-agent protocol

**Status: retired.** This initial puzzle format was stopped before completion and is excluded from the next Cup. No winner was declared. The next game selection is pending. Original target: 50 sequential waves, two newly spawned agents per wave, 100 unique agent profiles. This is not the same as running two programs 100 times.

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

## Tournament layer: open play

The original paired answers are sealed first. The same 100 profiles then enter a separate [Cup bracket](cup/README.md): open dialogue in all 50 heats, then 49 played knockouts. The bracket code has been fixture-tested; no actual champion is declared. Byes and missing submissions never count as wins. Experimental tie scores are not silently forced into a result.

The [FightingICE protocol](fighting-study/PROTOCOL.md), [engine bridge](fightingice/README.md) and [video production plan](edit/fighting/story-plan.json) are included. Early successful heats are not a complete dataset. Raw upstream game assets, internal tool paths, and native captures are intentionally excluded.
