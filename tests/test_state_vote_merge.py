"""Regression tests for lossless, source-qualified state vote refreshes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_state_redistricting_bills import merge_vote_records


class StateVoteMergeTests(unittest.TestCase):
    def test_zero_placeholder_cannot_erase_previous_positive_tally(self):
        prior = {"id": "vote-1", "counts": {"yes_count": 15, "no_count": 2},
                 "tallyStatus": "reported_positive_tally"}
        missing = {"id": "vote-1", "counts": {},
                   "tallyStatus": "not_reported_or_unverifiable"}
        self.assertEqual(merge_vote_records([prior], [missing])["vote-1"], prior)

    def test_new_positive_tally_replaces_missing_placeholder(self):
        prior = {"id": "vote-1", "counts": {},
                 "tallyStatus": "not_reported_or_unverifiable"}
        positive = {"id": "vote-1", "counts": {"yes_count": 20, "no_count": 1},
                    "tallyStatus": "reported_positive_tally"}
        self.assertEqual(merge_vote_records([prior], [positive])["vote-1"], positive)

    def test_existing_and_new_vote_ids_are_retained(self):
        old = {"id": "vote-old", "counts": {}, "tallyStatus": "not_reported_or_unverifiable"}
        new = {"id": "vote-new", "counts": {}, "tallyStatus": "not_reported_or_unverifiable"}
        self.assertEqual(set(merge_vote_records([old], [new])), {"vote-old", "vote-new"})


if __name__ == "__main__":
    unittest.main()
