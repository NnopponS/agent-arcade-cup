import unittest

from cup100_report import action_agreement, summarize, winner_coverage


class ReportTests(unittest.TestCase):
    def test_counts_cross_model_mirrors_byes_and_side_separately(self):
        rows = [
            {"status":"bye", "id":"R1-03","winner":{"model":"model-b"}},
            {"status":"pending", "id":"R2-01"},
        ]
        def match(ident, models, ids, winner, frames):
            return dict(match=ident, models=models, entrantIds=ids, winner=winner,
                        frames=[[44], [44+frames]])
        matches = [
            match("R1-01",["model-a","model-b"],["A1","B1"],"B1",120),
            match("R1-02",["model-a","model-a"],["A2","A3"],"A2",60),
            match("R2-02",["model-b","model-a"],["B2","A2"],"A2",240),
        ]
        result = summarize(rows, matches, ["model-a","model-b"])
        self.assertEqual(result["verified"],3)
        self.assertEqual(result["crossModel"],2)
        self.assertEqual(result["sameModel"],1)
        self.assertEqual(result["byeTotal"],1)
        self.assertEqual(result["sideWins"],[1,2])
        self.assertEqual(result["medianGameFrameSpan"],120)
        self.assertEqual(result["models"]["model-a"],dict(wins=1, losses=1, mirrors=1, byes=0))
        self.assertEqual(result["models"]["model-b"],dict(wins=1, losses=1, mirrors=0, byes=1))
        self.assertEqual(result["headToHead"],{"model-a":{"model-b":1},"model-b":{"model-a":1}})

    def test_empty_snapshot_has_no_median(self):
        self.assertIsNone(summarize([], [], ["a","b"])["medianGameFrameSpan"])

    def test_action_scores_use_expected_action_for_denominator(self):
        data = {"m": {"rows": [
            {"expected":"DASH", "choice":"DASH"},
            {"expected":"DASH", "choice":"THROW_A"},
            {"expected":"THROW_A", "choice":"THROW_A"},
        ]}}
        self.assertEqual(action_agreement(data), {
            "m":{"DASH":{"correct":1,"trials":2},"THROW_A":{"correct":1,"trials":1}}
        })

    def test_distinct_winner_coverage_ignores_same_model_and_repeated_winners(self):
        roster = [
            dict(id="A1",model="a",profile="steady",temperature=0),
            dict(id="A2",model="a",profile="fast",temperature=0.2),
            dict(id="A3",model="a",profile="steady",temperature=0.6),
            dict(id="B1",model="b",profile="fast",temperature=0.2),
        ]
        bouts = [
            dict(winner="A1",models=["a","b"]),
            dict(winner="A1",models=["a","b"]),
            dict(winner="A2",models=["b","a"]),
            dict(winner="A3",models=["a","a"]),
        ]
        self.assertEqual(winner_coverage(roster,bouts)["a"],dict(entrants=2, profiles=2, temperatures=2))
        self.assertEqual(winner_coverage(roster,bouts)["b"],dict(entrants=0, profiles=0, temperatures=0))


if __name__ == "__main__":
    unittest.main()
