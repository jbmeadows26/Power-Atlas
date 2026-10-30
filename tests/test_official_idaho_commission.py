"""Commission redistricting plans are not state legislative bill candidates."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IdahoCommissionEvidenceChecks(unittest.TestCase):
    def test_commission_plans_are_separate_from_zero_hit_bill_index(self):
        doc = json.loads((ROOT / "data/legislation/official-idaho-commission-redistricting-2021.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((ROOT / "data/legislation/state-redistricting-jurisdictions.json").read_text(encoding="utf-8"))
        bills = json.loads((ROOT / "data/legislation/state-redistricting-bills.json").read_text(encoding="utf-8"))
        feed = json.loads((ROOT / "data/app-feed.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["jurisdiction"], "ID")
        self.assertEqual(checkpoint["jurisdictions"]["ID"]["totalMatchesReported"], 0)
        self.assertEqual(checkpoint["jurisdictions"]["ID"]["persistedCandidateRows"], 0)
        self.assertFalse(any(r["state"] == "ID" for r in bills["records"]))
        rows = doc["records"]
        self.assertEqual({r["plan"]: r["districts"] for r in rows}, {"C03": 2, "L03": 35})
        self.assertEqual(feed["legislation"]["officialIdahoCommissionPlans"]["records"], rows)
        self.assertEqual(feed["coverage"]["officialIdahoCommissionPlanRows"], len(rows))
        self.assertEqual(feed["legislation"]["officialIdahoCommissionPlans"]["keywordIndexBillCandidateRows"], 0)
        for row in rows:
            self.assertTrue(row["source"].startswith("https://sos.idaho.gov/"))
            self.assertEqual(row["voteTalliesStatus"], "not_independently_transcribed_from_official_rollcall")
            self.assertIn("spotcheck", row["reviewStatus"])
            self.assertNotIn("contributor_name", row)
            self.assertNotIn("contributor_address", row)


if __name__ == "__main__":
    unittest.main()
