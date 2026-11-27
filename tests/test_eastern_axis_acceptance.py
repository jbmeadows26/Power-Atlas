import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('registry', ROOT / 'scripts/validate_eastern_axis_acceptance.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'site/development-control/acceptance.json').read_text())

    def test_pending_is_not_completed(self):
        report = module.summarize(self.data)
        self.assertEqual(report['verifiedAcceptanceRecords'], 0)
        self.assertEqual(report['applicableAcceptanceRecords'], 240)
        self.assertFalse(any(r['complete'] for r in report['requirements'].values()))

    def test_verified_requires_executed_evidence(self):
        self.data['requirements'][0]['criteria'][0]['state'] = 'Verified'
        with self.assertRaisesRegex(ValueError, 'requires evidence'):
            module.summarize(self.data)

    def test_missing_gate_rejected(self):
        self.data['requirements'][0]['gates'].pop()
        with self.assertRaisesRegex(ValueError, 'Missing or duplicate'):
            module.summarize(self.data)

    def test_inapplicable_is_excluded_not_passed(self):
        self.data['requirements'][0]['gates'][3].update(state='Not applicable', reason='No forecast in this capability')
        report = module.summarize(self.data)
        self.assertEqual(report['applicableAcceptanceRecords'], 239)
        self.assertEqual(report['notApplicableRecords'], 1)
        self.assertEqual(report['verifiedAcceptanceRecords'], 0)

    def test_data_cannot_be_waived(self):
        self.data['requirements'][0]['gates'][0]['state'] = 'Not applicable'
        with self.assertRaisesRegex(ValueError, 'mandatory'):
            module.summarize(self.data)

    def test_cycles_rejected(self):
        self.data['requirements'][0]['dependencies'] = ['EA-002']
        self.data['requirements'][1]['dependencies'] = ['EA-001']
        with self.assertRaisesRegex(ValueError, 'cycle'):
            module.summarize(self.data)

    def test_failed_evidence_rejected(self):
        record = self.data['requirements'][0]['criteria'][0]
        record.update(state='Verified', evidence=['test'])
        self.data['evidence'].append(dict(id='test', executedAt='2026-11-27T00:00:00Z', commit='a'*40, artifact='test-log', method='unit', scope='source', result='failed'))
        with self.assertRaisesRegex(ValueError, 'Failed or unexecuted'):
            module.summarize(self.data)


if __name__ == '__main__':
    unittest.main()
