"""Original WA official 2023–24 rollcall source-level integrity tests."""
import json,unittest
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/"data/legislation/wa-2023-24-rollcalls/source-rollcalls.json"
class WashingtonRollCallSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(BASE.read_text(encoding="utf8"))
        cls.rows=cls.d["records"]
    def test_original_official_source_provenance(self):
        self.assertEqual(self.d["state"],"WA")
        self.assertEqual(self.d["biennium"],"2023-24")
        self.assertGreater(self.d["rollCalls"],10)
        self.assertEqual(self.d["rollCalls"],len(self.rows))
        self.assertGreater(self.d["memberVoteRows"],250)
        self.assertTrue(all(r["sourceOfficialURL"].startswith(
            "https://wslwebservices.leg.wa.gov/LegislationService.asmx/GetRollCalls") for r in self.rows))
        self.assertTrue(all(len(r["sha256OriginalResponse"])==64 for r in self.rows))
    def test_member_positions_sum_to_recorded_yea_nay_absent_excused(self):
        for row in self.rows:
            c=Counter(v["vote"] for v in row["memberVotes"])
            for code,field in (("Yea","YeaVotes"),("Nay","NayVotes"),
                               ("Absent","AbsentVotes"),("Excused","ExcusedVotes")):
                self.assertEqual(c[code],row["summary"][field])
            self.assertEqual(len({v["memberId"] for v in row["memberVotes"]}),
                             len(row["memberVotes"]))
    def test_cannot_claim_full_state_biennium_or_nationwide_completion(self):
        self.assertFalse(self.d["historicalSessionComplete"])
        self.assertFalse(self.d["allStateRollCallsComplete"])
        self.assertIn("sample",self.d["publicationStatus"])
        self.assertEqual(self.d["billsRequested"],42)
        self.assertEqual(len({r["id"] for r in self.rows}),len(self.rows))
if __name__=="__main__": unittest.main()
