"""Checks that the Voting Access seed is evidence-gated and mechanically sound."""
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "voting-access" / "evidence-seed-v1.json"


class VotingAccessEvidenceSeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DATA.read_text(encoding="utf-8"))

    def test_contract_and_counts(self):
        self.assertEqual(self.doc["schema"], "power-atlas.voting-access.seed.v1")
        self.assertEqual(self.doc["publicationStatus"], "historical_source_index_not_comprehensive_state_law_coverage")
        self.assertEqual(self.doc["count"], len(self.doc["records"]))
        self.assertGreaterEqual(self.doc["count"], 8)

    def test_every_fact_is_source_attributed_and_dated(self):
        ids = []
        allowed_types = {"legal_precedent", "research_estimate"}
        for rec in self.doc["records"]:
            ids.append(rec["id"])
            self.assertIn(rec["type"], allowed_types)
            self.assertIsInstance(rec["year"], int)
            self.assertLessEqual(rec["year"], 2026)
            self.assertGreaterEqual(rec["year"], 1960)
            self.assertEqual(urlparse(rec["source"]).scheme, "https")
            self.assertTrue(urlparse(rec["source"]).netloc)
            for key in ("finding", "jurisdiction", "topic", "confidence", "reviewStatus"):
                self.assertTrue(rec.get(key), (rec["id"], key))
            self.assertNotIn("current_state_law_verified", rec["reviewStatus"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_historical_statistics_cannot_be_misread_as_live(self):
        for rec in self.doc["records"]:
            if rec["type"] == "research_estimate":
                self.assertIn("historical", rec["reviewStatus"])
                self.assertLess(rec["year"], 2026)


if __name__ == "__main__":
    unittest.main()
