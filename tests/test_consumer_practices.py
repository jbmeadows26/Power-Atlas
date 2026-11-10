"""Offline evidence, navigation and frontend checks for Consumer Watch."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "consumer-practices" / "cases-v1.json"
UNIFIED = ROOT / "platform" / "unified"
SITE = ROOT / "site"
STATUSES = {"terms", "lawsuit", "proposed", "settlement"}


class ConsumerPracticesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.cases = cls.data["cases"]
        cls.main = (UNIFIED / "consumer-practices.html").read_text(encoding="utf-8")
        cls.research = (SITE / "consumer-practices.html").read_text(encoding="utf-8")
        cls.js = (UNIFIED / "consumer-watch-v2.js").read_text(encoding="utf-8")
        cls.css = (UNIFIED / "consumer-watch-v2.css").read_text(encoding="utf-8")

    def test_evidence_schema_and_unique_cases(self):
        d = self.data
        self.assertEqual(d["schema"], "power-atlas.consumer-practices.v1")
        self.assertGreaterEqual(len(self.cases), 18)
        self.assertEqual(len({c["id"] for c in self.cases}), len(self.cases))
        self.assertEqual(len(set(d["industries"])), len(d["industries"]))
        self.assertEqual(set(d["industries"]), {c["industry"] for c in self.cases})
        self.assertGreaterEqual(len(d["industries"]), 12)
        self.assertEqual(set(d["statuses"]), STATUSES)
        self.assertIn("allegations are not proven", d["methodology"]["statusRules"].lower())

    def test_source_status_and_legal_qualifiers(self):
        for c in self.cases:
            with self.subTest(case=c["id"]):
                self.assertIn(c["status"], STATUSES)
                self.assertTrue(c["source"]["url"].startswith("https://"))
                self.assertEqual(c["source"]["kind"], "primary")
                self.assertTrue(c["name"] and c["claim"] and c["implication"] and c["action"])
                self.assertTrue(re.fullmatch(r"20\d\d-\d\d-\d\d", c["eventDate"]))
                if c["status"] != "terms":
                    self.assertIn("ftc.gov", c["source"]["url"])
        t = next(c for c in self.cases if c["id"] == "tmobile")
        self.assertEqual(t["status"], "terms")
        self.assertIn("not been established", t["implication"].lower())
        self.assertEqual(t["relatedPage"], "telecom-promotions.html")
        self.assertTrue((UNIFIED / t["relatedPage"]).is_file())
        h = next(c for c in self.cases if c["id"] == "hopper")
        self.assertEqual(h["status"], "settlement")
        self.assertIn("entered", h["claim"])

    def test_dashboard_preserves_source_labels_and_fail_closed(self):
        for page in (self.main, self.research):
            self.assertIn("power-atlas.consumer-practices.v1", page)
            self.assertIn("raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/", page)
            self.assertIn('id="pcSearch"', page)
            self.assertIn('id="pcIndustry"', page)
            self.assertIn('id="pcEvidence"', page)
            self.assertIn('id="pcCases"', page)
            self.assertIn('id="pcCount"', page)
            self.assertIn('id="pcReset"', page)
            self.assertIn('src="bug-report.js"', page)
            self.assertIn('src="consumer-watch-v2.js"', page)
            self.assertIn('href="consumer-watch-v2.css"', page)
            self.assertIn('id="pcStoryButtons"', page)
            self.assertIn('id="pcPatternGrid"', page)
            self.assertIn('id="pcStoryStages"', page)
            self.assertIn('id="pcStatusOverview"', page)
            self.assertIn("No verdicts by graphic design.", page)
            self.assertIn('class="cw-top" role="region"', page)
            self.assertNotIn('<header class="cw-top">', page)
            self.assertNotIn("localStorage", page)
            self.assertNotIn("sendBeacon", page)
        self.assertIn('href="global-navigation.css"', self.main)
        self.assertIn('data-pa-nav="consumer" aria-current="page"', self.main)
        self.assertIn("No unsourced company findings are displayed", self.js)
        self.assertIn("unexpected evidence schema", self.js)
        self.assertIn("data-story", self.js)
        self.assertIn("data-pattern", self.js)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertEqual(self.js, (SITE / "consumer-watch-v2.js").read_text(encoding="utf-8"))
        self.assertEqual(self.css, (SITE / "consumer-watch-v2.css").read_text(encoding="utf-8"))

    def test_links_and_parent_category(self):
        for directory in (UNIFIED, SITE):
            for name in ("consumer-practices.html", "telecom-promotions.html", "service-accountability.html", "index.html"):
                self.assertTrue((directory / name).is_file(), name)
            self.assertIn('href="consumer-practices.html"', (directory / "index.html").read_text(encoding="utf-8"))
            self.assertIn('href="consumer-practices.html"', (directory / "telecom-promotions.html").read_text(encoding="utf-8"))
        life = (UNIFIED / "my-life.html").read_text(encoding="utf-8")
        self.assertIn('href="consumer-practices.html"', life)
        self.assertIn('id="consumerPracticesCategory"', life)

    def test_cross_industry_cost_comparison(self):
        model = json.loads((ROOT / "data" / "consumer-practices" / "comparison-framework-v1.json").read_text(encoding="utf-8"))
        phone = json.loads((ROOT / "data" / "consumer-practices" / "phone-upgrade-true-cost-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(model["schema"], "power-atlas.consumer-watch.comparison-framework.v1")
        self.assertEqual({c["id"] for c in self.cases}, {s["id"] for s in model["scenarios"]})
        self.assertTrue(all(s["consumerCostModel"]["unknown"] for s in model["scenarios"]))
        self.assertTrue(all(s["source"].startswith("https://") for s in model["scenarios"]))
        self.assertEqual(phone["schema"], "power-atlas.consumer-watch.phone-true-cost.v1")
        self.assertGreaterEqual(len(phone["plans"]), 6)
        for page in (self.main, self.research):
            for text in ('id="cwCompareSelect"', 'id="cwPhoneRows"', 'src="consumer-watch-cost.js"', 'href="consumer-watch-cost.css"'):
                self.assertIn(text, page)
        self.assertEqual((UNIFIED / "consumer-watch-cost.js").read_bytes(), (SITE / "consumer-watch-cost.js").read_bytes())
        self.assertEqual((UNIFIED / "consumer-watch-cost.css").read_bytes(), (SITE / "consumer-watch-cost.css").read_bytes())

    def test_external_javascript_parses_with_node(self):
        if shutil.which("node") is None:
            self.skipTest("Node.js unavailable")
        for directory in (UNIFIED, SITE):
            proc = subprocess.run(
                ["node", "--check", str(directory / "consumer-watch-v2.js")],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            cost = subprocess.run(["node", "--check", str(directory / "consumer-watch-cost.js")], capture_output=True, text=True)
            self.assertEqual(cost.returncode, 0, cost.stderr)


if __name__ == "__main__":
    unittest.main()
