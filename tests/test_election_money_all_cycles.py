"""Regression tests for historical federal election-cycle funding coverage."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MONEY = ROOT / "data" / "money-influence"
HTML = ROOT / "platform" / "unified" / "election-money.html"
HOME = ROOT / "platform" / "unified" / "index.html"


def load(name):
    return json.loads((MONEY / name).read_text(encoding="utf-8"))


class ElectionMoneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load("fec-federal-cycle-overview-2002-2026.json")
        cls.os = load("opensecrets-presidential-donor-excerpts-2020-2024.json")
        cls.brennan = load("brennan-top40-midterms-2014-2026.json")
        cls.rows = cls.summary["cycles"]

    def test_every_even_federal_cycle_2002_to_2026(self):
        self.assertEqual([r["cycle"] for r in self.rows], list(range(2002, 2028, 2)))
        self.assertEqual(len(self.rows), 13)
        for r in self.rows:
            self.assertEqual(r["type"], "presidential" if r["cycle"] % 4 == 0 else "midterm")
            self.assertGreater(r["congressionalReceipts18M"], 0)
            self.assertTrue(r["congressionalSource18"].startswith("https://www.fec.gov/"))

    def test_reporting_windows_are_not_mixed(self):
        for r in self.rows:
            if r["cycle"] == 2026:
                self.assertIsNone(r["congressionalReceipts24M"])
                self.assertIsNone(r["independentExpenditures24M"])
                self.assertEqual(r["congressionalReceipts18M"], 2799.1)
                self.assertEqual(r["pacReceipts18M"], 8307.4)
            else:
                self.assertIsNotNone(r["congressionalReceipts24M"])
                self.assertGreater(r["congressionalReceipts24M"], 0)

    def test_published_presidential_receipts(self):
        amounts = {r["cycle"]: r["presidentialReceipts24M"] for r in self.rows}
        self.assertEqual(amounts[2016], 1539.1)
        self.assertEqual(amounts[2020], 4073.9)
        self.assertEqual(amounts[2024], 2012.0)
        self.assertIsNone(amounts[2022])

    def test_historical_spending_and_source_flags(self):
        source = self.summary["sourceDictionary"]
        self.assertTrue(all(url.startswith("https://www.fec.gov/") for url in source.values()))
        self.assertEqual(self.rows[-1]["coverage"], "partial_18mo")
        self.assertTrue(self.summary["completeness"])
        self.assertTrue(all(r["congressionalReceipts18M"] > 0 for r in self.rows))

    def test_donor_coverage_does_not_pretend_equal_completeness(self):
        self.assertEqual(len(self.brennan["records"]), 160)
        self.assertEqual(len(self.os["donors"]), 18)
        self.assertEqual(sum(r["cycle"] == 2020 for r in self.os["donors"]), 7)
        self.assertEqual(sum(r["cycle"] == 2024 for r in self.os["donors"]), 11)
        for row in self.os["donors"]:
            self.assertIsNone(row["darkMoney"])
        self.assertTrue(all(r["amountUsd"] > 0 for r in self.os["donors"]))

    def test_visualization_and_home_navigation(self):
        page = HTML.read_text(encoding="utf-8")
        home = HOME.read_text(encoding="utf-8")
        self.assertIn("congressTrend", page)
        self.assertIn("presTrend", page)
        self.assertIn("donorRows", page)
        self.assertIn("2026", page)
        self.assertIn("election-money.html", home)
        self.assertIn("No ranked donor list ingested", page)


if __name__ == "__main__":
    unittest.main()
