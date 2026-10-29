"""Offline regression tests for bounded, fair state-source scheduling."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from expand_state_bill_coverage import select_jurisdictions


class StateCoverageSchedulerTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
