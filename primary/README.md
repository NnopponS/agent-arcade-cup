# Fresh Agent Arcade Cup

A paired, prospective experiment about **what a fresh agent does with an explicit note**, using harder tactical positions derived from the 100 Games Arcade. This is distinct from the earlier scripted-bot tournament. Here, one contestant produces one final puzzle action or route directly in its own fresh native-agent session, without tools. The two contestants in the same wave independently face the same challenge; they are not playing a live multiplayer interface.

## What is fixed before play

- 50 paired challenges: 17 Connect Four Classic positions, 17 Sliding Puzzle Arcade+ layouts, and 16 Lights Out Classic boards.
- Predeclared seed `0x4b4e5432`; exactly 25 left and 25 right treatment seats, balanced within each three-title family as closely as counts permit. Opponent board/goal is identical within a pair. Prompts are frozen in `evidence/challenges.json`; answers and source-construction traces in `evidence/grading-key.json` are kept away from contestants until the relevant submission is irrevocably frozen.
- Connect Four positions are reachable via alternating drops; no prior win; one column forces a win in at most three own drops against every legal opponent move; none wins earlier under minimax. Sliding routes have a shortest length of 8–14 computed by iterative bounded search using a Manhattan lower bound. Lights Out minima are certified by checking all 32 possible top-row press patterns, with each lower-row press forced by the requirement to turn off the row immediately above.
- Runtime model, effort, scheduling, prompt notes, retention-label counterbalance and timeout treatment are specified in the organizer's separate frozen protocol. A prior alias does not mean the runtime is retained.

## Reproduce and check

The corpus is already sealed and can be verified without generating a replacement:

```sh
cd primary
sha256sum -c evidence/corpus-sha256.txt
node src/verify-corpus.cjs
ARCADE_SOURCE=/absolute/path/to/100-games node src/verify-native-rules.cjs
# Grading consumes a logged answer, not an invitation or analytic text.
node src/grade.cjs AAC-01 /path/to/reply.json
node src/summarize-lifecycle.cjs /path/to/retired-contestant-responses.jsonl
```

Reachability, search proofs and strict legal grading are code-checkable. The separate native test exercises original board-update snippets in Node: all options for both sides of each Connect Four root position and every Lights Out cell, plus every move of each reference sliding solution. It is a transition agreement check, not proof that every path was run in a browser.

## Outcomes and limits

Use paired exact correctness as the primary metric: both correct, note only, neutral only, neither, incomplete. Solve-but-not-optimal counts as an informative secondary category, not primary correctness. Rerank every answer from raw data instead of trusting supplied grades. Consider the per-family results alongside the aggregate; retain invalid, missing, timed-out, and bootstrapping attempts with honest labels. The summary computation treats a result with no code-compliant JSON as incorrect, not a silent exclusion. An exact discordance test can summarize imbalance between note-only and neutral-only pairs; repeated strategy ancestry and a single frozen task mix limit inference.

This compares **fresh starts with versus without an explicit, scoped method note**. It does not observe private model state, prove internal data erasure, compare with a long-lived runtime, or establish conclusions about other models or games. Control a long-lived runtime separately if the real question is retention versus cold recreation. Any screen animation must be labeled as an edited replay or challenge visualization unless it was directly captured from actual game interaction. Do not report \`planned\` starts as \`completed\` starts.
