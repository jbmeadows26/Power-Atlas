"""Offline regression tests for bounded, fair state-source scheduling."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from expand_state_bill_coverage import select_jurisdictions, STATES, MAX_PER_RUN


class StateCoverageSchedulerTests(unittest.TestCase):
    def test_exact_51_jurisdictions_and_eight_request_batch_limit(self):
        self.assertEqual(len(STATES), 51)
        self.assertEqual(len(STATES), len(set(STATES)))
        self.assertIn('DC', STATES)
        self.assertEqual(MAX_PER_RUN, 8)
        self.assertLessEqual(len(select_jurisdictions(STATES, {}, {}, MAX_PER_RUN)), 8)

    def test_unattempted_states_precede_repeated_timeouts(self):
        states = ['HI', 'IL', 'LA', 'MA', 'MD', 'ME']
        attempts = {'HI': 3, 'IL': 2, 'LA': 1, 'MA': 1}
        self.assertEqual(select_jurisdictions(states, {}, attempts, 3),
                         ['MD', 'ME', 'LA'])

    def test_failed_states_remain_eligible_after_fresh_states(self):
        states = ['HI', 'IL', 'LA']
        attempts = {'HI': 3, 'IL': 2, 'LA': 1}
        self.assertEqual(select_jurisdictions(states, {}, attempts, 3),
                         ['LA', 'IL', 'HI'])

    def test_completed_jurisdictions_are_not_queried_again(self):
        states = ['HI', 'IL', 'LA']
        self.assertEqual(select_jurisdictions(states, {'IL': {}}, {}, 8),
                         ['HI', 'LA'])

    def test_failure_checkpoint_records_have_safe_source_metadata(self):
        import json
        root = Path(__file__).resolve().parents[1]
        path = root / 'data/legislation/state-redistricting-jurisdictions.json'
        if not path.exists():
            self.skipTest('State checkpoint not initialized')
        checkpoint = json.loads(path.read_text(encoding='utf-8'))
        scanned = checkpoint['jurisdictions']
        for state, failure in checkpoint.get('sourceFailures', {}).items():
            self.assertNotIn(state, scanned)
            self.assertIn(state, checkpoint['remainingJurisdictions'])
            self.assertIn(failure['status'], ('temporary_unavailable', 'http_failure', 'access_or_rate_deferred'))
            self.assertEqual(failure['sourceEndpoint'], 'https://api.billcommons.org/api/v1/search')
            self.assertIn(failure['requestsAttempted'], (1, 2))
            self.assertRegex(failure['lastAttemptUTC'], r'^20[0-9]{2}-[0-9]{2}-[0-9]{2}'+chr(36))
            self.assertNotIn('errorMessage', failure)


if __name__ == '__main__':
    unittest.main()
