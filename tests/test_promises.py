"""Unit tests for research-ledger integrity (not substantive truth)."""
import copy
import json
import unittest

from scripts.validate_promises import DEFAULT, validate


class CampaignPromiseLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DEFAULT.read_text(encoding="utf-8"))

    def changed(self):
        return copy.deepcopy(self.data)

    def test_current_pilot_valid(self):
        report = validate(self.changed())
        self.assertEqual(report["records"], 2)
        self.assertFalse(report["representative"])
        self.assertFalse(report["factualAdjudication"])

    def test_duplicate_ids_not_silently_merged(self):
        doc = self.changed()
        doc["records"].append(copy.deepcopy(doc["records"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate pledge id"):
            validate(doc)

    def test_post_election_promises_excluded(self):
        doc = self.changed()
        doc["records"][0]["pledgeSource"]["documentDate"] = "2020-12-12"
        with self.assertRaisesRegex(ValueError, "post-election"):
            validate(doc)

    def test_unreviewed_cannot_be_adjudicated_by_one_person(self):
        doc = self.changed()
        doc["records"][0]["codingStatus"] = "adjudicated"
        with self.assertRaisesRegex(ValueError, "one reviewer"):
            validate(doc)

    def test_do_not_confuse_missing_data_with_unattempted(self):
        doc = self.changed()
        doc["records"][1]["outcome"] = "unattempted"
        with self.assertRaisesRegex(ValueError, "unattempted contradicts"):
            validate(doc)

    def test_future_term_outcome_must_be_unresolved(self):
        doc = self.changed()
        doc["records"][0]["rightCensored"] = True
        with self.assertRaisesRegex(ValueError, "right-censored"):
            validate(doc)

    def test_private_or_insecure_source_urls_rejected(self):
        doc = self.changed()
        doc["records"][0]["pledgeSource"]["url"] = "https://name:password@example.org/foo"
        with self.assertRaisesRegex(ValueError, "HTTPS URL"):
            validate(doc)

    def test_success_requires_implementation_event(self):
        doc = self.changed()
        doc["records"][0]["events"] = []
        with self.assertRaisesRegex(ValueError, "implementation event"):
            validate(doc)

    def test_hand_selected_records_cannot_be_relabelled_representative(self):
        doc = self.changed()
        doc["coverage"]["denominatorDefined"] = True
        with self.assertRaisesRegex(ValueError, "exhaustive denominator"):
            validate(doc)


if __name__ == "__main__":
    unittest.main()
