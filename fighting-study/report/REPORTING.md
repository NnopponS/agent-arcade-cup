# Reporting checklist

The edited film and the research record serve different purposes. The film shows two selected authentic examples and the tournament winner. The report evaluates only the primary cohort for the card-by-pivot question.

## Build the report from observed data

From the project root, replace `PRIVATE_RUN` with a local copy of the genuine retained records. The operator's private transcripts are not included in the published bundle. From the public bundle, reproduce the aggregates from the already sanitized `observed-heats.jsonl` and published formulas; raw-runtime verification requires authorized access to original records.

```sh
mkdir -p RESULTS
node fighting-study/report/audit-release.cjs PRIVATE_RUN RESULTS/audited-match-results.json
python fighting-study/report/summarize.py PRIVATE_RUN/matches RESULTS
python fighting-study/report/behavior.py PRIVATE_RUN/matches RESULTS/token-diagnostics.json
python fighting-study/report/markdown.py RESULTS/audited-match-results.json RESULTS/summary.json RESULTS/token-diagnostics.json RESULTS/README.md
python fighting-study/report/draw-result.py RESULTS/summary.json RESULTS/hp-contrast.svg
```

- Keep the frozen protocol intact. The final record describes which draft aims were not operationalized. Counterpart stance and the exact-token diagnostics are retrospective proxies, not a frozen response family.
- Gate a winner claim on the complete dependency graph. Count on-engine finishes, native rematches, seeded lots, and forfeits distinctly. A forfeit is neither a played finish nor two speakers.
- Publish selected engine telemetry and the score readout, not game sprites, sounds, runtime pathnames, full private notes, raw communications or secret values from unrelated systems. The schedule nonce is deliberately public **only after** the full bracket closes.
- Preserve treatment assignment and actual received card separately. Do not call a carried note a persistent model memory. Explain whether the prior runtime was actually reachable at the next appearance.
- Interpret the bootstrap interval as an exploratory uncertainty summary; it does not model inheritance across sequential notes. Use real HP units and preserve zero on the figure.
- Original replays must hash-match the pinned engine; dramatic animation and synthesized line performance should be labeled. If a tied rematch or final forfeit resolves the bracket, report that decision explicitly in both the film and the report.
