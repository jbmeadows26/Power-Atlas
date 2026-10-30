"""Coverage scaffold checks: unknown must never be misreported as current law."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "data/voting-access/state-policy-coverage-v1.json"
EXPECTED = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())

class StatePolicyCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DOC.read_text(encoding="utf-8"))
    def test_all_jurisdictions_unique_and_complete(self):
        got = [x["id"].removeprefix("US-") for x in self.doc["jurisdictions"]]
        self.assertEqual(len(got), 51)
        self.assertEqual(set(got), EXPECTED)
    def test_truthful_coverage_status(self):
        self.assertEqual(self.doc["verifiedRuleCount"], 0)
        self.assertEqual(self.doc["publicationStatus"], "coverage_scaffold_not_current_law")
        topics = set(next(iter(self.doc["jurisdictions"]))["topics"])
        self.assertEqual(len(topics), self.doc["topicCount"])
        for row in self.doc["jurisdictions"]:
            self.assertEqual(set(row["topics"]), topics)
            self.assertEqual(row["verificationStatus"], "not_yet_verified")
            for policy in row["topics"].values():
                self.assertEqual(policy["status"], "not_yet_verified")
                self.assertIsNone(policy["rule"])
                self.assertIsNone(policy["effectiveDate"])
                self.assertIsNone(policy["officialSource"])

if __name__ == "__main__":
    unittest.main()
