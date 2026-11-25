import unittest

from cup100_report import summarize


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


if __name__ == "__main__":
    unittest.main()
