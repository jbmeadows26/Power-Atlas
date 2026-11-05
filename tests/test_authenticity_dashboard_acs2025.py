"""Prevent the political-authenticity dashboard from silently reverting to 2024 ACS."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "site/political-authenticity.js"
DATA = ROOT / "data/research/political-authenticity/acs-2025-age-representation-comparison.json"

class AuthenticityDashboardACS2025Tests(unittest.TestCase):
    def test_dashboard_uses_published_2025_dataset_and_schema(self):
        js = JS.read_text(encoding="utf-8")
        dataset = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertIn("get('acs-2025-age-representation-comparison.json')", js)
        self.assertIn(dataset["schema"], js)
        self.assertNotIn("get('age-comparison.json')", js)
        self.assertNotIn("2024 U.S. resident population aged 25+", js)
    def test_dashboard_binds_real_2025_field_names(self):
        js = JS.read_text(encoding="utf-8")
        dataset = json.loads(DATA.read_text(encoding="utf-8"))
        for key in ("votingHouseMembersAge25to34", "votingHouseMembers",
                    "memberSnapshotDate", "populationAge25to34ShareOf25plus",
                    "memberMinusResidentPercentagePoints", "districts"):
            self.assertIn("a."+key, js)
            self.assertIn(key, dataset)
        self.assertEqual(dataset["districts"],435)
        self.assertEqual(dataset["votingHouseMembers"],433)
        self.assertEqual(dataset["votingHouseMembersAge25to34"],5)
    def test_dashboard_preserves_source_and_caveat(self):
        js = JS.read_text(encoding="utf-8")
        self.assertIn("2025 ACS release", js)
        self.assertIn("eligibility differs", js)
        self.assertIn("no valid respondent-to-member join", js)
        self.assertIn("member wealth", js)

if __name__ == "__main__":
    unittest.main()
