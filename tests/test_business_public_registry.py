import json,unittest
from pathlib import Path
from scripts.build_business_analyst_registry import build
ROOT=Path(__file__).resolve().parents[1]
class PublicRegistryTests(unittest.TestCase):
 def test_registry_never_infers_execution_from_code(self):
  r=build([]);self.assertEqual(len(r['analysts']),18)
  self.assertTrue(all(a['lastSuccessfulExecution'] is None and a['operationalStatus']!='operational' for a in r['analysts']))
 def test_failure_preserves_success_and_is_not_operational(self):
  runs=[{'workflowName':'Eastern Axis physical early warning','conclusion':'failure','updatedAt':'2026-11-27T00:00:00Z','url':'https://github.com/example/failure'}, {'workflowName':'Eastern Axis physical early warning','conclusion':'success','updatedAt':'2026-11-26T00:00:00Z','url':'https://github.com/example/success'}]
  a=build(runs)['analysts'][0];self.assertEqual(a['operationalStatus'],'failed');self.assertEqual(a['lastSuccessfulExecution'],'2026-11-26T00:00:00Z')
 def test_case_is_historical_attributable_and_isolated(self):
  c=json.loads((ROOT/'site/business-intelligence/data/public-case.json').read_text())
  self.assertEqual(c['source']['publicationDate'],'2022-11-06');self.assertIn('Historical',c['caseType']);self.assertIn('Never inserted',c['isolation']);self.assertEqual(len(c['source']['retrievedHtmlSha256']),64)
  js=(ROOT/'site/business-intelligence/public-intelligence.mjs').read_text();self.assertNotIn('localStorage',js);self.assertNotIn('innerHTML',js);self.assertNotIn('approve(',js)
 def test_licensing_does_not_clear_commercial_launch(self):
  d=json.loads((ROOT/'business-intelligence/commercial-licensing.json').read_text());self.assertFalse(d['reviewedCommercialClearance']);self.assertTrue(d['commercialLaunch'].startswith('blocked'))
