"""Describe a fixed tournament snapshot without treating bouts as IID samples."""
from statistics import median


def action_agreement(comparison):
    """Count agreement against the authored expected action, by model and action."""
    out = {}
    for model, scores in comparison.items():
        actions = out[model] = {}
        for row in scores["rows"]:
            expected = row["expected"]
            stats = actions.setdefault(expected, dict(correct=0, trials=0))
            stats["trials"] += 1
            stats["correct"] += row["choice"] == expected
    return out


def winner_coverage(roster, bouts):
    """Count distinct settings represented among cross-model winners."""
    entrants = {e["id"]: e for e in roster}
    winners = {e["model"]: set() for e in roster}
    for bout in bouts:
        if bout["models"][0] != bout["models"][1]:
            winner = entrants[bout["winner"]]
            winners[winner["model"]].add(winner["id"])
    return {
        model: dict(entrants=len(ids),
                    profiles=len({entrants[i]["profile"] for i in ids}),
                    temperatures=len({entrants[i]["temperature"] for i in ids}))
        for model, ids in winners.items()
    }


def summarize(bracket, bouts, checkpoints):
    counts = {m: dict(wins=0, losses=0, mirrors=0, byes=0) for m in checkpoints}
    h2h = {m: {n: 0 for n in checkpoints if m != n} for m in checkpoints}
    side_wins = [0, 0]
    frame_spans = []
    for row in bracket:
        if row["status"] == "bye":
            counts[row["winner"]["model"]]["byes"] += 1
    for bout in bouts:
        side = bout["entrantIds"].index(bout["winner"])
        w, l = bout["models"][side], bout["models"][1 - side]
        side_wins[side] += 1
        frame_spans.append(bout["frames"][-1][0] - bout["frames"][0][0])
        if w == l:
            counts[w]["mirrors"] += 1
        else:
            counts[w]["wins"] += 1
            counts[l]["losses"] += 1
            h2h[w][l] += 1
    return dict(verified=len(bouts), crossModel=sum(x["wins"] for x in counts.values()),
                sameModel=sum(x["mirrors"] for x in counts.values()),
                byeTotal=sum(x["byes"] for x in counts.values()), sideWins=side_wins,
                medianGameFrameSpan=median(frame_spans) if frame_spans else None,
                models=counts, headToHead=h2h)
