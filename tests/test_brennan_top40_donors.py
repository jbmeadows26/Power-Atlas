"""Validate the externally sourced top-40 midterm donor reference snapshot."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/money-influence/brennan-top40-midterms-2014-2026.json"
FRONTEND_PATH = ROOT / "platform/unified/donor-intelligence.html"
INDEX_PATH = ROOT / "platform/unified/index.html"


class BrennanTop40DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.records = cls.dataset["records"]

    def test_four_full_midterm_cycles(self):
        self.assertEqual(len(self.records), 160)
        for year in (2014, 2018, 2022, 2026):
            rows = [r for r in self.records if r["cycle"] == year]
            self.assertEqual(len(rows), 40, f"Missing donors in {year}")
            self.assertEqual(sorted(r["rank"] for r in rows), list(range(1, 41)))

    def test_no_silent_party_or_money_recoding(self):
        for row in self.records:
            self.assertTrue(row["donor"])
            self.assertGreater(row["amountUsd"], 0)
            self.assertIsInstance(row["darkMoney"], bool)
            self.assertIn(row["partySupported"], {"Republican", "Democratic", "Both parties"})
            self.assertTrue(row["sector"])

    def test_reference_totals(self):
        rows = [r for r in self.records if r["cycle"] == 2026]
        self.assertAlmostEqual(sum(r["amountUsd"] for r in rows), 2430975074.4, delta=2)
        self.assertAlmostEqual(sum(r["amountUsd"] for r in rows if r["darkMoney"]), 699323262.77, delta=3)
        self.assertEqual(rows[0]["donor"], "Elon Musk and United States of America Inc.")
        self.assertEqual(rows[0]["amountUsd"], 483255336)

    def test_provenance_and_limitations(self):
        self.assertEqual(self.dataset["sourceArticleUpdated"], "2026-10-29")
        self.assertIn("brennancenter.org", self.dataset["sourceArticle"])
        self.assertIn("zhangj-brennan", self.dataset["originalData"])
        self.assertGreaterEqual(len(self.dataset["interpretationWarnings"]), 3)
        self.assertIn("nominal", self.dataset["amounts"])

    def test_frontend_navigation(self):
        page = FRONTEND_PATH.read_text(encoding="utf-8")
        home = INDEX_PATH.read_text(encoding="utf-8")
        self.assertIn("brennan-top40-midterms-2014-2026.json", page)
        self.assertIn("donor-intelligence.html", home)
        self.assertIn("darkFilter", page)
        self.assertIn("partyFilter", page)
        self.assertIn("sectorFilter", page)


if __name__ == "__main__":
    unittest.main()
