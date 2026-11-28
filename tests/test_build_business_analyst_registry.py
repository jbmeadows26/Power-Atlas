import copy
import json
from pathlib import Path
import unittest

from scripts.build_business_analyst_registry import build, validate_receipts


WORKFLOW = 'Eastern Axis global conflict analyst'


def receipt(run, updated, conclusion='success', stages=None, sha='a' * 40):
    value = {
        'conclusion': conclusion,
        'headSha': sha,
        'updatedAt': updated,
        'url': f'https://github.com/jbmeadows26/Power-Atlas/actions/runs/{run}',
        'workflowName': WORKFLOW,
    }
    if stages is not None:
        value['stageEvidence'] = stages
    return value


def stage(status, evidence='test evidence', **extra):
    return {'status': status, 'evidence': [evidence], **extra}


def analyst(result):
    return next(item for item in result['analysts'] if item['name'] == 'Global Conflict Analyst')


class ReceiptValidationTests(unittest.TestCase):
    def test_missing_field_unknown_conclusion_and_bad_identity_are_rejected(self):
        cases = []
        missing = receipt(1, '2026-11-27T21:00:00Z'); missing.pop('headSha'); cases.append(missing)
        unknown = receipt(2, '2026-11-27T21:00:00Z', conclusion='weird'); cases.append(unknown)
        bad_sha = receipt(3, '2026-11-27T21:00:00Z', sha='short'); cases.append(bad_sha)
        bad_url = receipt(4, '2026-11-27T21:00:00Z'); bad_url['url'] = 'https://example.org/run/4'; cases.append(bad_url)
        bad_time = receipt(5, 'not-a-date'); cases.append(bad_time)
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_receipts([value])

    def test_duplicate_runs_and_invalid_failed_stage_are_rejected(self):
        value = receipt(1, '2026-11-27T21:00:00Z')
        with self.assertRaisesRegex(ValueError, 'duplicates'):
            validate_receipts([value, copy.deepcopy(value)])
        invalid = receipt(2, '2026-11-27T21:00:00Z', stages={
            'publication': stage('failed')})
        with self.assertRaisesRegex(ValueError, 'classification'):
            validate_receipts([invalid])


class OrderingAndStageTests(unittest.TestCase):
    def test_canonical_failure_is_preserved_after_successful_publication_without_production_promotion(self):
        root = Path(__file__).resolve().parents[1]
        receipts = json.loads((root / 'business-intelligence/analyst-execution-receipts.json').read_text())
        item = analyst(build(receipts))
        self.assertEqual(item['analyticalStatus'], 'success')
        self.assertEqual(item['validationStatus'], 'success')
        self.assertEqual(item['publicationStatus'], 'success')
        publication_history = item['executionStages']['publication']['history']
        self.assertEqual([record['status'] for record in publication_history[:2]], ['success', 'failed'])
        self.assertEqual(publication_history[1]['failureClassification'], 'combined-checkout-publication-failure-unresolved')
        self.assertEqual(item['productionVerificationStatus'], 'unavailable')
        self.assertNotEqual(item['operationalStatus'], 'operational')

    def test_genuinely_unsorted_receipts_use_parsed_time_and_run_tie_break(self):
        receipts = [
            receipt(10, '2026-11-27T20:00:00Z', stages={'analysis': stage('success', 'old')}),
            receipt(30, '2026-11-27T21:00:00+00:00', conclusion='failure', stages={
                'analysis': stage('failed', 'new', failureClassification='source', reason='fixture')}),
            receipt(20, '2026-11-27T20:30:00Z', stages={'analysis': stage('success', 'middle')}),
            receipt(31, '2026-11-27T21:00:00Z', stages={'analysis': stage('success', 'tie winner')}),
        ]
        item = analyst(build(receipts))
        self.assertEqual(item['latestExecution']['url'].split('/')[-1], '31')
        self.assertEqual(item['analyticalStatus'], 'success')
        self.assertEqual(item['executionStages']['analysis']['history'][0]['evidence'], ['tie winner'])

    def test_run_conclusion_never_infers_stage_results(self):
        for conclusion in ('success', 'failure', 'skipped'):
            with self.subTest(conclusion=conclusion):
                item = analyst(build([receipt(1, '2026-11-27T21:00:00Z', conclusion)]))
                self.assertEqual(item['analyticalStatus'], 'unavailable')
                self.assertEqual(item['publicationStatus'], 'unavailable')
                self.assertEqual(item['productionVerificationStatus'], 'unavailable')

    def test_known_failure_distinguishes_successful_analysis_and_failed_publication(self):
        stages = {
            'analysis': stage('success'),
            'validation': stage('success'),
            'publication': stage('failed', failureClassification='combined-publish', reason='unknown dirty state'),
            'production': stage('unavailable'),
        }
        item = analyst(build([receipt(1, '2026-11-27T21:00:00Z', 'failure', stages)]))
        self.assertEqual(item['analyticalStatus'], 'success')
        self.assertEqual(item['validationStatus'], 'success')
        self.assertEqual(item['publicationStatus'], 'failed')
        self.assertEqual(item['productionVerificationStatus'], 'unavailable')
        self.assertEqual(item['operationalStatus'], 'failed')

    def test_newer_legacy_receipt_withholds_axis_but_preserves_history(self):
        receipts = [
            receipt(1, '2026-11-27T20:00:00Z', stages={'analysis': stage('success')}),
            receipt(2, '2026-11-27T21:00:00Z', conclusion='failure'),
        ]
        item = analyst(build(receipts))
        self.assertEqual(item['analyticalStatus'], 'unavailable')
        self.assertIsNotNone(item['lastSuccessfulAnalysis'])

    def test_failure_history_survives_later_success(self):
        receipts = [
            receipt(1, '2026-11-27T20:00:00Z', conclusion='failure', stages={
                'publication': stage('failed', failureClassification='conflict', reason='fixture')}),
            receipt(2, '2026-11-27T21:00:00Z', stages={'publication': stage('success')}),
        ]
        item = analyst(build(receipts))
        self.assertEqual(item['publicationStatus'], 'success')
        self.assertEqual([entry['recordedStatus'] for entry in item['executionStages']['publication']['history']], ['success', 'failed'])


class ProductionContextTests(unittest.TestCase):
    def test_production_requires_matching_ds001_release_context(self):
        release = 'b' * 40
        receipts = [receipt(1, '2026-11-27T21:00:00Z', stages={
            'production': stage('verified', releaseCommit=release)})]
        self.assertEqual(analyst(build(receipts))['productionVerificationStatus'], 'unavailable')
        stale = {'status': 'Verified', 'commit': 'c' * 40, 'releaseContext': {
            'schema': 'eastern-axis.release-context.v1', 'status': 'Verified', 'deployedCommit': 'c' * 40}}
        self.assertEqual(analyst(build(receipts, stale))['productionVerificationStatus'], 'stale')
        current = {'status': 'Verified', 'commit': release, 'releaseContext': {
            'schema': 'eastern-axis.release-context.v1', 'status': 'Verified', 'deployedCommit': release}}
        self.assertEqual(analyst(build(receipts, current))['productionVerificationStatus'], 'verified')

    def test_failed_production_is_preserved_without_becoming_stale(self):
        receipts = [receipt(1, '2026-11-27T21:00:00Z', conclusion='failure', stages={
            'production': stage('failed', failureClassification='browser', reason='workflow failed')})]
        item = analyst(build(receipts))
        self.assertEqual(item['productionVerificationStatus'], 'failed')
        self.assertEqual(item['executionStages']['production']['history'][0]['failureClassification'], 'browser')


if __name__ == '__main__':
    unittest.main()
