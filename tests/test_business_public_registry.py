import json,unittest
from pathlib import Path
from scripts.build_business_analyst_registry import build
ROOT=Path(__file__).resolve().parents[1]
def receipt(run, conclusion, updated, workflow='Eastern Axis physical early warning', stages=None):
 value={'workflowName':workflow,'conclusion':conclusion,'updatedAt':updated,
        'url':f'https://github.com/jbmeadows26/Power-Atlas/actions/runs/{run}',
        'headSha':'a'*40}
 if stages is not None:value['stageEvidence']=stages
 return value
class PublicRegistryTests(unittest.TestCase):
 def test_registry_never_infers_execution_from_code(self):
  r=build([]);self.assertEqual(len(r['analysts']),18)
  self.assertTrue(all(a['lastSuccessfulExecution'] is None and a['operationalStatus']!='operational' for a in r['analysts']))
  self.assertTrue(all(a['productionVerificationStatus']=='unavailable' for a in r['analysts']))
 def test_failure_preserves_success_and_is_not_operational(self):
  runs=[receipt(2,'failure','2026-11-27T00:00:00Z',stages={'analysis':{'status':'failed','evidence':['offline test failed'],'failureClassification':'analysis-test','reason':'fixture'}}),
        receipt(1,'success','2026-11-26T00:00:00Z',stages={'analysis':{'status':'success','evidence':['offline test passed']}})]
  a=build(runs)['analysts'][0];self.assertNotEqual(a['operationalStatus'],'operational');self.assertEqual(a['lastSuccessfulExecution'],'2026-11-26T00:00:00Z');self.assertEqual(len(a['executionStages']['analysis']['history']),2)
 def test_case_is_historical_attributable_and_isolated(self):
  c=json.loads((ROOT/'site/business-intelligence/data/public-case.json').read_text())
  self.assertEqual(c['source']['publicationDate'],'2022-11-06');self.assertIn('Historical',c['caseType']);self.assertIn('Never inserted',c['isolation']);self.assertEqual(len(c['source']['retrievedHtmlSha256']),64)
  js=(ROOT/'site/business-intelligence/public-intelligence.mjs').read_text();self.assertNotIn('localStorage',js);self.assertNotIn('innerHTML',js);self.assertNotIn('approve(',js)
 def test_licensing_does_not_clear_commercial_launch(self):
  d=json.loads((ROOT/'business-intelligence/commercial-licensing.json').read_text());self.assertFalse(d['reviewedCommercialClearance']);self.assertTrue(d['commercialLaunch'].startswith('blocked'))
 def test_public_ui_displays_stage_axes_and_retained_artifact_semantics(self):
  js=(ROOT/'site/business-intelligence/public-intelligence.mjs').read_text()
  for phrase in ('analysis ${a.analyticalStatus}','publication ${a.publicationStatus}','production ${a.productionVerificationStatus}','Retained artifact generated'):
   self.assertIn(phrase,js)
 def test_control_center_uses_canonical_analyst_registry_and_preserves_failure_history(self):
  html=(ROOT/'site/development-control/index.html').read_text()
  js=(ROOT/'site/development-control/app.mjs').read_text()
  self.assertIn('id="analysts"',html)
  self.assertIn("business-intelligence/data/analyst-registry.json",js)
  self.assertIn('analysis ${analyst.analyticalStatus}',js)
  self.assertIn('production ${analyst.productionVerificationStatus}',js)
  self.assertIn('Historical failures remain visible after later success.',js)
  self.assertNotIn("operationalStatus==='operational'",js)
