"""Integrity and publication-safety gates for the expanded pledge corpus.

These checks cannot establish factual correctness or an exhaustive denominator.
"""
import json
from pathlib import Path
import unittest

from scripts.validate_promises import validate

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "promises"


class CampaignPledgeExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pilot = json.loads((D / "us-2020-pilot.json").read_text())
        cls.expansion = json.loads((D / "us-2020-source-verified-expansion.json").read_text())
        cls.queue = json.loads((D / "us-2020-review-queue.json").read_text())
        cls.registry = json.loads((D / "source-registry.json").read_text())

    def test_expansion_format(self):
        report = validate(self.expansion)
        self.assertEqual(report["records"], 6)
        self.assertFalse(report["representative"])
        self.assertFalse(report["factualAdjudication"])

    def test_source_links_are_https(self):
        for doc in (self.pilot, self.expansion):
            for record in doc["records"]:
                self.assertTrue(record["pledgeSource"]["url"].startswith("https://"))
                for event in record["events"]:
                    self.assertTrue(event["source"].startswith("https://"))

    def test_all_scored_records_are_explicitly_provisional(self):
        for doc in (self.pilot, self.expansion):
            self.assertEqual(doc["coverage"]["denominatorDefined"], False)
            self.assertEqual(doc["publicationStatus"], "provisional_pilot_not_representative")
            for record in doc["records"]:
                self.assertEqual(record["codingStatus"], "provisional_source_checked")
                self.assertEqual(record["reviewerCount"], 1)

    def test_first_achievements_not_conflated_with_successor_reversals(self):
        changed = [r for r in self.expansion["records"]
                   if any(e["kind"] == "post_term_policy_reversal" for e in r["events"])]
        self.assertGreaterEqual(len(changed), 2)
        for r in changed:
            self.assertEqual(r["outcome"], "fully_enacted")
            reversal = [e for e in r["events"] if e["kind"] == "post_term_policy_reversal"]
            for e in reversal:
                self.assertGreaterEqual(e["date"], r["evaluationWindowEnd"])

    def test_pledge_ids_unique_across_pilot_expansion_and_queue(self):
        ids = ([r["id"] for r in self.pilot["records"]] +
               [r["id"] for r in self.expansion["records"]] +
               [r["id"] for r in self.queue["records"]])
        self.assertEqual(len(ids), len(set(ids)))

    def test_unscored_queue_cannot_be_counted_as_broken(self):
        self.assertEqual(self.queue["publicationStatus"], "not_eligible_for_fulfillment_statistics")
        self.assertFalse(self.queue["denominatorFrozen"])
        self.assertEqual(len(self.queue["records"]), 24)
        for item in self.queue["records"]:
            self.assertIsNone(item["outcome"])
            self.assertEqual(item["reviewStatus"], "no_outcome_research_completed")
            self.assertIn("candidate_needs_atomization_review", item["inclusionStatus"])

    def test_source_registry_is_not_pretending_to_be_ingested_data(self):
        self.assertEqual(self.registry["publicationStatus"], "source_catalog_only_no_data_ingestion")
        self.assertEqual(self.registry["sourceCount"], len(self.registry["sources"]))
        self.assertGreaterEqual(len(self.registry["sources"]), 15)
        for entry in self.registry["sources"]:
            self.assertEqual(entry["recordCountIngested"], 0)
            self.assertEqual(entry["licensesChecked"], False)
        self.assertEqual(len({e["id"] for e in self.registry["sources"]}),
                         len(self.registry["sources"]))

    def test_atomic_wage_promise_excludes_tipped_component(self):
        wage = next(r for r in self.pilot["records"] if "MINWAGE" in r["id"])
        self.assertNotIn("tipped", wage["pledgeParaphrase"].lower())
        self.assertNotIn("tipped", wage["successCriterion"].lower())

    def test_archived_platform_source_date_consistent(self):
        for r in self.expansion["records"]:
            self.assertEqual(r["pledgeSource"]["documentDate"], "2020-08-17")
            self.assertTrue(r["pledgeSource"]["isPreElection"])
            self.assertTrue(r["sourceLocator"])

    def test_kigali_distinguishes_ratification_from_legal_effect(self):
        row = next(r for r in self.expansion["records"] if "KIGALI" in r["id"])
        kinds = {e["kind"] for e in row["events"]}
        self.assertIn("international_entry_into_force", kinds)
        self.assertIn("executive_action", kinds)

    def test_no_wage_related_pledge_is_presented_as_full(self):
        row = next(r for r in self.pilot["records"] if "MINWAGE" in r["id"])
        self.assertNotEqual(row["outcome"], "fully_enacted")

    def test_reviewers_are_not_claimed(self):
        all_rows = self.pilot["records"] + self.expansion["records"]
        self.assertFalse(any(r["codingStatus"] == "adjudicated" for r in all_rows))


if __name__ == "__main__":
    unittest.main()
