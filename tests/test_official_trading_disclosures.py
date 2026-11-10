"""Validation of source-attributed public official trading disclosure research."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/public-integrity/official-trading-2025-2026-v1.json"
MIRROR = ROOT / "platform/unified/official-trading-data-v1.json"
PAGE = ROOT / "platform/unified/public-trading.html"

class OfficialTradingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.page = PAGE.read_text(encoding="utf-8")

    def test_deploy_data_matches_corpus(self):
        self.assertEqual(self.data, json.loads(MIRROR.read_text(encoding="utf-8")))
        self.assertEqual(self.data["schema"], "power-atlas.public-official-trading.v1")
        self.assertIn("not_independently_reconciled", self.data["sourceStatus"])

    def test_source_months_reconcile(self):
        rows = self.data["monthly"]
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]["month"], "2025-01")
        self.assertEqual(rows[-1]["month"], "2026-08")
        self.assertEqual([sum(row[k] for row in rows) for k in ("trumpAccounts", "congress")], [31877, 20973])
        self.assertEqual(sum(x["trumpAccounts"] > x["congress"] for x in rows), 16)
        self.assertEqual(self.data["comparison"]["difference"], 10904)
        self.assertAlmostEqual((31877 / 20973 - 1) * 100, 52.0, places=1)
        self.assertTrue(self.data["comparisonPeriod"]["finalMonthPotentiallyIncomplete"])

    def test_notional_range_not_misrepresented(self):
        tr,co = self.data["groups"]
        self.assertEqual(tr["notionalUsdRange"], [1600000000, 5200000000])
        self.assertEqual(co["notionalUsdRange"], [600000000, 1800000000])
        self.assertLessEqual(tr["notionalUsdRange"][0], co["notionalUsdRange"][1])
        self.assertEqual(self.data["researchScope"]["stage"], "descriptive_baseline_only")

    def test_ticker_view_is_separate_period(self):
        stocks = self.data["stockCoverage"]
        self.assertEqual((stocks["start"], stocks["end"]), ("2026-01", "2026-05"))
        self.assertEqual(stocks["distinctTickersReported"], 746)
        self.assertEqual(len(stocks["topTen"]), 10)
        self.assertEqual(stocks["topTen"][0]["purchases"] + stocks["topTen"][0]["sales"], 37)

    def test_provenance_contains_primary_originals(self):
        sources = {x["type"]: [] for x in self.data["sources"]}
        for source in self.data["sources"]:
            sources[source["type"]].append(source["url"])
        self.assertEqual(len(sources["primary"]), 3)
        self.assertTrue(any("kadoa.com/congress/insights" in u for u in sources["aggregation"]))
        self.assertTrue(any("reddit.com" in u for u in sources["social_illustration"]))
        guards = " ".join(self.data["interpretiveGuards"]).lower()
        for concern in ("third-party", "filings", "profit", "insider trading", "consumer-price effects"):
            self.assertIn(concern.replace("third-party", "white house") if concern == "third-party" else concern, guards)

    def test_review_dashboard_accessible_and_navigable(self):
        for token in ("id=\"chart\"", "id=\"selection\"", "aria-label", "aria-pressed", "role=\"status\"",
                      "official-trading-data-v1.json", "data-period=\"2025\"", "data-period=\"2026\"",
                      "sourceList", "bug-report.js"):
            self.assertIn(token, self.page)
        for path in ("platform/unified/index.html", "platform/unified/donor-intelligence.html", "platform/unified/my-life.html"):
            self.assertIn('href="public-trading.html"', (ROOT / path).read_text(encoding="utf-8"))
        self.assertNotIn("proved insider trading", self.page.lower())

if __name__ == "__main__":
    unittest.main()
