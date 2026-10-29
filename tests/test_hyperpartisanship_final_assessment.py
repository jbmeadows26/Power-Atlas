"""Guard the frozen October 2026 hyperpartisanship assessment against false claims.

These checks validate the complete historical panel, endpoint figures, and
document methodology. 119th Congressional statistics are treated as a dated
snapshot, so future refreshes must not invalidate this historical assessment.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "hyperpartisanship"
DOC = ROOT / "research" / "hyperpartisanship" / "FINAL_ASSESSMENT_2026-10-29.md"


class FinalAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = DOC.read_text(encoding="utf-8")
        cls.rolls = json.loads((DATA / "voteview-party-divisions-v1.json").read_text())
        cls.laws = json.loads((DATA / "baseline-v1.json").read_text())
        cls.bills = json.loads((DATA / "govinfo-119-bill-cosponsors-v1.json").read_text())
        cls.by_vote = {(x["congress"], x["chamber"]): x for x in cls.rolls["records"]}

    def test_no_historical_gaps_or_imputed_zero_rates(self):
        self.assertTrue(self.rolls["diagnostics"]["historicalCoverageComplete"])
        self.assertEqual(self.rolls["diagnostics"]["historicalMissingChamberPeriods"], [])
        self.assertEqual(len(self.by_vote), 40)
        for n in range(100, 119):
            for chamber in ("House", "Senate"):
                row = self.by_vote[n, chamber]
                self.assertEqual(row["periodStatus"], "completed_congress")
                self.assertEqual(row["evidenceStatus"], "derived_voted_member_aggregates")
                self.assertGreaterEqual(row["rollCallsEligibleBothParties"], 100)
                self.assertIsNotNone(row["opposed90PctShare"])
                self.assertIsNotNone(row["oppositePartyMajorityShare"])
        for chamber in ("House", "Senate"):
            self.assertEqual(self.by_vote[119, chamber]["periodStatus"], "incomplete_congress")

    def test_strict_opposition_rate_and_bounded_population(self):
        for n, chamber in ((100, "House"), (100, "Senate"), (118, "House"), (118, "Senate")):
            row = self.by_vote[n, chamber]
            count = row["opposed90PctPartyRollCalls"]
            denom = row["rollCallsEligibleBothParties"]
            self.assertAlmostEqual(row["opposed90PctShare"], count / denom, places=6)
            self.assertGreaterEqual(count, 0)
            self.assertLessEqual(count, denom)
        self.assertLess(self.by_vote[100, "House"]["opposed90PctShare"], self.by_vote[118, "House"]["opposed90PctShare"])
        self.assertLess(self.by_vote[100, "Senate"]["opposed90PctShare"], self.by_vote[118, "Senate"]["opposed90PctShare"])
        self.assertIn("7.7% to 48.7% in the House", self.report)
        self.assertIn("6.3% to 52.1% in the Senate", self.report)

    def test_legislative_cohort_means_match_report(self):
        rows = self.laws["series"]
        self.assertEqual(len(rows), 20)
        early = [r for r in rows if 100 <= r["congress"] <= 109]
        late = [r for r in rows if 110 <= r["congress"] <= 118]
        mean = lambda rs, key: sum(x[key] for x in rs) / len(rs)
        self.assertAlmostEqual(mean(early, "substantive_laws_pre_election"), 308.4)
        self.assertAlmostEqual(mean(late, "substantive_laws_pre_election"), 170.66666667, places=5)
        self.assertAlmostEqual(mean(early, "cloture_motions_filed"), 65.5)
        self.assertAlmostEqual(mean(late, "cloture_motions_filed"), 211.33333333, places=5)
        self.assertIn("time windows forbid joint causal estimates", self.report)
        self.assertIn("including nominations", self.report)

    def test_bipartisan_bounds_and_unknowns_never_zeroed(self):
        count = self.bills["coverage"]
        self.assertEqual(count["count"], count["crossPartyTrue"] + count["crossPartyFalseWithCompletePartyData"] + count["crossPartyUnknown"])
        self.assertGreater(count["crossPartyTrue"], 100)
        self.assertGreater(count["crossPartyUnknown"], 0)
        known_share = count["crossPartyTrue"] / (count["crossPartyTrue"] + count["crossPartyFalseWithCompletePartyData"])
        self.assertTrue(0 < known_share < 1)
        self.assertIn("not an inferential confidence interval", self.report)
        self.assertIn("party at sponsorship date", self.report)

    def test_research_status_is_descriptive_not_falsely_causal(self):
        for content in (
            "not an identified causal effect",
            "UNTESTED",
            "unproven",
            "Viral attention is not the same thing",
            "118th Congress",
            "PNAS Nexus",
            "Böken",
            "not established",
            "production",
        ):
            self.assertIn(content.lower(), self.report.lower())
        self.assertIn("FINAL RESEARCH ASSESSMENT", self.report)
        self.assertIn("38 of 38 completed slots verified", self.report)

if __name__ == "__main__":
    unittest.main()
