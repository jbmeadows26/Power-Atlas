"""RQ1 input contracts; no respondent microdata or synthetic fit published."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from rq1_gee import check
def fixture():
    rows=[]
    for d in range(30):
        for i in range(15):
            rows.append({"district_id":f"TEST-{d:02d}","efficacy_v242200":str(1+i%5),
              "weight":"1.5","income_percentile":str((i+.5)/15),"age":"35",
              "member_sfi":str(d/29),"partisan_lean":"0.1","incumbent_tenure":"4",
              "party_match":"1"})
    return rows
manifest={"status":"reviewed_licensed_microdata","congress":119,"geoBasis":"released_congressional_district","weightsValidated":True,"sfiCalibrationApproved":True}
class RQ1Tests(unittest.TestCase):
    def test_respondent_schema_and_valid_item_coding(self):
        r=check(fixture(),manifest)
        self.assertEqual(len(r),450)
        self.assertEqual(r[0]["alienated"],1)
        self.assertEqual(r[2]["alienated"],0)
    def test_reject_zip4_sensitive_join(self):
        rows=fixture()
        rows[0]["zip4"]="1234"
        with self.assertRaises(ValueError):check(rows,manifest)
    def test_unreviewed_inputs_denied(self):
        with self.assertRaises(ValueError):check(fixture(),dict(manifest,weightsValidated=False))
    def test_distict_misalignment_denied(self):
        rows=fixture()
        rows[2]["member_sfi"]="0.6"
        with self.assertRaises(ValueError):check(rows,manifest)
    def test_invalid_nonresponse_denied(self):
        rows=fixture()
        rows[0]["efficacy_v242200"]="-9"
        with self.assertRaises(ValueError):check(rows,manifest)
if __name__=="__main__":unittest.main()
