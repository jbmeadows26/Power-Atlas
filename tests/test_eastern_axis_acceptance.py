import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('registry', ROOT / 'scripts/validate_eastern_axis_acceptance.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'site/development-control/acceptance.json').read_text())

    def record(self, requirement='EA-001', identifier='EA-001-AC01'):
        target = next(item for item in self.data['requirements'] if item['id'] == requirement)
        return next(item for item in target['criteria'] + target['gates'] if item['id'] == identifier)

    def evidence(self, identifier, *, stage='source', result='passed', commit='a' * 40, disposition='assessment', release_scope=None):
        item = dict(
            id=identifier,
            executedAt='2026-11-28T00:00:00Z',
            commit=commit,
            artifact='https://github.com/jbmeadows26/Power-Atlas/actions/runs/1',
            method='Isolated acceptance fixture',
            scope=stage,
            stage=stage,
            result=result,
            disposition={'class': disposition} if disposition == 'assessment' else {'class': disposition, 'reason': 'Retained release execution.'},
        )
        if stage in {'deployed', 'production', 'commercial'}:
            item['deployedCommit'] = commit
        if release_scope:
            item['releaseScope'] = {'policy': 'unchanged-assets', 'paths': release_scope}
        self.data['evidence'].append(item)
        return item

    def assess(self, record, evidence, *, state='Verified', stage='source', history=None, assessed='2026-11-28T00:00:01Z'):
        record.update(state=state, stage=stage, evidence=[evidence], assessedAt=assessed)
        record['assessmentHistory'] = history if history is not None else [dict(state='Pending', evidence=[], reason='Initial state.', assessedAt='2026-11-27T23:59:59Z')]
        if state in {'Partial', 'Failed'}:
            record['reason'] = 'Bounded execution result.'

    def context(self, commit='a' * 40, carry=None):
        return dict(status='Verified', deployedCommit=commit, source='pages-release-identity', artifact='identity.json', carryForwardEvidence=carry or [])

    def verify_requirement(self, identifier='EA-001', commit='a' * 40):
        target = next(item for item in self.data['requirements'] if item['id'] == identifier)
        stages = {'criterion': 'production', 'G02': 'production', 'G05': 'production', 'G06': 'production', 'G07': 'production', 'G08': 'production', 'G09': 'deployed'}
        records = [('criterion', item) for item in target['criteria']] + [(item['id'], item) for item in target['gates']]
        for index, (kind, record) in enumerate(records):
            stage = stages.get(kind, 'source')
            evidence_id = f'fixture-{identifier}-{index}'
            self.evidence(evidence_id, stage=stage, commit=commit)
            self.assess(record, evidence_id, stage=stage)
        return target

    def test_canonical_registry_is_valid_without_release_context(self):
        report = module.summarize(self.data)
        self.assertEqual(report['verifiedAcceptanceRecords'], 7)
        self.assertEqual(report['applicableAcceptanceRecords'], 240)
        self.assertEqual(report['currentRelease']['status'], 'unavailable')
        self.assertFalse(any(item['complete'] for item in report['requirements'].values()))

    def test_verified_requires_executed_evidence(self):
        record = self.record()
        record.update(state='Verified', stage='source', evidence=[], assessedAt='2026-11-28T00:00:01Z', assessmentHistory=[dict(state='Pending', evidence=[], reason='Initial.', assessedAt='2026-11-28T00:00:00Z')])
        with self.assertRaisesRegex(ValueError, 'requires evidence'):
            module.summarize(self.data)

    def test_missing_gate_rejected(self):
        self.data['requirements'][0]['gates'].pop()
        with self.assertRaisesRegex(ValueError, 'Missing or duplicate gate'):
            module.summarize(self.data)

    def test_not_applicable_is_excluded_not_passed(self):
        gate = self.record('EA-001', 'G04')
        gate.update(state='Not applicable', evidence=[], reason='This capability defines no forecast output.')
        report = module.summarize(self.data)
        self.assertEqual(report['notApplicableRecords'], 1)
        self.assertEqual(report['applicableAcceptanceRecords'], 239)
        self.assertFalse(report['requirements']['EA-001']['acceptanceSatisfied'])

    def test_dependency_cycles_rejected(self):
        self.data['requirements'][0]['dependencies'] = ['EA-002']
        self.data['requirements'][1]['dependencies'] = ['EA-001']
        with self.assertRaisesRegex(ValueError, 'cycle'):
            module.summarize(self.data)

    def test_ci_is_not_production(self):
        record = self.record('EA-005', 'G06')
        record['stage'] = 'ci'
        with self.assertRaisesRegex(ValueError, 'stage does not match'):
            module.summarize(self.data)

    def test_gate_and_customer_counts_remain_separate(self):
        report = module.summarize(self.data)
        self.assertEqual(sum(report['criterionStates'].values()), 20)
        self.assertEqual(sum(report['gateStates'].values()), 220)

    def test_ci_plus_current_identity_cannot_complete_customer_workflow(self):
        target = next(item for item in self.data['requirements'] if item['id'] == 'EA-001')
        self.evidence('ci-only', stage='ci')
        self.evidence('identity-only', stage='deployed')
        for record in target['criteria'] + target['gates']:
            evidence = 'identity-only' if record['id'] == 'G09' else 'ci-only'
            stage = 'deployed' if record['id'] == 'G09' else 'ci'
            self.assess(record, evidence, stage=stage)
        report = module.summarize(self.data, self.context())['requirements']['EA-001']
        self.assertTrue(report['acceptanceSatisfied'])
        self.assertFalse(report['productionWorkflowVerified'])
        self.assertFalse(report['complete'])

    def test_matching_and_mismatched_evidence_stages(self):
        record = self.record()
        self.evidence('source-pass')
        self.assess(record, 'source-pass')
        module.summarize(self.data)
        record['stage'] = 'ci'
        with self.assertRaisesRegex(ValueError, 'stage does not match'):
            module.summarize(self.data)

    def test_missing_assessment_stage_rejected(self):
        record = self.record()
        self.evidence('source-pass')
        self.assess(record, 'source-pass')
        del record['stage']
        with self.assertRaisesRegex(ValueError, 'explicit valid stage'):
            module.summarize(self.data)

    def test_duplicate_and_unknown_evidence_references_rejected(self):
        record = self.record()
        self.evidence('source-pass')
        self.assess(record, 'source-pass')
        record['evidence'].append('source-pass')
        with self.assertRaisesRegex(ValueError, 'Duplicate evidence references'):
            module.summarize(self.data)
        record['evidence'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'Unknown evidence reference'):
            module.summarize(self.data)

    def test_failed_assessment_requires_failed_evidence(self):
        record = self.record()
        self.evidence('passed-only')
        self.assess(record, 'passed-only', state='Failed')
        with self.assertRaisesRegex(ValueError, 'failed execution evidence'):
            module.summarize(self.data)

    def test_legitimate_release_level_failed_evidence_may_be_unreferenced(self):
        self.evidence('integrated-release-failure', stage='production', result='failed', disposition='release')
        module.summarize(self.data)
        self.data['evidence'][-1]['disposition'] = {'class': 'assessment'}
        with self.assertRaisesRegex(ValueError, 'not referenced'):
            module.summarize(self.data)

    def test_invalid_history_and_unknown_historical_reference_rejected(self):
        record = self.record()
        self.evidence('source-pass')
        self.assess(record, 'source-pass')
        record['assessmentHistory'][0]['state'] = 'Invented'
        with self.assertRaisesRegex(ValueError, 'Invalid historical assessment state'):
            module.summarize(self.data)
        record['assessmentHistory'][0].update(state='Failed', evidence=['removed'], stage='source')
        with self.assertRaisesRegex(ValueError, 'Unknown evidence reference in historical'):
            module.summarize(self.data)

    def test_malformed_evidence_timestamp_and_commit_rejected(self):
        item = self.evidence('malformed')
        item['executedAt'] = 'yesterday'
        with self.assertRaisesRegex(ValueError, 'Invalid evidence timestamp'):
            module.summarize(self.data)
        item['executedAt'] = '2026-11-28T00:00:00Z'
        item['commit'] = 'abc'
        with self.assertRaisesRegex(ValueError, 'full commit SHA'):
            module.summarize(self.data)

    def test_blocked_state_and_dependency_blockers_are_distinct(self):
        record = self.record('EA-002', 'EA-002-AC01')
        record.update(state='Blocked', evidence=[], reason='Awaiting an upstream official source.', blocker={'type': 'source', 'description': 'Publisher endpoint unavailable.'})
        report = module.summarize(self.data)
        own = report['requirements']['EA-002']
        downstream = report['requirements']['EA-003']
        self.assertTrue(any(item['currentState'] == 'Blocked' for item in own['directBlockers']))
        self.assertIn('EA-002', downstream['dependencyDerivedBlockers'])
        self.assertNotIn('EA-001', downstream['dependencyDerivedBlockers'])

    def test_mandatory_gate_declaration_is_required_and_immutable(self):
        del self.data['mandatoryGatePolicy']
        with self.assertRaisesRegex(ValueError, 'Missing mandatory'):
            module.summarize(self.data)
        self.setUp()
        self.data['mandatoryGatePolicy']['gateIds'] = ['G01']
        with self.assertRaisesRegex(ValueError, 'unauthorized'):
            module.summarize(self.data)

    def test_mandatory_gates_cannot_be_waived(self):
        gate = self.record('EA-001', 'G01')
        gate.update(state='Not applicable', evidence=[], reason='Attempted waiver')
        with self.assertRaisesRegex(ValueError, 'cannot be waived'):
            module.summarize(self.data)

    def test_current_release_can_complete_noncontinuous_requirement(self):
        self.verify_requirement('EA-001')
        report = module.summarize(self.data, self.context())
        self.assertTrue(report['requirements']['EA-001']['productionWorkflowVerified'])
        self.assertTrue(report['requirements']['EA-001']['complete'])

    def test_historical_release_is_stale_for_current_completion(self):
        self.verify_requirement('EA-001', 'a' * 40)
        report = module.summarize(self.data, self.context('b' * 40))
        self.assertFalse(report['requirements']['EA-001']['productionWorkflowVerified'])
        self.assertFalse(report['requirements']['EA-001']['complete'])
        self.assertGreater(report['currentStates']['Stale'], 0)

    def test_missing_release_context_withholds_current_completion(self):
        self.verify_requirement('EA-001')
        report = module.summarize(self.data)
        self.assertFalse(report['requirements']['EA-001']['productionWorkflowVerified'])
        self.assertGreater(report['currentStates']['Unavailable'], 0)

    def test_mixed_release_evidence_is_stale(self):
        record = self.record()
        self.evidence('old-production', stage='production', commit='a' * 40)
        self.evidence('new-production', stage='production', commit='b' * 40)
        self.assess(record, 'old-production', stage='production')
        record['evidence'].append('new-production')
        report = module.summarize(self.data, self.context('b' * 40))
        self.assertEqual(report['assessmentStates']['EA-001:EA-001-AC01']['currentState'], 'Stale')

    def test_commercial_evidence_does_not_replace_technical_production(self):
        self.verify_requirement('EA-001')
        gate = self.record('EA-001', 'G02')
        replaced = gate['evidence'][0]
        prior = next(item for item in self.data['evidence'] if item['id'] == replaced)
        prior['disposition'] = {'class': 'historical', 'reason': 'Replaced in this fixture by a commercial assessment.'}
        commercial = self.evidence('commercial-pass', stage='commercial')
        gate.update(stage='commercial', evidence=[commercial['id']], assessedAt='2026-11-28T00:00:01Z')
        report = module.summarize(self.data, self.context())
        self.assertFalse(report['requirements']['EA-001']['productionWorkflowVerified'])

    def test_unchanged_scope_can_carry_functional_evidence_forward(self):
        self.verify_requirement('EA-001', 'a' * 40)
        carried = []
        for item in self.data['evidence']:
            if item['id'].startswith('fixture-EA-001') and item['stage'] != 'deployed':
                item['releaseScope'] = {'policy': 'unchanged-assets', 'paths': ['site/business-intelligence/app.mjs']}
                carried.append(item['id'])
        report = module.summarize(self.data, self.context('b' * 40, carried))
        self.assertTrue(report['requirements']['EA-001']['productionWorkflowVerified'])

    def test_stale_nonworkflow_gate_prevents_current_readiness(self):
        self.verify_requirement('EA-001', 'a' * 40)
        gate = self.record('EA-001', 'G03')
        gate['stage'] = 'production'
        evidence = next(item for item in self.data['evidence'] if item['id'] == gate['evidence'][0])
        evidence.update(stage='production', deployedCommit='a' * 40)
        report = module.summarize(self.data, self.context('b' * 40))['requirements']['EA-001']
        self.assertFalse(report['currentAcceptanceSatisfied'])
        self.assertFalse(report['releaseReady'])

    def test_failure_resolution_preserves_failed_history(self):
        record = self.record()
        self.evidence('failed-run', result='failed')
        self.evidence('fixed-run')
        record.update(state='Verified', stage='source', evidence=['fixed-run'], assessedAt='2026-11-28T00:00:02Z', assessmentHistory=[
            dict(state='Pending', evidence=[], reason='Initial state.', assessedAt='2026-11-27T23:59:58Z'),
            dict(state='Failed', stage='source', evidence=['failed-run'], reason='Observed failure.', assessedAt='2026-11-28T00:00:01Z'),
        ])
        report = module.summarize(self.data)
        self.assertEqual(report['assessmentStates']['EA-001:EA-001-AC01']['state'], 'Verified')
        self.assertEqual(self.data['evidence'][-2]['result'], 'failed')

    def test_unsupported_transition_to_pending_is_rejected(self):
        record = self.record()
        record['assessmentHistory'] = [dict(state='Verified', stage='source', evidence=['ci-vault-59830a7e'], assessedAt='2026-11-27T17:30:00Z')]
        # The referenced evidence is CI, so fix the history stage to reach transition validation.
        record['assessmentHistory'][0]['stage'] = 'ci'
        with self.assertRaisesRegex(ValueError, 'Unsupported assessment state transition'):
            module.summarize(self.data)

    def test_ea020_can_be_release_ready_but_never_complete(self):
        self.verify_requirement('EA-020')
        report = module.summarize(self.data, self.context())['requirements']['EA-020']
        self.assertTrue(report['releaseReady'])
        self.assertFalse(report['complete'])

    def test_python_and_javascript_readiness_parity(self):
        self.verify_requirement('EA-001')
        context = self.context()
        python = module.summarize(copy.deepcopy(self.data), context)
        process = subprocess.run(
            ['node', 'tests/acceptance_summary_runner.mjs'],
            cwd=ROOT,
            input=json.dumps({'registry': self.data, 'releaseContext': context}),
            text=True,
            capture_output=True,
            check=True,
        )
        javascript = json.loads(process.stdout)
        for key in ('states', 'currentStates', 'criterionStates', 'gateStates', 'verifiedByStage', 'verifiedAcceptanceRecords', 'currentProductionVerifiedRecords', 'assessmentStates', 'requirements'):
            self.assertEqual(javascript[key], python[key], key)


if __name__ == '__main__':
    unittest.main()
