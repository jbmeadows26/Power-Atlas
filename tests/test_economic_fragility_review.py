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

if __name__=="__main__":
    unittest.main()
