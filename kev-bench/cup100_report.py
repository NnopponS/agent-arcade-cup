"""Describe a fixed tournament snapshot without treating bouts as IID samples."""
from statistics import median


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
