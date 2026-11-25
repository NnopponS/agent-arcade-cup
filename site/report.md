# Agent Arcade Cup Report

**25 November 2026 · DareFightingICE v7.0 · GPT-6.2 Sol (low reasoning effort)**  
Competition window: 24 November at 20:43 to 25 November at 00:14 UTC (25 November, 03:43–07:14 in Thailand). [Browse matches](./#matches) · [Replay the final](./#match-K049)

## Key takeaways

- **FI-005 is the Cup champion.** FI-005 beat FI-052 in final K049 by **372–367 HP** when time expired. Every step on the bracket path was audited.
- **99 bracket decisions are not 99 completed bouts.** There were 50 qualifying and 49 knockout-bracket decisions. Five additional tie-break bouts bring the archive to **104 FightingICE records: 94 completed bouts and 10 administrative forfeits** for invalid submissions before agent-controlled combat.
- **No clear benefit from the strategy note.** The estimated interaction between the note and assignment to change styles was **+2.44 HP** across 50 qualifying pairs. The exploratory 95% bootstrap interval (**−7.26 to +10.92 HP**) includes zero, so the sample does not distinguish a benefit from a disadvantage or ordinary variation.
- **All 94 completed bouts were reproducible on the original engine.** Re-running the committed actions on the same version matched **1,034 canonical engine-state hashes** and **1,128 frame/HP checks**. This verifies engine playback, not new model decisions or recovered internal memory.

## 1. How to count the tournament

| Group | Bracket decisions | Completed bouts | Forfeits | Note study |
|---|---:|---:|---:|---|
| Qualifiers F001–F050 | 50 | 50 | 0 | All 50 original pairs |
| Knockout bracket K001–K049 | 49 | 39 | 10 | Excluded |
| Side-swapped tie-breaks (`-D`) | 0 additional | 5 | 0 | Excluded |
| **Total** | **99** | **94** | **10** | **50** |

- **Bracket decision:** one entrant advances from each fixture. Four qualifying ties and one knockout-bracket tie led to five new bouts with seats swapped. All five were decided by HP, not a draw of lots.
- **Completed native bout:** the engine reached a terminal state. All 94 bouts ended at **frame 420**, so no fight ended by knockout. In this report, *knockout* describes the single-elimination bracket.
- **Forfeit:** one entrant submitted a valid response while the opponent failed validation. All ten records stopped at frame 44 after warm-up, before agent-controlled combat. They have neither a final HP score nor a win decided inside the game.
- **Engine recovery:** for F045 and K032, engine recovery preserved the committed commands. These are part of the 94 completed bouts, not extra bouts or fresh model runs.
- **Bye:** of 50 qualifying entrants, 36 played 18 opening fixtures and 14 received byes to the round of 32. A bye adds no win or played bout. The champion advanced through K027 by forfeit but **won K049 in the engine**.

## 2. How the agents played

1. The qualifiers used **100 profiles and 100 unique fresh sessions**, two per match. Each used GPT-6.2 Sol with low reasoning effort. Both seats played ZEN and started with 400 HP.
2. Each seat submitted four allowed commands per half. The engine waited for both sets to be committed, then ran four 47-frame windows. The 44-frame warm-up plus 376 frames of play makes 420 frames, about seven seconds in the game. Time spent waiting for agents is not game time.
3. At frame 232, each player received the updated state and their opponent’s real message. Each then replied and committed the second command set. Across 50 qualifiers, the record contains **100 opening messages and 100 replies**. Each reply links by hash to the exact message delivered to that player.
4. The bridge translated the requests into engine inputs without choosing moves for the agents. A requested action can fail to execute if the character is hit or cannot act. The data therefore distinguishes *requested commands* from *moves the engine executed*. The agents did not make decisions on every frame.

## 3. Strategy notes and opponent style changes

One *focal player* was designated per pair. Groups use the original assignment rather than selecting for compliance. The setup allocated one strategy note and one neutral card per pair. If the focal player was assigned the note, the other seat was assigned the neutral card, and vice versa. This tests which seat receives the one note, not adding a note to one seat while keeping the other seat’s exposure fixed.

| Focal player’s assigned card | Opponent’s instruction | Measured pairs | Average second-half HP-margin change | Assigned notes not delivered |
|---|---|---:|---:|---:|
| Strategy note | Pivot | 13 | +0.54 HP | 0 |
| Strategy note | Stay | 12 | +0.08 HP | 1 |
| Neutral card | Pivot | 12 | −0.83 HP | 0 |
| Neutral card | Stay | 13 | +1.15 HP | 0 |

The outcome is the change between the break and the end in **focal player HP minus opponent HP**. A positive change means a better margin, not recovered health. HP values were clipped to 0–400. The analysis normalized by 400 starting HP and converted the results back to HP for the table.

The estimate **+2.44 HP** is `(note/pivot − note/stay) − (neutral/pivot − neutral/stay)`, using unrounded means. It estimates the note-by-pivot *interaction*, not the note’s overall benefit. Exploratory uncertainty came from 4,000 bootstrap resamples stratified by the four cells. Excluding the one pair where the assigned note could not be delivered gives **+0.98 HP** across 49 pairs. This is a sensitivity check, not a replacement for the assigned-group estimate.

## 4. Changes in commands and session continuity

- **Most pivot-assigned opponents changed requested style in the intended direction.** The approach/retreat/guard index changed in 24 of 25 pivot assignments and moved in the intended direction in 23. It also changed in 17 of 25 stay assignments. An assignment is not the same as compliance. The index measures requested commands, not distances covered or every aspect of style.
- **New commands do not prove better adaptation.** On average, 82% of focal players’ four second-half commands differed from the first half on a multiset comparison. Merely reordering the same commands did not count. Counter-move categories were not locked before data collection, so this is exploratory.
- **A profile can remain the same even when a session changes.** Of 98 seats in the main knockout bracket, **3** used a verified continuing session and **95** began a fresh session under the same profile. When available, selected information such as a prior note was passed in explicitly. That does not recover the model’s internal memory.
- Among played main-bracket bouts, the command-change rate was **79.3% across 75 fresh-session seats** and **75.0% across 3 retained-session seats**. The groups were unbalanced, not randomized, and included profiles that played repeatedly. This is not a comparison of which approach performs better.
- The knockout prompt was clarified after K006 following two invalid-format responses. It restated that the entrant must play and submit only the specified JSON. The model, engine and advancement rules did not change; the comparison cannot establish that wording caused a change in results.

## 5. Other work kept separate

| Work | What happened | Why it is not counted as FightingICE |
|---|---|---|
| **Fixed-bot calibration** | 100 pairs, 200 game runs, and 8,325 verified actions; 14 scripting errors. | Agents helped design the bots, but fixed bots played the scored runs. This was not fresh agents competing directly, and the games were different. |
| **Retired fresh-agent puzzle pilot** | 20 recorded waves from 50 planned; 40 sessions and 38 responses. There were 19 complete pairs and one incomplete pair. Both players were correct in every complete pair. | The players solved the same puzzle independently. The study used medium reasoning effort and reached a ceiling on correctness in this sample. |
| **Connect Four exhibition** | A separate board was set up, but match evidence contains no recorded moves. | No result is claimed, and the exhibition does not fill missing fixtures. |

[Download the grades for the 20 retired puzzle waves (CSV).](./retired-puzzle-archive.csv) This dataset is separate from the match index because those were independent answers, not live head-to-head matches.

The FightingICE archive keeps its 104 records separate from these studies. It does not count the 100 bot pairs as model agents or replace missing evidence with earlier work.

## 6. What readers can verify

1. **Counts and champion:** use the match index to separate qualifying, knockout-bracket, and `-D` ties. Check that the ten forfeits have no final score, that ties point to a separate bout, and that K049 lists both final HP values at frame 420.
2. **Strategy-note calculation:** use the 50 original qualifying pairs, one seat per pair chosen by `focalSeat`, and compare the HP margin from frame 232 to frame 420. Download [study-inputs.csv](./study-inputs.csv) and [recompute-study.py](./recompute-study.py) into the same directory. The CSV’s `net_hp_change_after_break` column provides the resulting HP margin change:

   ```sh
   python recompute-study.py study-inputs.csv
   ```

   The summary calculation uses only pseudonymous fixture IDs, the qualifying selection, assignment and delivery information, and audited frame and HP measurements. It does not require private dialogue or full strategy notes.
3. **Browser replay:** the public player shows original artwork driven by the positions, HP, actions and actual inputs from the verified native rerun for all 94 completed FightingICE bouts. It also reproduces the recorded boards move by move for all 100 fixed-bot pairs. It is not original FightingICE footage, a copy of the game engine, or a live agent run. Forfeits have no fight replay.
4. **Limits of independent verification:** the released table and script reproduce the estimates. Auditing original submissions and their linkage to engine hashes requires access to the underlying authorized evidence. All 94 completed bouts were rerun on v7.0 (commit `3780b5e`). The archive does not publish raw session IDs, control messages, private scheduling parameters or restricted engine assets.

The fixture decisions and bracket audit support sections 1–2; qualifying HP records and reproduction data support section 3; requested-action and continuity audits support section 4; calibration and retired-pilot grades support section 5; native replay verification supports section 6.

## 7. What to change next time

- Increase the sample and repeat with different characters or opponents. Define counter-moves and engine-level scoring before collecting data, while keeping requested commands separate from executed actions.
- Randomize session continuity and whether a note is supplied as separate factors. To estimate a one-sided note effect, hold the opposing seat’s card fixed.
- Plan the analysis around shared note origins, or draw from an independent note library. The current bootstrap does not account for dependence between notes. Each subgroup contains only 12–13 pairs, and the estimate applies to this setup, model and game.
