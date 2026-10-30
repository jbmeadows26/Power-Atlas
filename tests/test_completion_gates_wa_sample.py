"""Guard against conflating official WA member-vote sample with redistricting vote verification."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class OfficialRollcallScopeTests(unittest.TestCase):
    def test_wa_sample_is_persisted_and_not_a_national_redistricting_census(self):
        wa=json.loads((ROOT/'data/legislation/wa-2023-24-rollcalls/source-rollcalls.json').read_text(encoding='utf-8'))
        gates=json.loads((ROOT/'data/health/completion-gates.json').read_text(encoding='utf-8'))
        by_id={g['id']:g for g in gates['gates']}
        sample=by_id['official_wa_2023_24_member_rollcall_sample']
        redistricting=by_id['official_state_rollcalls']
        self.assertEqual(sample['observed'],len(wa['records']))
        self.assertEqual(sample['observed'],wa['rollCalls'])
        self.assertEqual(wa['memberVoteRows'],sum(len(r['memberVotes']) for r in wa['records']))
        self.assertEqual(sample['scope'],'WA_2023_24_42_requested_bills_21_with_votes')
        self.assertEqual(sample['status'],'complete_bounded_primary_source_sample')
        self.assertFalse(wa['historicalSessionComplete'])
        self.assertFalse(wa['allStateRollCallsComplete'])
        self.assertEqual(redistricting['observed'],1)
        self.assertEqual(redistricting['status'],'partial_sample_not_member_ballot_census')
        self.assertEqual(gates['disposition'],'not_nationwide_research_complete')


if __name__=='__main__':
    unittest.main()
