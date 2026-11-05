"""Civic power reform catalog, current-law boundary, UI and privacy checks."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/money-influence/civic-power-reforms-v1.json"
PAGE = ROOT / "platform/unified/reform-lab.html"
HOME = ROOT / "platform/unified/index.html"
DARK = ROOT / "platform/unified/dark-money.html"

class CivicPowerReformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_schema_and_complete_16_reforms(self):
        data = self.catalog
        self.assertEqual(data["schema"], "power-atlas.civic-power-reforms.v1")
        self.assertEqual(data["recordType"], "policy_proposals_not_current_federal_law")
        self.assertEqual(len(data["records"]), 16)
        self.assertEqual(len(data["pillars"]), 4)
        self.assertEqual({p["id"] for p in data["pillars"]},
                         {"transparency", "structural", "citizen", "integrity"})
        self.assertEqual({r["pillar"] for r in data["records"]},
                         {p["id"] for p in data["pillars"]})
        self.assertEqual(len({r["id"] for r in data["records"]}), 16)
        for pillar in {p["id"] for p in data["pillars"]}:
            self.assertEqual(sum(r["pillar"] == pillar for r in data["records"]), 4)

    def test_cards_have_balanced_factual_fields(self):
        required = {"id", "pillar", "title", "short", "route", "baseline", "proposal",
                    "benefit", "tradeoff", "measure", "source"}
        for record in self.catalog["records"]:
            self.assertTrue(required.issubset(record), record.get("id"))
            for key in required:
                self.assertTrue(isinstance(record[key], str) and record[key].strip(),
                                (record["id"], key))
            self.assertTrue(record["source"].startswith("https://"), record["id"])
        self.assertEqual(len({r["source"] for r in self.catalog["records"]}), 16)

    def test_sensitive_claims_are_qualified(self):
        reform = {r["id"]: r for r in self.catalog["records"]}
        self.assertIn("not publicly disclose", reform["beneficial-ownership"]["baseline"])
        self.assertIn("not prove coordination", reform["coordination"]["baseline"])
        self.assertIn("Supreme Court", reform["spending-amendment"]["baseline"])
        self.assertIn("six commissioners", reform["fec-reform"]["baseline"])
        self.assertIn("New York City", reform["matching"]["baseline"])
        self.assertIn("Seattle", reform["vouchers"]["baseline"])

    def test_dashboard_is_interactive_and_mobile_safe(self):
        for expected in ['name="viewport"', 'id="reformList"', 'id="pillars"',
                         'id="search"', 'id="donation"', 'data-ratio="6"',
                         'data-ratio="8"', 'function updateCalc()', 'gift*ratio',
                         'aria-pressed', 'data-pillar="all"', 'policy_proposals_not_current_federal_law']:
            # recordType is only present in the linked JSON catalog, not page HTML
            if expected == "policy_proposals_not_current_federal_law":
                continue
            self.assertIn(expected, self.html)
        self.assertIn("not automatically proof of influence", self.html)
        self.assertIn("not a universal 24-hour rule", self.html)
        self.assertIn("Most nonprofit donor Schedule B identities are not public", self.html)

    def test_home_and_dark_money_navigation(self):
        self.assertIn('href="reform-lab.html"', HOME.read_text(encoding="utf-8"))
        self.assertIn('href="reform-lab.html"', DARK.read_text(encoding="utf-8"))
        self.assertIn('href="dark-money.html"', self.html)
        self.assertIn("civic-power-reforms-v1.json", self.html)
        self.assertNotIn("verifiedOriginalDonorAttributions: 1", self.html)


if __name__ == "__main__":
    unittest.main()
