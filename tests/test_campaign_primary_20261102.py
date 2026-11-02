"""Structural, provenance and inference-safety checks for 2026-11-02 additive campaign evidence.
CI cannot independently adjudicate pledges or establish the truth of linked primary sources.
"""
import datetime as dt
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "promises"
LEDGER = DATA / "primary-paris-tcja-mts-2026-11-02.json"


class CampaignPrimaryNov02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.old = [
            json.loads((DATA / name).read_text(encoding="utf-8"))
            for name in (
                "primary-crossnational-discovery-2026-10-30.json",
                "primary-events-fiscal-actuals-2026-10-31.json",
                "primary-medicare-tax-mts-2026-11-01.json",
            )
        ]

    def test_no_unearned_population_or_causal_inference(self):
        d = self.d
        self.assertFalse(d["denominatorFrozen"])
        self.assertFalse(d["sourceScopeComplete"])
        self.assertIsNone(d["eligiblePopulationCount"])
        self.assertIsNone(d["fulfillmentRate"])
        self.assertIsNone(d["causalEffect"])
        self.assertEqual(d["independentHumanReviewCount"], 0)
        self.assertEqual(d["reviewRequired"]["fulfillmentVerdicts"], 0)
        self.assertFalse(d["reviewRequired"]["exclusionLogComplete"])

    def test_source_dates_and_rights(self):
        self.assertEqual(len(self.d["sourceDocuments"]), 2)
        for s in self.d["sourceDocuments"]:
            self.assertTrue(s["alreadyIndexed"])
            self.assertTrue(s["rights"])
            self.assertTrue(s["locator"])
            self.assertFalse(s["originalPartyDocumentInventoryComplete"])
            self.assertEqual(urlsplit(s["url"]).scheme, "https")
            self.assertLess(dt.date.fromisoformat(s["published"]), dt.date.fromisoformat(s["electionDate"]))

    def test_atomic_candidates_and_existing_parent_references(self):
        candidates = self.d["candidatePledges"]
        self.assertEqual(len(candidates), 3)
        ids = [x["id"] for x in candidates]
        self.assertEqual(len(ids), len(set(ids)))
        previous_ids = {p["id"] for ledger in self.old for p in ledger.get("candidatePledges", [])}
        self.assertFalse(set(ids) & previous_ids)
        self.assertIn("US24-GOP-TCJA", previous_ids)
        docs = {x["id"] for x in self.d["sourceDocuments"]}
        events = {x["id"] for x in self.d["officialEvents"]}
        for p in candidates:
            self.assertIn(p["documentId"], docs)
            self.assertTrue(p["locator"])
            self.assertTrue(p["criterion"])
            self.assertIsNone(p["outcome"])
            self.assertEqual(p["independentReviewers"], 0)
            self.assertTrue(set(p["linkedOfficialEventIds"]) <= events)
            if "parentExistingCandidateId" in p:
                self.assertIn(p["parentExistingCandidateId"], previous_ids)

    def test_seven_events_are_distinct_from_previous_ledgers(self):
        events = self.d["officialEvents"]
        self.assertEqual(len(events), 7)
        ids = [e["id"] for e in events]
        self.assertEqual(len(ids), len(set(ids)))
        previous_ids = {e["id"] for ledger in self.old for e in ledger.get("officialEvents", [])}
        self.assertFalse(set(ids) & previous_ids)
        for e in events:
            dt.date.fromisoformat(e["date"])
            self.assertEqual(urlsplit(e["url"]).scheme, "https")
            self.assertTrue(e["locator"])
            self.assertTrue(e["notProofOf"])
        self.assertEqual(sum(e["kind"] == "enacted_statutory_provision_mapping" for e in events), 2)
        self.assertEqual({e["linksExistingStatuteId"] for e in events if "linksExistingStatuteId" in e}, {"US25-PL11921"})
        self.assertIn("US25-PL11921", previous_ids)
        self.assertEqual({e["date"] for e in events if "WITHDRAWAL-EFFECTIVE" in e["id"]}, {"2026-01-27"})

    def test_treasury_actuals_are_monthly_and_noninvestment(self):
        rows = self.d["fiscalActualObservations"]
        self.assertEqual(len(rows), 5)
        self.assertEqual({r["calendarMonth"] for r in rows},
                         {"2020-09", "2020-10", "2020-11", "2020-12", "2021-01"})
        self.assertEqual({r["value"] for r in rows if r["calendarMonth"] == "2020-11"}, {364819})
        self.assertEqual({r["unit"] for r in rows}, {"USD_millions_current"})
        self.assertEqual({r["measure"] for r in rows},
                         {"total_federal_outlays_on_and_off_budget_modified_cash_basis"})
        prior_ids = {r["id"] for ledger in self.old for r in ledger.get("fiscalActualObservations", [])}
        self.assertFalse({r["id"] for r in rows} & prior_ids)
        for r in rows:
            self.assertGreater(r["value"], 0)
            self.assertEqual(urlsplit(r["source"]).scheme, "https")
            self.assertTrue(r["locator"].startswith("Table 1, FY"))
            self.assertEqual(r["periodEnd"][:7], r["calendarMonth"])
            self.assertEqual(r["fiscalYear"], 2020 if r["calendarMonth"] == "2020-09" else 2021)
        self.assertIn("not investment", self.d["fiscalProvenance"]["caution"].lower())
        self.assertIn("payment-date", self.d["fiscalProvenance"]["caution"].lower())


if __name__ == "__main__":
    unittest.main()
