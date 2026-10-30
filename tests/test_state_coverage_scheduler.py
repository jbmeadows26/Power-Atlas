"""Offline regression tests for bounded, fair state-source scheduling."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from expand_state_bill_coverage import select_jurisdictions, retry_allowed, STATES, MAX_PER_RUN


class StateCoverageSchedulerTests(unittest.TestCase):
    def test_exact_51_jurisdictions_and_eight_request_batch_limit(self):
        self.assertEqual(len(STATES), 51)
        self.assertEqual(len(STATES), len(set(STATES)))
        self.assertIn('DC', STATES)
        self.assertEqual(MAX_PER_RUN, 8)
        self.assertLessEqual(len(select_jurisdictions(STATES, {}, {}, MAX_PER_RUN)), 8)

    def test_same_day_retry_ceiling_and_access_restrictions(self):
        today = '2026-10-29'
        transient = {'IL': {'status': 'temporary_unavailable', 'lastAttemptUTC': today}}
        self.assertFalse(retry_allowed('IL', {'IL': 3}, transient, today))
        self.assertTrue(retry_allowed('IL', {'IL': 3}, transient, '2026-10-30'))
        denied = {'IL': {'httpStatus': 403, 'lastAttemptUTC': today}}
        self.assertFalse(retry_allowed('IL', {'IL': 1}, denied, '2026-10-30'))
        limited = {'IL': {'httpStatus': 429, 'lastAttemptUTC': today}}
        self.assertFalse(retry_allowed('IL', {'IL': 1}, limited, today))
        self.assertTrue(retry_allowed('IL', {'IL': 1}, limited, '2026-10-30'))

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
            self.assertIn(failure['requestsAttempted'], (1, 2, 3, 4))
            if 'perPageVariantsAttempted' in failure:
                self.assertEqual(failure['perPageVariantsAttempted'][0], 20)
                self.assertTrue(set(failure['perPageVariantsAttempted']).issubset({20, 10, 5}))
            self.assertRegex(failure['lastAttemptUTC'], r'^20[0-9]{2}-[0-9]{2}-[0-9]{2}'+chr(36))
            self.assertNotIn('errorMessage', failure)


    def test_official_search_fallbacks_do_not_fake_jurisdiction_coverage(self):
        """Official bill spotchecks are evidence, not completed first-page searches."""
        import json
        root = Path(__file__).resolve().parents[1]
        checkpoint = json.loads((root / 'data/legislation/state-redistricting-jurisdictions.json').read_text(encoding='utf-8'))
        probes = json.loads((root / 'data/health/state-source-probes.json').read_text(encoding='utf-8'))
        for state, prefix in (('IL', 'https://www.ilga.gov/'),
                              ('TX', 'https://capitol.texas.gov/')):
            matches = [row for row in probes['sources']
                       if row.get('jurisdiction') == state
                       and row.get('domain') == 'state_legislation']
            self.assertEqual(len(matches), 1)
            self.assertTrue(matches[0]['officialSearch'].startswith(prefix))
            self.assertIn('spotcheck', matches[0]['persistedOfficialSpotchecks'])
            if state in checkpoint['remainingJurisdictions']:
                self.assertNotIn(state, checkpoint['jurisdictions'])
                self.assertIn(state, checkpoint['sourceFailures'])
                self.assertTrue(matches[0]['unresolved'])



    def test_scanned_does_not_mean_candidate_rows_exist(self):
        """A successful keyword request is not proof a state has indexed bills."""
        import json
        root = Path(__file__).resolve().parents[1]
        checkpoint = json.loads((root / 'data/legislation/state-redistricting-jurisdictions.json').read_text(encoding='utf-8'))
        bills = json.loads((root / 'data/legislation/state-redistricting-bills.json').read_text(encoding='utf-8'))
        counts = {}
        for row in bills['records']:
            counts[row['state']] = counts.get(row['state'], 0) + 1
        for state, metadata in checkpoint['jurisdictions'].items():
            persisted = counts.get(state, 0)
            self.assertEqual(metadata.get('persistedCandidateRows'), persisted)
            if persisted == 0 and (metadata.get('totalMatchesReported') or 0) > 0:
                self.assertEqual(metadata['status'], 'first_page_matches_reported_no_candidates_persisted')
            elif persisted == 0:
                self.assertEqual(metadata['status'], 'first_page_empty_search_not_no_bills')
            else:
                self.assertEqual(metadata['status'], 'first_page_indexed_not_exhaustive')


if __name__ == '__main__':
    unittest.main()
