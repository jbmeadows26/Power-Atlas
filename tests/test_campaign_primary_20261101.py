"""Structural and inference-safety checks for 2026-11-01 campaign evidence.

These tests cannot establish primary-source truth or independent adjudication.
"""
import datetime as dt
import json
import pathlib
import unittest
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "promises"
LEDGER = DATA / "primary-medicare-tax-mts-2026-11-01.json"


class CampaignPrimaryNov01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.old = json.loads((DATA / "primary-crossnational-discovery-2026-10-30.json").read_text(encoding="utf-8"))
        cls.oct31 = json.loads((DATA / "primary-events-fiscal-actuals-2026-10-31.json").read_text(encoding="utf-8"))

    def test_no_false_population_or_causal_claims(self):
        d = self.data
        self.assertFalse(d["denominatorFrozen"])
        self.assertFalse(d["sourceScopeComplete"])
        self.assertIsNone(d["eligiblePopulationCount"])
        self.assertIsNone(d["fulfillmentRate"])
        self.assertIsNone(d["causalEffect"])
        self.assertEqual(d["independentHumanReviewCount"], 0)
        self.assertEqual(d["reviewRequired"]["fulfillmentVerdicts"], 0)
        self.assertFalse(d["reviewRequired"]["exclusionLogComplete"])

    def test_three_previously_known_source_documents(self):
        d = self.data
        self.assertEqual(len(d["sourceDocuments"]), 3)
        for s in d["sourceDocuments"]:
            self.assertTrue(s["alreadyIndexed"])
            self.assertTrue(s["rights"])
            self.assertTrue(s["locator"])
            self.assertEqual(urlsplit(s["url"]).scheme, "https")
            self.assertLess(dt.date.fromisoformat(s["published"]), dt.date.fromisoformat(s["electionDate"]))

    def test_candidates_not_duplicate_or_adjudicated(self):
        d = self.data
        candidates = d["candidatePledges"]
        self.assertEqual(len(candidates), 3)
        old_ids = {x["id"] for x in self.old["candidatePledges"]}
        old_ids.update(x["id"] for x in self.oct31["candidatePledges"])
        self.assertEqual(len({p["id"] for p in candidates}), len(candidates))
        self.assertFalse({p["id"] for p in candidates} & old_ids)
        docs = {s["id"] for s in d["sourceDocuments"]}
        events = {e["id"] for e in d["officialEvents"]}
        events.update(r["id"] for r in d["existingCrossLedgerEventReferences"])
        for p in candidates:
            self.assertIn(p["documentId"], docs)
            self.assertTrue(p["locator"])
            self.assertTrue(p["criterion"])
            self.assertIsNone(p["outcome"])
            self.assertEqual(p["independentReviewers"], 0)
            self.assertTrue(set(p["linkedOfficialEventIds"]) <= events)

    def test_events_unique_and_linked_prior_law_not_duplicated(self):
        d = self.data
        events = d["officialEvents"]
        self.assertEqual(len(events), 8)
        ids = [e["id"] for e in events]
        self.assertEqual(len(ids), len(set(ids)))
        old = {e["id"] for e in self.old["officialEvents"]}
        old.update(e["id"] for e in self.oct31["officialEvents"])
        self.assertFalse(set(ids) & old)
        for e in events:
            dt.date.fromisoformat(e["date"])
            self.assertEqual(urlsplit(e["url"]).scheme, "https")
            self.assertTrue(e["locator"])
            self.assertTrue(e["notProofOf"])
        self.assertEqual(len(d["existingCrossLedgerEventReferences"]), 1)
        self.assertIn("US22-PL117169", {e["id"] for e in self.old["officialEvents"]})
        self.assertNotIn("US22-PL117169", ids)
        self.assertTrue(all(e["kind"] != "actual_expenditure" for e in events))

    def test_treasury_monthly_actuals_not_capital_or_pledge_outcomes(self):
        d = self.data
        rows = d["fiscalActualObservations"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({r["id"] for r in rows}), 8)
        self.assertEqual({r["fiscalYear"] for r in rows}, {2024, 2025})
        self.assertEqual({r["unit"] for r in rows}, {"USD_millions_current"})
        self.assertEqual({r["measure"] for r in rows},
                         {"total_federal_outlays_on_and_off_budget_modified_cash_basis"})
        self.assertEqual({r["value"] for r in rows if r["calendarMonth"] == "2024-11"}, {668517})
        for r in rows:
            self.assertGreater(r["value"], 0)
            self.assertEqual(urlsplit(r["source"]).scheme, "https")
            self.assertTrue(r["locator"].startswith("Table 1, FY"))
            self.assertEqual(r["periodEnd"][:7], r["calendarMonth"])
        self.assertIn("not investment", d["fiscalProvenance"]["caution"].lower())
        self.assertIn("payment-date", d["fiscalProvenance"]["caution"].lower())


if __name__ == "__main__":
    unittest.main()
