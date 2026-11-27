import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'eastern-axis/scripts'))
from forecast_governance import assess
class Governance(unittest.TestCase):
 def test_empty_is_experimental_not_zero_error(self):
  r=assess([]);self.assertIsNone(r['prospectiveMAE']);self.assertFalse(r['eligibleForIndependentReview'])
 def test_retrospective_and_duplicate_targets_do_not_inflate(self):
  rows=[]
  for i in range(20):
   rows.extend([{'kind':'issued','forecastId':str(i),'recordedAt':'2026-12-01T00:00:00+00:00','forecast':{'targetPeriod':'2027-01','methodologyVersion':'brent-3month-mean-h2-v1'}},{'kind':'outcome','forecastId':str(i),'absoluteError':2,'baselineAbsoluteError':1}])
  r=assess(rows);self.assertEqual(r['prospectiveTargets'],1);self.assertFalse(r['eligibleForIndependentReview']);self.assertEqual(r['prospectiveMAE'],2)
