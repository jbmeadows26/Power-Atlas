"""Structural checks for the additive 2026-10-31 campaign evidence increment.

These are not source-truth or independent-human-adjudication tests.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "data/promises/primary-events-fiscal-actuals-2026-10-31.json"


class CampaignEvidenceDiscoveryIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))

    def test_no_false_population_or_causal_claims(self):
        d = self.data
        self.assertFalse(d["denominatorFrozen"])
        self.assertFalse(d["sourceScopeComplete"])
        self.assertIsNone(d["eligiblePopulationCount"])
        self.assertIsNone(d["fulfillmentRate"])
        self.assertIsNone(d["causalEffect"])
        self.assertEqual(d["independentHumanReviewCount"], 0)
        self.assertEqual(d["reviewRequired"]["outcomeVerdictsPublished"], 0)

    def test_unique_ids_and_valid_links(self):
        d = self.data
        all_items = d["candidatePledges"] + d["officialEvents"] + d["fiscalActualObservations"]
        ids = [item["id"] for item in all_items]
        self.assertEqual(len(ids), len(set(ids)))
        events = {item["id"] for item in d["officialEvents"]}
        for pledge in d["candidatePledges"]:
            self.assertIsNone(pledge["outcome"])
            self.assertIsNone(pledge["independentCoderA"])
            self.assertIsNone(pledge["independentCoderB"])
            self.assertTrue(set(pledge["linkedOfficialEventIds"]).issubset(events))
        for item in d["officialEvents"]:
            self.assertTrue(item["url"].startswith("https://"))
            self.assertFalse(item["actualExpenditure"])
        for item in d["fiscalActualObservations"]:
            self.assertTrue(item["source"].startswith("https://"))

    def test_exact_observation_counts_and_units(self):
        d = self.data
        self.assertEqual(len(d["candidatePledges"]), 3)
        self.assertEqual(len(d["officialEvents"]), 6)
        self.assertEqual(len(d["fiscalActualObservations"]), 3)
        amounts = {x["fiscalYear"]: x["value"] for x in d["fiscalActualObservations"]}
        self.assertEqual(amounts, {
            "2022-23": 6828959017,
            "2023-24": 7619725159,
            "2024-25": 7968878253,
        })
        for item in d["fiscalActualObservations"]:
            self.assertEqual(item["unit"], "CAD_current_dollars")
            self.assertEqual(item["measure"], "departmental_total_actual_spending_authorities_used_including_internal_services")
        self.assertIn("C$1 discrepancy", d["fiscalActualObservations"][1]["note"])

    def test_2020_pledges_and_temporal_direction(self):
        d = self.data
        self.assertEqual(d["campaignSource"]["published"], "2020-08-17")
        self.assertEqual(d["campaignSource"]["electionDate"], "2020-11-03")
        self.assertTrue(d["campaignSource"]["alreadyIndexed"])
        self.assertTrue(all(x["date"] > d["campaignSource"]["electionDate"] for x in d["officialEvents"] if x["country"] == "US"))

    def test_rights_and_no_fiscal_conflation(self):
        d = self.data
        self.assertIn("paraphrase_only", d["campaignSource"]["rights"])
        self.assertTrue(any("not comparable" in x.lower() for x in d["limitations"]))
        self.assertTrue(any("predates" in x.lower() for x in d["limitations"]))


if __name__ == "__main__":
    unittest.main()
