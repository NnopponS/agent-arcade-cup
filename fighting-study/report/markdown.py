"""Build a reader-facing results summary from audited records, not hard-coded outcomes."""
import argparse,json
from pathlib import Path

def finish(report, hp, behavior):
    e=report['evidence']
    if (e['verified_admissions'],e['qualifying_two_speaker'],e['knockouts_verified'])!=(100,50,49) or not e['champion']:
        raise ValueError('This is not an audited full result')
    if hp['completed_primary_heats']+hp['recorded_nonplayed']!=50:
        raise ValueError('Primary denominator inconsistent')
    final=report['final']
    tie=' A tied rematch advanced the champion by the declared seeded lot, not by a decisive native win.' if final['decision']=='administrative-tie' else ''
    if final['decision']=='administrative-forfeit':
        tie=' The final was resolved by a recorded forfeit, not an on-engine victory.'
    lines=["# Agent Arcade Cup: what happened when strategies changed?",
           "",
           f"**Champion: {e['champion']}**. Final record: {final['id']}, {final['A']} vs. {final['B']}.{tie}",
           "",
           "A fighting-game tournament and an exploratory study of how identically configured agents adapt during a match.",
           "",
           "## The setup",
           "",
           f"- 100 distinct, fresh contestant runtimes, 50 opening heats and {report['authenticatedPrimaryReplies']} recipient-linked replies in the primary heats. Two contestants at a time, not 100 simultaneous processes.",
           f"- {report['engine']} ({report['engineCommit']}), identical ZEN fighters with 400 HP. Each agent chose four legal commands per half; the engine waited for both decisions before stepping through the commands.",
           "- Every contestant used **GPT-6.2 Sol, reasoning effort low**. Other models were not tested. This is a turn-gated native game evaluation, not an official real-time contest.",
           "- Each player saw its opponent's real opening line at the break. A hash binds each recorded reply to the actual line delivered. On-engine state, not what a contestant said it intended to do, determines the result.",
           "",
           "## Did a strategy note change performance?",
           "",
           "| Assigned note | Opponent instruction | Scored heats | Mean phase-two net HP change | Assigned note unavailable |",
           "|---|---|---:|---:|---:|"]
    for v in hp['bins']:
        lines.append(f"| {v['assigned_card']} | {v['assigned_stimulus']} | {v['n']} | {400*v['mean_focal_net_phase2_hp_per400']:+.2f} HP | {v['method_card_unavailable_or_not_delivered']} |")
    est=hp.get('hp_difference_in_differences')
    lines.append('')
    if est:
        lo,hi=est['bootstrap_percentile_95_hp']
        lead=f"The exploratory note-by-pivot estimate was **{est['in_HP']:+.2f} HP**; the 95% bootstrap interval was **[{lo:+.2f}, {hi:+.2f}] HP**."
        if lo<=0<=hi:
            lead+=' This pilot does not establish that the note improved performance.'
        if est['delivered_card_sensitivity_HP'] is not None:
            lead+=f" Restricting to heats where the assigned card was delivered gives {est['delivered_card_sensitivity_HP']:+.2f} HP (descriptive sensitivity check)."
        lines.append(lead)
    if hp['recorded_nonplayed']:
        lines.append(f"{hp['recorded_nonplayed']} early or nonplayed records are kept in the tally and not treated as completed two-phase gameplay.")
    checks=behavior['assignment_is_not_compliance']
    pivot=checks.get('pivot',{})
    if pivot.get('scored'):
        lines.extend(['', f"Under the exploratory spacing proxy, **{pivot['observed_shift_toward_assigned_direction']}/{pivot['scored']}** pivot-assigned opponents shifted in the intended direction. This refers to requested commands (advance vs retreat or guard), not guaranteed native actions."])
    lines+=['',
            'An exact-token diagnostic is provided separately. It measures overlap in the four requested commands between phases; rearrangement alone does not count. The response-family taxonomy in the draft protocol was not frozen before data collection, so this is not a confirmatory behavioral result.',
            '',
            '## What continued after a runtime ended?',
            '',
            f"Fifty winning profiles entered 49 bracket decisions. Across regular knockout seats, {report['continuity']['retained']} retained an observed native runtime and {report['continuity']['rehydrated']} were rehydrated under their same public ID with an explicit prior note when available. Rehydration is not memory recovery, and runtime retention was not randomized.",
            f"The 49 regular knockout fixtures included {report['fullNativeKnockouts']} on-engine finishes and {report['knockoutForfeits']} invalid-submission forfeits. A forfeit was not scored as a played fight, and its missing dialog or inputs were not reconstructed.",
            f"Brackets exclude mirrored tie-breaks from the 49-decision count. The native log also contains {report['auditedNativeAdditionalRounds']} additional tie-break matches and {report['engineRecoveredRecords']} engine recovery records.",
            '',
            '## Limits and reproduction',
            '',
            '- One model setting, one character mirror and short decision windows. A private instruction encourages style; it does not force a physical move. One strategy note may influence later notes, so naïve bootstrap intervals do not account for note-lineage dependence.',
            '- Case footage is original animation rebuilt from the pinned engine state. A selected comeback shows what happened in one heat, not what an average heat looked like.',
            '- Final scores and reply binding are separately auditable from actual accepted inputs. Public-profile IDs are pseudonyms. No private runtime identifiers, raw handoff notes, authentication data or game assets are included.',
            '',
            'See the accompanying observed-heats JSONL, audited-match results JSON, HP summary and token diagnostics for the tables and exact denominators.',
            '']
    return '\n'.join(lines)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for v in ('audit','hp','behavior','output'):
        p.add_argument(v,type=Path)
    a=p.parse_args()
    a.output.write_text(finish(*(json.loads(x.read_text()) for x in (a.audit,a.hp,a.behavior))),encoding='utf-8')
