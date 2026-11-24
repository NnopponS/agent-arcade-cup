# FightingICE v7.0 integration

Development fixtures only. No contestants are enrolled by this directory.

## Upstream and rights

- Source: [TeamFightingICE/FightingICE v7.0](https://github.com/TeamFightingICE/FightingICE/tree/v7.0) at exact commit `3780b5efa3f5ecf142369e567a43a8c292013a58`; tracked source was compiled locally for validation, and the native bridge runs against the official release jar.
- Official [v7.0 platform ZIP](https://github.com/TeamFightingICE/FightingICE/releases/download/v7.0/DareFightingICE-7.0.zip), SHA-256 `d14ce73530b190686abe787416f178fe03400b8c48b328497a57a4978a8e2e9a`.
- Official [v6.3 resource ZIP](https://github.com/TeamFightingICE/FightingICE/releases/download/v6.3/resources-6.3.zip), reused by v7.0 per the release notes, SHA-256 `cc04f64518a8c7f7f09508def8a5673930b8d0effa877f643bcd583fd4e57f06`.
- Official jar SHA-256 `f159c485e10860ab31a2978f8b2dcfecb2c45f9bbde7e66948d0f904365b5d1c`.
- No explicit project/source redistribution license or public gameplay-footage clearance was found in the inspected upstream tree or ZIP manifests. The [official organizer site](https://www.ice.ci.ritsumei.ac.jp/~ftgaic/) credits game resources to **The Rumble Fish 2 / Dimps Corporation** and explains their release for AI research. Do not redistribute upstream source, jar, resources or unlicensed rendered footage with this package. Acquire upstream files directly from the official download; retain native captures locally. For publication, our independent vector replay uses only numeric engine telemetry and new art, no game sprites, music, logos, UI imagery, or other game assets. This does not assert that public use of actual footage is categorically prohibited or licensed.

## Reproduction

Use Java 21 with `jdk.compiler` (a full JDK, or a distribution that includes the compiler module), Python 3 and optionally Pillow/FFmpeg. Download and extract the official release beside this README as `DareFightingICE-7.0/`, then extract the resources ZIP inside that directory. Alternatively set `FIGHTINGICE_RUNTIME` to the prepared directory. No GPU, network server, purchases or game accounts are required for the state stepping. The official launcher v7.0 changed gRPC to socket; this local bridge calls the original Java core directly, rather than coordinating opaque asynchronous controller threads. The verified official Headless launcher test is separately built-in AI vs built-in AI, not contestant play. Its binary replay worked, while its optional JSON flag lacks a bundled provider.

```bash
printf 'new 420 400 ZEN ZEN\nstep 44 FORWARD_WALK FORWARD_WALK\nobserve\nstep 47 STAND_FB CROUCH_GUARD\nquit\n' | ./run-bridge.sh
python src/preflight.py
python src/render-trace.py evidence/development-original.frames.jsonl footage/development-vector-proof.mp4
```

| Line | Effect |
| --- | --- |
| `new 420 400 ZEN ZEN` | Reset frame count, native engine, both queues and output writers; 420 frames, 400 starting HP each. |
| `observe` | Inspect both characters, logical frames, terminal status, and hashes without advancing. |
| `step 47 ACTION1 ACTION2` | Apply both committed action intents at the same boundary. Advance up to exactly 47 frames unless terminal. Player keys derive from native CommandCenter and update together in native KeyData. |
| `trace /absolute/path/file.jsonl` | Record initial state and every subsequent processed frame with native key masks, fighter metrics and canonical checksum. Ends on a new match or quit. |
| `capture /absolute/private/folder 4` | Use the official AWT renderer to capture real frames locally, every 4 native frames, plus terminal frame when off stride. Not a browser webcam or physical monitor capture; not part of public package. |
| `quit` | Exit. Last observed terminal result is authoritative. |

The committed action is **re-issued through native CommandCenter whenever controllable**, consuming its queued keys even across boundaries. An intent does not guarantee execution; the engine controls collision, energy, hitstun, ranges and cancel windows. Integer counters separately report how many queues began, how many frames sent any actual key, and how many frames sampled a matching native action. For `NEUTRAL`, no new command is generated; its matching native action frames are still counted. Warmup is a disclosed symmetric 44-frame forward walk, from x240/720 to x455/505 with no damage. Eight 47-frame simultaneous decision windows produce exact 420-frame terminal time unless earlier KO. Both HP equal at timeout is a draw, not an arbitrarily awarded winner.

The literal protobuf checksum contains random per-attack UUIDs from the original engine. Canonical equality strips only protobuf fields named `identifier`; that UUID is copied for observation, not compared by gameplay. `nativeFrameSha256` is canonical; `rawNativeFrameSha256` is forensic and not guaranteed equal across runs. Trace files contain the canonical hash; the bridge does not patch upstream RNG or engine physics. Cosmetic hit-effect offset randomness belongs to original graphics and is not claimed deterministic.

## Development proof (not Cup results)

`evidence/development-preflight.json` records a 420-frame fixed-input demo ending 370–365, its exact duplicate, the mirrored 365–370 outcome, an alternate-command 380–348 result, and a separate native KO at frame 67. Original and repeated runs have byte-identical 421-row canonical traces including both players' actual key masks, with game-render capture active on the repeat. A malformed command was rejected without mutation, and more inputs do not advance after terminal. None of these fixtures are fresh-subagent results or competition scores.
