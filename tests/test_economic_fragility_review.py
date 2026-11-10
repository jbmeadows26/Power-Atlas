"""Guardrails for the unpublished economic fragility research page."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/economic-fragility/2027-review-v1.json"
PAGE=ROOT/"platform/unified/economic-fragility-review.html"

class EconomicFragilityReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(DATA.read_text(encoding="utf-8"))
        cls.html=PAGE.read_text(encoding="utf-8")

    def test_branch_evidence_is_not_marked_public(self):
        self.assertEqual(self.d["publicationStatus"],"review_only_not_approved")
        self.assertIn('name="robots" content="noindex,nofollow"',self.html)
        self.assertIn("UNPUBLISHED · REVIEW DRAFT",self.html)

    def test_metrics_are_dated_sourced_and_caveated(self):
        self.assertGreaterEqual(len(self.d["metrics"]),5)
        ids=[v["id"] for v in self.d["metrics"]]
        self.assertEqual(len(ids),len(set(ids)))
        for x in self.d["metrics"]:
            with self.subTest(metric=x["id"]):
                self.assertTrue(x["source"].startswith("https://"))
                self.assertTrue(x["period"] and x["measure"] and x["interpretation"])
                self.assertIn(x["direction"],("resilience","stress","mixed"))

    def test_financing_instruments_cannot_be_misinterpreted_as_losses(self):
        f=self.d["financing"]
        self.assertEqual({x["id"] for x in f["items"]},{"revenue","debt","equity"})
        self.assertEqual({x["id"]:x["billions"] for x in f["items"]},{"revenue":1400,"debt":650,"equity":300})
        self.assertIn("neither realized losses",f["interpretation"])
        self.assertIn("not losses",self.html)

    def test_no_spurious_local_or_crash_probabilities(self):
        combined=" ".join(self.d["evidenceRules"])
        self.assertIn("No numeric forecast",combined)
        self.assertIn("ZIP",combined)
        self.assertNotIn("navigator.geolocation",self.html)
        self.assertNotIn("localStorage",self.html)
        self.assertNotIn("2027 crash probability",self.html)

    def test_page_points_to_the_review_dataset(self):
        self.assertIn("../../data/economic-fragility/2027-review-v1.json",self.html)
        self.assertIn("Data are unavailable rather than zero",self.html)
        self.assertIn("scenario_not_forecast",str(self.d["pathways"]))
        self.assertEqual(len(self.d["connections"]),3)


    def test_market_stress_is_sourced_comparable_and_review_only(self):
        market = self.d["marketStress"]
        self.assertEqual(market["asOf"], self.d["asOf"])
        self.assertEqual({m["id"] for m in market["measures"]}, {"sp500", "nasdaq", "sox"})
        self.assertEqual(len(market["historicalSp500Drawdowns"]), 5)
        self.assertEqual(market["historicalSample"]["atLeastSixPercentEvents"], 56)
        self.assertFalse(market["historicalSample"]["currentSp500InSample"])
        self.assertIn("not a model of future crash probability", market["historicalSample"]["description"])
        self.assertEqual(market["evidenceLevel"], "verified_snapshot_with_third_party_historical_comparisons")
        for item in market["measures"]:
            with self.subTest(index=item["id"]):
                self.assertGreater(item["drawdownPercent"], 0)
                self.assertLess(item["drawdownPercent"], 100)
                self.assertTrue(item["source"].startswith("https://"))
                self.assertTrue(item["recordDate"].startswith("2026-"))
        self.assertIn('id="markets"', self.html)
        self.assertIn('id="marketBars"', self.html)
        self.assertIn('id="historicBars"', self.html)
        self.assertIn('id="marketPathways"', self.html)
        self.assertIn('class="marketItem"', self.html)
        self.assertIn("s.historicalSp500Drawdowns", self.html)
        self.assertIn("scenarios to investigate", self.html.lower())
        site_data = json.loads((ROOT / "site/data/economic-fragility/2027-review-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(site_data, self.d)
        site_page = (ROOT / "site/economic-fragility-review.html").read_text(encoding="utf-8")
        self.assertIn('id="markets"', site_page)
        self.assertIn('name="robots" content="noindex,nofollow"', site_page)

if __name__=="__main__":
    unittest.main()
