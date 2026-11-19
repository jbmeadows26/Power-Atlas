"""Offline regression guards for reference-first evidence integrity.

Run: python -m unittest discover -s tests -p 'test_reference_evidence_integrity.py'
No network, external credentials, or personal information.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ReferenceEvidenceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = read("data/health/reference-gap-progress-v1.json")
        cls.cases = read("data/health/reference-first-evidence-cases-v1.json")
        cls.index = read("platform/unified/data/source-reference-index-v1.json")

    def test_reference_mode_never_implies_ingestion(self):
        self.assertEqual(self.index["activeMode"], "reference")
        self.assertTrue(self.index["integrityPolicy"]["noImplicitGapClosure"])
        self.assertTrue(self.index["integrityPolicy"]["publicLinkNotEqualToVerifiedEvidence"])
        self.assertTrue(self.index["integrityPolicy"]["zipAndUserIdentityNotPersisted"])
        for source in self.index["sources"]:
            self.assertEqual(source["retrievalStatus"], "source_entry_point_identified_not_evidence_ingested")
            self.assertIn(source["authority"], ("official", "secondary_mirror"))

    def test_ledger_counts_match_rows(self):
        scope = self.ledger["scope"]
        rows = self.ledger["gaps"]
        self.assertEqual(len(rows), scope["openTotal"])
        self.assertEqual(sum(row["category"] == "local" for row in rows), scope["localGapCount"])
        self.assertEqual(sum(row["category"] == "national" for row in rows), scope["nationalBlockingGateCount"])
        self.assertEqual(scope["fullGapClosures"], 0)
        self.assertTrue(all(row["originalGateClosed"] is False for row in rows))

    def test_bounded_cases_have_provenance_and_do_not_close_gates(self):
        cases = self.cases["cases"]
        self.assertEqual(len(cases), self.ledger["scope"]["boundedEvidenceCasesReviewed"])
        case_ids = [case["id"] for case in cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        ledger_ids = {row["gapId"] for row in self.ledger["gaps"]}
        for case in cases:
            self.assertIs(case["originalGapClosureAllowed"], False)
            self.assertTrue(case["sourceDocuments"])
            self.assertTrue(case["checks"])
            self.assertTrue(case["limits"])
            for source in case["sourceDocuments"]:
                self.assertTrue(source["authority"])
                self.assertTrue(source["url"].startswith("https://"))
                self.assertIn("sha256", source)
            for gap_id in case["relatedLocalGapIds"] + case["relatedNationalGateIds"]:
                self.assertIn(gap_id, ledger_ids)
                row = next(row for row in self.ledger["gaps"] if row["gapId"] == gap_id)
                self.assertIn(case["id"], row["boundedCaseIds"])


if __name__ == "__main__":
    unittest.main()
