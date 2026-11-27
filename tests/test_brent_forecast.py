import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('brent',ROOT/'eastern-axis/scripts/forecast_brent.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class BrentTests(unittest.TestCase):
 def setUp(self):
  self.source=json.loads((ROOT/'eastern-axis/public/analysis/physical-early-warning.json').read_text())
  self.source['checkedAt']='2026-11-27T00:00:00Z'
  self.history=next(x for x in self.source['metrics'] if x['id']=='worldbank-brent')['history']
  self.proof={'historyHash':m.digest(self.history),'sha256':'fixture-only'}
 def report(self):return m.build(self.source,'2026-11-27T12:00:00Z',self.proof)
 def test_actual_retained_history_evaluation_and_no_superiority_claim(self):
  r=self.report();self.assertEqual(r['targetPeriod'],'2026-12');self.assertEqual(r['evaluation']['origins'],23)
  self.assertEqual(r['evaluation']['beatsPersistence'],r['evaluation']['mae']<r['evaluation']['persistenceMae'])
 def test_no_lookahead(self):
  before=m.evaluate(self.history);after=deepcopy(self.history);after[-1]['value']=999
  changed=m.evaluate(after)
  self.assertEqual(before[:-1],changed[:-1]);self.assertEqual(before[-1]['predicted'],changed[-1]['predicted'])
 def test_source_failure_withholds_but_preserves_retrospective_evaluation(self):
  r=m.build(self.source,'2026-11-27T12:00:00Z');self.assertNotIn('forecastId',r);self.assertNotIn('predicted',r);self.assertIn('evaluation',r)
 def test_gaps_future_stale_invalid_values_withhold(self):
  for mut in [lambda h:h.pop(5),lambda h:h[5].update(value=None),lambda h:h[5].update(value=True),lambda h:h[5].update(value=float('nan'))]:
   data=deepcopy(self.source);hist=next(x for x in data['metrics'] if x['id']=='worldbank-brent')['history'];mut(hist)
   self.assertNotIn('forecastId',m.build(data,'2026-11-27T12:00:00Z',self.proof))
  self.assertNotIn('forecastId',m.build(self.source,'2026-12-01T00:00:00Z',self.proof))
 def test_append_only_idempotent_and_tampering_detected(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'events.jsonl';r=self.report();self.assertEqual(m.append_events(path,r,self.source),1)
   old=path.read_bytes();self.assertEqual(m.append_events(path,r,self.source),0);self.assertEqual(path.read_bytes(),old)
   path.write_text(path.read_text().replace('110.9','999.9'))
   with self.assertRaises(ValueError):m.append_events(path,r,self.source)
 def test_outcomes_append_without_changing_issued_forecast(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'events.jsonl';r=self.report();m.append_events(path,r,self.source);old=path.read_bytes()
   later=deepcopy(r);later['forecastId']='test-next-issue';later['supportingObservations'].append({'period':'2026-12','value':150});later['createdAt']='2027-01-20T00:00:00Z'
   self.assertEqual(m.append_events(path,later,self.source),2);self.assertTrue(path.read_bytes().startswith(old))
   event=json.loads(path.read_text().splitlines()[1]);self.assertEqual(event['kind'],'outcome');self.assertAlmostEqual(event['absoluteError'],39.1)
