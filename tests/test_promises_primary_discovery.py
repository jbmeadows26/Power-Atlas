"""Fail-closed checks for additive source discovery (NOT factual adjudication)."""
import datetime as dt
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data/promises/primary-crossnational-discovery-2026-10-30.json"

class PrimaryDiscoveryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_no_published_population_rate_or_causal_claim(self):
        d = self.data
        self.assertFalse(d["denominatorFrozen"])
        self.assertFalse(d["sourceScopeComplete"])
        self.assertIsNone(d["eligiblePopulationCount"])
        self.assertIsNone(d["fulfillmentRate"])
        self.assertIsNone(d["causalEffect"])
        self.assertEqual(d["adjudicatedPledgeCount"], 0)

    def test_primary_documents_precede_elections(self):
        docs = self.data["sourceDocuments"]
        self.assertEqual(len({d["id"] for d in docs}), len(docs))
        self.assertEqual({d["country"] for d in docs}, {"US", "UK", "CA", "DE", "PT"})
        for d in docs:
            with self.subTest(d["id"]):
                self.assertLess(dt.date.fromisoformat(d["published"]), dt.date.fromisoformat(d["electionDate"]))
                self.assertEqual(urlsplit(d["url"]).scheme, "https")
                self.assertTrue(d["license"])
                self.assertTrue(d["locator"])
                self.assertTrue(d["notes"])

    def test_all_candidates_unscored_and_source_linked(self):
        d = self.data
        docs = {s["id"]: s for s in d["sourceDocuments"]}
        events = {e["id"] for e in d["officialEvents"]}
        rows = d["candidatePledges"]
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        self.assertGreaterEqual(len(rows), 10)
        for r in rows:
            with self.subTest(r["id"]):
                self.assertIn(r["documentId"], docs)
                self.assertIsNone(r["outcome"])
                self.assertEqual(r["independentReviewers"], 0)
                self.assertFalse(r["independentAdjudication"])
                self.assertEqual(r["eligibility"], "candidate_requires_independent_atomization")
                self.assertTrue(r["successCriterion"])
                self.assertTrue(r["locator"])
                self.assertTrue(set(r["linkedOfficialEventIds"]) <= events)

    def test_events_not_spending_or_enactment_proxies(self):
        rows = self.data["officialEvents"]
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        for r in rows:
            with self.subTest(r["id"]):
                dt.date.fromisoformat(r["date"])
                self.assertEqual(urlsplit(r["url"]).scheme, "https")
                self.assertTrue(r["notProofOf"])
                self.assertTrue(r["locator"])
        self.assertEqual(
            {e["id"] for e in rows if e["kind"] == "enacted_statute_unlinked_2020"},
            {"US21-PL11758", "US22-PL117167", "US22-PL117169"}
        )
        linked = {e for p in self.data["candidatePledges"] for e in p["linkedOfficialEventIds"]}
        self.assertFalse(linked & {"US21-PL11758", "US22-PL117167", "US22-PL117169"})

    def test_fiscal_discovery_not_passed_off_as_observations(self):
        for s in self.data["fiscalSourceDiscovery"]:
            self.assertEqual(s["status"], "source_verified_no_new_records_ingested")
            self.assertTrue(s["warning"])
            self.assertEqual(urlsplit(s["url"]).scheme, "https")

if __name__ == "__main__":
    unittest.main()
