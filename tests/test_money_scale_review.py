"""Review guards for the independently sourced scale-of-money explorer."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site/data/money-scale-v1.json"
PAGE = ROOT / "site/money-scale-review.html"
REDESIGN = ROOT / "site/redesign-preview.html"

class MoneyScaleReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.redesign = REDESIGN.read_text(encoding="utf-8")

    def test_review_only_and_visible_navigation(self):
        self.assertEqual(self.data["status"], "review-only")
        self.assertIn('name="robots" content="noindex,nofollow"', self.page)
        self.assertIn("REVIEW ONLY", self.page)
        self.assertIn("money-scale-review.html", self.redesign)
        self.assertIn('fetch("data/money-scale-v1.json"', self.page)

    def test_every_metric_has_a_source_a_year_and_a_measurement_kind(self):
        self.assertGreaterEqual(len(self.data["metrics"]), 9)
        ids = [x["id"] for x in self.data["metrics"]]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = {"asset-stock", "liability-stock", "annual-flow",
                   "annual-flow-estimate", "annual-flow-alternative"}
        for x in self.data["metrics"]:
            with self.subTest(id=x["id"]):
                self.assertIn(x["measurement"], allowed)
                self.assertGreater(x["valueTrillionsUsd"], 0)
                self.assertTrue(x["sourceUrl"].startswith("https://"))
                self.assertTrue(x["year"] and x["scope"])
                self.assertTrue(x["definition"] and x["interpretation"])
                self.assertNotEqual(x["confidence"], "")

    def test_defense_methods_not_double_counted(self):
        records = {x["id"]: x for x in self.data["metrics"]}
        self.assertEqual(records["global-defense-iiss-2025"]["valueTrillionsUsd"], 2.63)
        self.assertEqual(records["global-military-sipri-2025"]["valueTrillionsUsd"], 2.887)
        self.assertEqual(records["global-military-sipri-2025"]["measurement"],
                         "annual-flow-alternative")
        self.assertIn('r.measurement!=="annual-flow-alternative"', self.page)

    def test_corrected_healthcare_year_and_projection(self):
        records = {x["id"]: x for x in self.data["metrics"]}
        health = records["us-healthcare-spending-2025"]
        self.assertEqual(health["valueTrillionsUsd"], 5.7)
        self.assertEqual(health["measurement"], "annual-flow-estimate")
        self.assertIn("projected-source-confirmed", health["confidence"])
        self.assertIn("2024", health["interpretation"])
        self.assertIn("healthcare", str(self.data["sourceCorrections"]).lower())

    def test_no_synthetic_zip_specific_costs_or_claimed_causality(self):
        policy = str(self.data["methodology"]).lower()
        self.assertIn("causality", policy)
        self.assertIn("no zip-level causal effect", policy)
        self.assertNotIn("navigator.geolocation", self.page)
        self.assertNotIn("localStorage", self.page)
        self.assertNotIn("this caused your bill", self.page.lower())

    def test_source_graphics_are_linked_and_not_republished(self):
        self.assertEqual(len(self.data["basedOn"]), 3)
        self.assertIn("not reproduced images",
                      self.data["methodology"]["copyrightNote"])
        self.assertGreaterEqual(len(self.data["sourceCorrections"]), 8)

if __name__ == "__main__":
    unittest.main()
