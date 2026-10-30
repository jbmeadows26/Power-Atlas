"""Negative and reproducibility tests for 119th House geography."""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from build_authenticity_district_crosswalk import SEATS,build
def fixture():
    states={"schema":"power-atlas.states.v1","states":[{"postal":s,"fips":f"{i+1:02d}"} for i,s in enumerate(sorted(SEATS))]}
    rows=[];i=0
    for s,n in SEATS.items():
        for d in ([0] if n==1 else range(1,n+1)):
            i+=1
            if (s,d) in (("FL",20),("TX",23)):continue
            rows.append({"bioguideId":f"A{i:06d}","chamber":"House","state":s,"district":d,"votingMember":True,"ageYears":50})
    return {"schema":"power-atlas.representation-members.v1","asOf":"2026-10-29","source":"fixture","sourceSha256":"fixture","records":rows},states
class Tests(unittest.TestCase):
    def test_full_keys_and_vacancies(self):
        a,b=fixture();x=build(a,b)
        self.assertEqual((x["seatCount"],x["occupiedSeatCount"],x["vacantSeatCount"]),(435,433,2))
        self.assertEqual({r["seatKey"] for r in x["records"] if r["memberBioguideId"] is None},{"FL-20","TX-23"})
        self.assertEqual(next(r["censusDistrictCode"] for r in x["records"] if r["state"]=="AK"),"00")
        self.assertTrue(all(r["acs2025Age25to34Estimate"] is None and r["acs2025Age25to34MOE"] is None for r in x["records"]))
    def test_bad_district_rejected(self):
        a,b=fixture();a["records"][0]["district"]=999
        with self.assertRaises(ValueError):build(a,b)
    def test_fictitious_433_nj_districts_rejected(self):
        a,b=fixture()
        for r in a["records"]:r["state"]="NJ"
        with self.assertRaises(ValueError):build(a,b)
    def test_duplicate_seat_rejected(self):
        a,b=fixture()
        a["records"][1]["state"]=a["records"][0]["state"]
        a["records"][1]["district"]=a["records"][0]["district"]
        with self.assertRaises(ValueError):build(a,b)
    def test_bad_fips_rejected(self):
        a,b=fixture();b["states"][0]["fips"]="bad"
        with self.assertRaises(ValueError):build(a,b)
    def test_checked_in_reproducibility(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        paths=[root/"data/research/political-authenticity/members.json",root/"data/geography/states.json",root/"data/research/political-authenticity/house-district-crosswalk-119.json"]
        if not all(p.exists() for p in paths):self.skipTest("Dataset not yet committed")
        a,b,c=[json.loads(p.read_text()) for p in paths]
        self.assertEqual(c["memberSnapshotDate"], a["asOf"], "Crosswalk must track current member snapshot date")
        self.assertEqual(build(a,b),c)
if __name__=="__main__":unittest.main()
