"""Guardrail tests: all real-world IDI inference is withheld until construct validation."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from idi_research_gate import assess,evaluate,bounded

class IdiResearchGateTests(unittest.TestCase):
    def test_corrected_reference_algebra(self):
        doc=json.loads((ROOT/"data/research/political-authenticity/idi-synthetic.json").read_text())
        rows={x["memberId"]:x for x in assess(doc)["records"]}
        self.assertAlmostEqual(rows["SYNTH-001"]["point"],0.8105)
        self.assertAlmostEqual(rows["SYNTH-002"]["point"],0.152)
        self.assertEqual(rows["SYNTH-005"]["point"],0)
    def test_interval_propagation(self):
        row=evaluate({"memberId":"demo","W":[.2,.4],"O":.5,"S":[.4,.6],"C":.2})
        self.assertAlmostEqual(row["low"],.345)
        self.assertAlmostEqual(row["high"],.465)
        self.assertIsNone(row["point"])
    def test_no_imputation_for_missing_components(self):
        row=evaluate({"memberId":"demo","W":None,"O":0,"S":1,"C":0})
        self.assertIsNone(row["point"])
        self.assertEqual(row["missing"],["W"])
    def test_reject_out_of_range_and_reversed_intervals(self):
        for x in [-.01,1.01,float("nan"),float("inf"),True,[.8,.2]]:
            with self.assertRaises(ValueError):bounded(x)
    def test_refuse_any_real_member_score_without_validation(self):
        r=evaluate({"memberId":"M001","W":.1,"O":.9,"S":.4,"C":.2},kind="observed")
        self.assertEqual(r["status"],"not_validated_for_public_ranking")
        self.assertIsNone(r["point"])
    def test_reject_duplicate_records(self):
        doc=json.loads((ROOT/"data/research/political-authenticity/idi-synthetic.json").read_text())
        doc["records"].append(dict(doc["records"][0]))
        with self.assertRaises(ValueError):assess(doc)
if __name__=="__main__":unittest.main()
