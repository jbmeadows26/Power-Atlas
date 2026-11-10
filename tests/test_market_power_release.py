"""Production release checks for the market-power visual atlas."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "platform" / "unified"
SITE = ROOT / "site"
DATA = ROOT / "data"

class MarketPowerReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.market = json.loads((DATA / "market-power" / "evidence-v1.json").read_text(encoding="utf-8"))
        cls.bridge = json.loads((UNIFIED / "household-market-bridge.json").read_text(encoding="utf-8"))
        cls.money = json.loads((UNIFIED / "money-scale.json").read_text(encoding="utf-8"))

    def test_evidence_provenance_and_legal_classification(self):
        self.assertEqual(self.market["schema"], "power-atlas.market-power.v1")
        self.assertEqual(self.market["publication"], "production")
        ids = [c["id"] for c in self.market["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 12)
        kinds = {c["kind"] for c in self.market["cases"]}
        self.assertTrue({"measured", "finding", "allegation", "context"}.issubset(kinds))
        for c in self.market["cases"]:
            self.assertTrue(c["source"].startswith("https://"), c["id"])
            for k in ("scope", "mechanism", "benefits", "costs", "status", "period", "metricLabel"):
                self.assertTrue(c[k], (c["id"], k))
        amazon = next(c for c in self.market["cases"] if c["id"] == "amazon")
        self.assertIn("ftc-sues-amazon-illegally-maintaining-monopoly-power", amazon["source"])
        self.assertEqual(amazon["kind"], "allegation")
        pbm = next(c for c in self.market["cases"] if c["id"] == "pbms")
        self.assertIn("2025/01/ftc-releases-second-interim", pbm["supportingSources"][0]["url"])

    def test_data_copies_match(self):
        for root in (SITE, UNIFIED):
            self.assertEqual(self.market, json.loads((root / "market-power.json").read_text(encoding="utf-8")))
            self.assertEqual(self.bridge, json.loads((root / "household-market-bridge.json").read_text(encoding="utf-8")))
            self.assertEqual(self.money, json.loads((root / "money-scale.json").read_text(encoding="utf-8")))
        self.assertEqual(self.money, json.loads((SITE / "data" / "money-scale-v1.json").read_text(encoding="utf-8")))

    def test_household_claims_not_fabricated(self):
        self.assertEqual(self.bridge["publicationStatus"], "published")
        self.assertEqual(self.money["status"], "published")
        self.assertEqual(self.bridge["baseline"]["totalExpenditureUsd"], 81905)
        self.assertEqual(self.bridge["incomeExample"]["annualUsd"], 110847)
        cases = {c["id"] for c in self.market["cases"]}
        for item in self.bridge["categories"]:
            self.assertGreater(item["annualUsd"], 0)
            self.assertTrue(item["unresolved"])
            self.assertTrue(set(item["caseIds"]).issubset(cases))
        low = json.dumps(self.bridge).lower()
        self.assertIn("no nationwide, zip-level or individual-household causal estimate", low)
        self.assertIn("housing includes utilities", low)
        self.assertNotIn("monopoly_overcharge_usd", low)
        self.assertNotIn("estimated_surcharge", low)

    def test_public_pages_live_and_connected(self):
        for root in (SITE, UNIFIED):
            market = (root / "market-power.html").read_text(encoding="utf-8")
            money = (root / "money-scale.html").read_text(encoding="utf-8")
            for page in (market, money):
                self.assertNotIn("NOT PUBLISHED", page)
                self.assertNotIn('content="noindex,nofollow"', page)
                self.assertIn('content="index,follow"', page)
            self.assertIn('id="caseMenu"', market)
            self.assertIn('id="marketBars"', market)
            self.assertIn('id="household-bridge"', market)
            self.assertIn('src="market-power-household.js"', market)
            self.assertIn("URLSearchParams", market)
            self.assertIn("supportingSources", market)
            self.assertIn('fetch("./market-power.json"', market)
            self.assertIn('fetch("money-scale.json"', money)
            home = (root / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="market-power.html"', home)
            self.assertIn("atlas-visual-system.js", home)
            consumer = (root / "consumer-practices.html").read_text(encoding="utf-8")
            self.assertIn('href="market-power.html"', consumer)
            # Public navigation is authoritative; the optional redesign proof page may not yet ship.
            preview = root / "redesign-preview.html"
            if preview.exists():
                redesign = preview.read_text(encoding="utf-8")
                self.assertIn('id="market-power"', redesign)
                self.assertIn('href="market-power.html#household-bridge"', redesign)
            for file in ("market-power-household.css", "market-power-household.js", "market-power.json", "household-market-bridge.json"):
                self.assertTrue((root / file).exists(), (root, file))

    def test_research_methodology_documented(self):
        method = (ROOT / "research" / "market-power" / "README.md").read_text(encoding="utf-8")
        for token in ("causal", "antitrust", "Geography", "monopsony"):
            self.assertIn(token.lower(), method.lower())

if __name__ == "__main__":
    unittest.main()
