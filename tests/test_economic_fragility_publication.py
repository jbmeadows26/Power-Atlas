"""Validate the published economic fragility page and its Power Atlas entrypoints."""
import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "site/data/economic-fragility/2027-v1.json"
PAGE = BASE / "site/economic-fragility.html"
RESEARCH = BASE / "site/index.html"
UNIFIED = BASE / "platform/unified/index.html"
EVERYDAY = BASE / "platform/unified/my-life.html"

class EconomicFragilityPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(DATA.read_text(encoding="utf-8"))
        cls.p = PAGE.read_text(encoding="utf-8")
        cls.research = RESEARCH.read_text(encoding="utf-8")
        cls.unified = UNIFIED.read_text(encoding="utf-8")
        cls.everyday = EVERYDAY.read_text(encoding="utf-8")

    def test_source_snapshot_is_explicit_and_approved(self):
        d = self.d
        self.assertEqual(d["schema"], "power-atlas.economic-fragility.v1")
        self.assertEqual(d["publicationStatus"], "published")
        self.assertTrue(d["publicationApproval"])
        self.assertEqual(d["asOf"], "2026-11-09")
        self.assertEqual(len(d["metrics"]), 5)
        self.assertEqual(len(d["pathways"]), 3)
        for m in d["metrics"]:
            self.assertTrue(m["source"].startswith("https://"))
            self.assertTrue(m["period"])
            self.assertIn(m["direction"], {"stress", "resilience", "mixed"})
        self.assertIn("not a", d["method"].lower() + " " + " ".join(d["evidenceRules"]).lower())

    def test_production_page_and_data_route(self):
        self.assertIn("The Fragile Economy | Power Atlas", self.p)
        self.assertIn('fetch("./data/economic-fragility/2027-v1.json"', self.p)
        self.assertIn('publicationStatus!=="published"', self.p)
        self.assertNotIn('noindex,nofollow', self.p)
        self.assertNotIn('UNPUBLISHED · REVIEW DRAFT', self.p)
        self.assertNotIn("Review branch only", self.p)
        self.assertIn("Nov", self.p)
        self.assertNotIn("navigator.geolocation", self.p)
        self.assertNotIn("localStorage", self.p)

    def test_navigation_staged_in_everyday_and_research_entrypoints(self):
        self.assertIn('href="economic-fragility.html"', self.research)
        url="economic-fragility.html"
        self.assertIn('href="'+url+'"', self.unified)
        self.assertIn('href="'+url+'"', self.everyday)
        self.assertTrue((BASE / "platform/unified/economic-fragility.html").is_file())

    def test_evidence_categories_cannot_be_added(self):
        f = self.d["financing"]
        self.assertEqual({x["id"]:x["billions"] for x in f["items"]},
                         {"revenue":1400, "debt":650, "equity":300})
        self.assertIn("neither realized losses", f["interpretation"])
        self.assertTrue(all(p["status"]=="scenario_not_forecast" for p in self.d["pathways"]))
        self.assertIn("ZIP", " ".join(self.d["evidenceRules"]))

if __name__=="__main__":
    unittest.main()
