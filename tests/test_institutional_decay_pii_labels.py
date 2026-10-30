"""Verify official metadata labels match OECD PII raw measure codes."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/institutional-decay/oecd-pii-raw-2020-2025.json"
LABELS=ROOT/"data/institutional-decay/oecd-pii-measure-labels.json"


class OECDPIILabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=json.loads(RAW.read_text(encoding="utf-8"))
        cls.labels=json.loads(LABELS.read_text(encoding="utf-8"))

    def test_official_metadata_coverage(self):
        expected={r["measureCode"] for r in self.raw["rows"]}
        found={r["code"] for r in self.labels["measureLabels"]}
        self.assertEqual(len(expected),44)
        self.assertEqual(expected,found)
        self.assertEqual(self.labels["coverage"]["missingCodeCount"],0)
        self.assertEqual(self.labels["coverage"]["labeledCount"],44)
        self.assertEqual(self.labels["status"],"fully_labeled")

    def test_no_inferred_definitions(self):
        for row in self.labels["measureLabels"]:
            self.assertTrue(row["englishLabel"].strip())
            self.assertEqual(row["codelistId"],"CL_MEASURE")
            self.assertTrue(row["code"].startswith("PII_"))
        self.assertIn("sdmx.oecd.org",self.labels["source"])
        self.assertTrue(any("not measures of illegal conduct" in s for s in
                            self.labels["limitations"]))

    def test_raw_values_preserved_independently(self):
        groups={}
        for row in self.raw["rows"]:
            groups[row["valueKind"]]=groups.get(row["valueKind"],0)+1
        self.assertEqual(groups["numeric"],2418)
        self.assertEqual(groups["reported_fraction"],1640)
        self.assertEqual(groups["source_missing"],1718)
        self.assertEqual(sum(groups.values()),5776)


if __name__=="__main__":
    unittest.main()
