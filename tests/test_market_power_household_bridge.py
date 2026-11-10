"""Source and UI guardrails for review-only money-scale → household market-power bridge."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "platform" / "unified"
SCALE_SITE = ROOT / "site" / "data" / "money-scale-v1.json"
SCALE_UNIFIED = UNIFIED / "money-scale.json"
MARKET = UNIFIED / "market-power.json"
BRIDGE = UNIFIED / "household-market-bridge.json"
BENCH = ROOT / "data" / "place-impact" / "cost-benchmark-drivers-v1.json"

class MarketPowerHouseholdBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
        cls.market = json.loads(MARKET.read_text(encoding="utf-8"))
        cls.bench = json.loads(BENCH.read_text(encoding="utf-8"))
        cls.money = json.loads(SCALE_UNIFIED.read_text(encoding="utf-8"))
        cls.market_page = (UNIFIED / "market-power.html").read_text(encoding="utf-8")
        cls.money_page = (UNIFIED / "money-scale.html").read_text(encoding="utf-8")
        cls.script = (UNIFIED / "market-power-household.js").read_text(encoding="utf-8")

    def test_review_separation_and_source_parity(self):
        self.assertEqual(self.bridge["publicationStatus"], "review-only")
        self.assertEqual(self.money["status"], "review-only")
        self.assertEqual(self.money, json.loads(SCALE_SITE.read_text(encoding="utf-8")))
        self.assertIn("NOT PUBLISHED", self.market_page)
        self.assertIn('name="robots" content="noindex,nofollow"', self.money_page)
        self.assertIn('fetch("money-scale.json"', self.money_page)

    def test_spending_values_identical_to_bls_evidence(self):
        rows = {c["id"]: c for c in self.bridge["categories"]}
        mappings = {"housing":"housing","transport":"transport","groceries":"groceries","health":"health"}
        self.assertEqual(set(rows), set(mappings))
        for key, topic in mappings.items():
            with self.subTest(category=key):
                baseline = self.bench["topics"][topic]["headline"]
                self.assertEqual(rows[key]["annualUsd"], baseline["annual"])
                self.assertEqual(rows[key]["priorUsd"], baseline["prior"])
                self.assertEqual(rows[key]["year"], 2025)
                self.assertGreater(rows[key]["annualUsd"], 0)
                self.assertTrue(rows[key]["coverage"])
                self.assertTrue(rows[key]["unresolved"])
        self.assertEqual(self.bridge["baseline"]["totalExpenditureUsd"], 81905)
        self.assertEqual(self.bridge["incomeExample"]["annualUsd"], self.bench["topics"]["work"]["headline"]["annual"])
        self.assertIn("2025", self.bridge["baseline"]["period"])
        self.assertIn("bls.gov", self.bridge["baseline"]["sourceUrl"])

    def test_market_cases_exist_and_are_fully_linked(self):
        registered = {c["id"]:c for c in self.market["cases"]}
        self.assertGreaterEqual(len(registered), 12)
        for c in self.bridge["categories"]:
            self.assertTrue(c["caseIds"])
            for case_id in c["caseIds"]:
                with self.subTest(category=c["id"], case=case_id):
                    self.assertIn(case_id, registered)
                    self.assertTrue(registered[case_id]["source"].startswith("https://"))
                    self.assertTrue(registered[case_id]["kind"])
        self.assertIn("jobs", registered)
        self.assertEqual(self.bridge["incomeExample"]["caseIds"], ["jobs"])

    def test_no_estimated_monopoly_household_surcharge(self):
        serialized = json.dumps(self.bridge).lower()
        self.assertIn("not estimates of monopoly overcharges", serialized)
        self.assertIn("no nationwide, zip-level or individual-household causal estimate", serialized)
        self.assertNotIn('"monopoly_overcharge_usd"', serialized)
        self.assertNotIn('"estimated_surcharge"', serialized)
        self.assertNotIn("this caused your bill", serialized)
        self.assertIn("housing includes utilities", serialized)
        self.assertIn("food-at-home", serialized)

    def test_interactive_exploration_is_connected(self):
        self.assertIn('id="household-bridge"', self.market_page)
        self.assertIn('id="hbBars"', self.market_page)
        self.assertIn('id="hbDetail"', self.market_page)
        self.assertIn('src="market-power-household.js"', self.market_page)
        self.assertIn("household-market-bridge.json", self.script)
        self.assertIn("market-power.json", self.script)
        self.assertIn('addEventListener("click"', self.script)
        self.assertIn("button.dataset.category", self.script)
        self.assertIn("button.setAttribute", self.script)
        self.assertIn("case=", self.script)
        self.assertIn("URLSearchParams", self.market_page)
        self.assertIn('href="money-scale.html"', self.market_page)

    def test_money_scale_explains_distinct_measures(self):
        types = {m["measurement"] for m in self.money["metrics"]}
        self.assertGreaterEqual(len(self.money["metrics"]), 12)
        self.assertTrue({"asset-stock","liability-stock","annual-output","annual-flow"}.issubset(types))
        self.assertIn('data-group="annual-output"', self.money_page)
        self.assertIn("money-scale.json", self.money_page)
        self.assertIn("market-power.html#household-bridge", self.money_page)

if __name__ == "__main__":
    unittest.main()
