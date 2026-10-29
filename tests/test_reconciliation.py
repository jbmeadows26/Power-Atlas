"""Reconciliation/verification and access-control tests for Power Atlas."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def source_adapter():
    spec=importlib.util.spec_from_file_location('access',ROOT/'scripts/source_access.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ReconciliationTests(unittest.TestCase):
    def test_access_without_credentials_is_read_only(self):
        r=source_adapter().provider_access({})
        self.assertFalse(r['planscore']['permit_live_calls'])
        self.assertFalse(r['redistricting_data_hub']['permit_bulk_download'])
        self.assertEqual(r['planscore']['mode'],'published_methodology_metadata_only')
        self.assertEqual(r['redistricting_data_hub']['mode'],'public_file_manifest_metadata_only')

    def test_token_presence_not_approval_to_download(self):
        r=source_adapter().provider_access({
            'PLANSCORE_API_TOKEN':'test-token',
            'RDH_API_APPROVED':'true','RDH_USERNAME':'public-username',
            'RDH_PASSWORD':'not-a-real-secret'
        })
        self.assertFalse(r['planscore']['permit_live_calls'])
        self.assertFalse(r['redistricting_data_hub']['permit_bulk_download'])
        self.assertNotIn('test-token',str(r))
        self.assertNotIn('not-a-real-secret',str(r))

    def test_analytics_metric_prerequisite_gates(self):
        m=load('data/redistricting/analytics-sources.json')
        self.assertGreaterEqual(len(m['sources']),8)
        self.assertGreaterEqual(len(m['metrics']),8)
        for metric in m['metrics']:
            self.assertTrue(metric.get('prerequisites'))
            self.assertFalse(metric['calculationStatus']=='ready_to_label_gerrymandered')
        by_id={x['id']:x for x in m['sources']}
        self.assertEqual(by_id['redistricting_data_hub']['access'].startswith('verified_account'),True)

    def test_51_official_election_authorities_excludes_territory(self):
        d=load('data/elections/official-source-index.json')
        states={x['state'] for x in d['records']}
        self.assertEqual(len(states),51)
        self.assertIn('DC',states)
        self.assertIn('ND',states)
        self.assertNotIn('PR',states)
        for row in d['records']:
            self.assertTrue(row['electionOfficeURL'].startswith('https://'))
            self.assertIsNone(row['officialCertifiedResultURL'])
            self.assertFalse(row['stateCertifiedVoteTotalsRetrieved'])

    def test_reconciled_vote_staging_and_election_domain(self):
        path=ROOT/'data/reconciliation/domain-integrity.json'
        if not path.exists():
            self.skipTest('First evidence reconciliation has not published yet')
        d=load('data/reconciliation/domain-integrity.json')
        votes=load('data/reconciliation/rollcall-staging.json')
        staged=load('data/reconciliation/raw-legislative-ingestion.json')
        src=load('data/legislation/state-redistricting-votes.json')
        bills=load('data/legislation/state-redistricting-bills.json')
        self.assertEqual(staged['counts']['rawLegislativeBillCandidates'],len(bills['records']))
        self.assertEqual(len(votes['records']),len(src['records']))
        self.assertEqual(votes['counts']['certified_tally'],0)
        self.assertEqual(votes['counts']['partially_parsed'],sum(
            1 for x in src['records'] if {'yes_count','no_count','other_count'}.issubset(x.get('counts',{}))))
        self.assertEqual(sum(votes['counts'].values()),len(src['records']))
        self.assertTrue(all(v['officialTallyVerified'] is False for v in votes['records']))
        self.assertEqual(load('data/reconciliation/verified-production.json')['certifiedLegislativeRollCalls'],[])
        self.assertFalse(d['domainDefinitions']['campaign_finance']['crossDomainVoteAggregationAllowed'])
        self.assertEqual(d['summary']['candidateBillsPromotedToProduction'],0)

    def test_coverage_has_explicit_queue_and_no_false_full_sweep(self):
        path=ROOT/'data/reconciliation/search-coverage.json'
        if not path.exists():
            self.skipTest('First coverage reconciliation has not published yet')
        coverage=load('data/reconciliation/search-coverage.json')
        queue=load('data/reconciliation/ingestion-queue.json')
        checkpoint=load('data/legislation/state-redistricting-jurisdictions.json')
        self.assertEqual(len(coverage['records']),51)
        self.assertEqual(coverage['fullSweep'],0)
        self.assertEqual(coverage['page1Complete'],len(checkpoint['jurisdictions']))
        self.assertEqual(coverage['pendingFirstPage'],51-len(checkpoint['jurisdictions']))
        self.assertEqual(set(queue['pendingBaselineStates']),set(checkpoint['remainingJurisdictions']))
        self.assertTrue(all(row['coverageStatus'] in
                            ('pending','page1_complete','full_sweep') for row in coverage['records']))

    def test_temporal_legal_scope_is_not_automatic_risk_score(self):
        path=ROOT/'data/reconciliation/legal-framework-timeline.json'
        if not path.exists():
            self.skipTest('First legal framework reconciliation has not published yet')
        doc=load('data/reconciliation/legal-framework-timeline.json')
        self.assertIn('Callais',doc['reviewWarning'])
        by_id={x['id']:x for x in doc['frameworks']}
        self.assertEqual(by_id['VRA_Sec2_Callais_2026']['decisionDate'],'2026-04-29')
        self.assertTrue(all(x['legalApplicability']=='requires_case_specific_review_no_automated_retroactivity'
                            for x in doc['cases']))
if __name__=='__main__':
    unittest.main()
