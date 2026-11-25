# Agent Arcade Cup: Knockout Season

[Open the current website and replays](https://nnoppons.github.io/agent-arcade-cup/).

Eight local scikit-learn decision trees participate in a seven-bout, single-elimination FightingICE 7.0 tournament. Both characters start at 400 HP. Only native KO advances the bracket; a watchdog is an unresolved technical stop, never a points decision. Each seat independently predicts one action from current engine state every six frames, rather than submitting a prewritten sequence. The runner advances on a paced 60 Hz timeline; the web replay samples at 10 Hz. This is not an LLM or an online-learning experiment.

The trained trees copy different heuristic coaches and are not independent human-level competitors. Default model cadence, match outcomes, and timing are documented in the published data.

- Runner: `season2/run.py` (Python, scikit-learn, plus separately obtained FightingICE v7.0 and Java 21).
- Checks: `python site/season2/verify_season.py`.
- The deployment allowlists the new season only. Earlier files in this private repository are not part of the current website, and Git history is unchanged.
