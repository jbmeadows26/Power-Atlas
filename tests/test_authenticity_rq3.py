"""RQ3 vote/preference joining gates; tests use fictional vote preferences only."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from rq3_responsiveness import validate
def fixture():
    rows=[]
    for roll in range(1,151):
        for member in range(20):
            rows.append({"member_id":f"TEST{member}","district_id":f"TEST-{member}",
              "roll_id":f"house-2025-{roll:03d}","vote_date":"2025-06-30",
              "preferences_as_of":"2025-06-01","yea":str((roll+member)%2),"issue":"economy",
              "p_bottom":"0.4","p_middle":"0.5","p_top":"0.6",
              "n_bottom":"40","n_middle":"40","n_top":"40",
              "source":f"https://clerk.house.gov/evs/2025/roll{roll:03d}.xml"})
    return rows
manifest={"status":"preregistered_verified_issue_preferences","congress":119,
          "preselectedRollIds":[f"house-2025-{x:03d}" for x in range(1,151)]}
class RQ3Tests(unittest.TestCase):
    def test_complete_preregistered_rolls(self):
        self.assertEqual(len(validate(fixture(),manifest)),3000)
    def test_empty_research_manifest_rejects_analysis(self):
        with self.assertRaises(ValueError):validate(fixture(),dict(manifest,status="NOT_PREREGISTERED"))
    def test_nonvotes_not_treated_as_nays(self):
        rows=fixture();rows[0]["yea"]="-1"
        with self.assertRaises(ValueError):validate(rows,manifest)
    def test_no_postvote_survey(self):
        rows=fixture();rows[0]["preferences_as_of"]="2025-07-01"
        with self.assertRaises(ValueError):validate(rows,manifest)
    def test_no_sparse_income_subgroups(self):
        rows=fixture();rows[0]["n_bottom"]="2"
        with self.assertRaises(ValueError):validate(rows,manifest)
    def test_no_posthoc_selected_roll(self):
        rows=fixture();rows[0]["roll_id"]="house-2026-001"
        with self.assertRaises(ValueError):validate(rows,manifest)
if __name__=="__main__":unittest.main()
