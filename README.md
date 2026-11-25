# Agent Arcade Cup: 100-agent tournament

[Watch the championship replay](https://nnoppons.github.io/agent-arcade-cup/cup100.html?match=R7-01#cup-replay) · [Full bracket, all 99 replays, and model comparison](https://nnoppons.github.io/agent-arcade-cup/cup100.html)

**LAYA-09 is the champion.** It knocked out LAYA-06 and finished with 28 HP.

## What ran

Five local model checkpoints (Julia-1, Kev 0.8B, Laya, Qwen2.5 0.5B Instruct, and SmolLM2 135M Instruct), with the same twenty prompt/temperature configurations per model. The bracket recorded **99 engine-confirmed knockouts**, including 71 cross-model and 28 same-model bouts. The 28 bracket byes are not wins.

Both controllers see the same game frame and legal option menu, from their own fighter's perspective. The engine waits for both valid choices, then advances. No round timer decides a result; a double knockout does not advance either fighter. This tests the controllers with equal decision opportunities, not which one reacts faster in real time.

## What we learned

- Laya went **36–4** against other checkpoints. Its cross-model wins came from 15 distinct entrants across 5 prompt profiles and 4 temperatures. Against Kev specifically, Laya went **8–1**.
- Kev led the fixed-scenario test (**18/28** vs. Laya's **15/28**) and selected the expected standing punish **8/8** times but the expected throw only **1/8**. Laya was **6/8** and **4/8**, respectively. The fixed scenarios and the bracket have different states and menus. Neither establishes what caused a particular win or gives a universal ranking.

The web player reconstructs native game telemetry and lets you scrub or change playback speed. It is not rendered game footage. The [Decision Lab](https://nnoppons.github.io/agent-arcade-cup/) holds the separate CPU latency and real-time timing tests.

Reproducibility: `kev-bench/` holds the runner, benchmark, source pins, snapshot generator, and tests. Model weights and raw runner records are not distributed through Pages.
