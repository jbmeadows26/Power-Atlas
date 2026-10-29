"""Independent checks of age-gap reproducibility, source cohort, and fail-closed behavior."""
import json
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_political_authenticity_age_comparison import ACS, STATES, build

def snapshot_fixture():
    members=[]
    for i in range(433):
        members.append({
            "bioguideId":f"A{i+1:06d}","chamber":"House","state":"NJ","district":i+1,
            "votingMember":True,"birthDate":"1996-06-01" if i<5 else "1976-06-01",
            "ageYears":30 if i<5 else 50})
    for i in range(100):
        members.append({
            "bioguideId":f"B{i+1:06d}","chamber":"Senate","state":sorted(STATES)[i//2],
            "district":None,"votingMember":True,"birthDate":"1966-06-01","ageYears":60})
    for i,state in enumerate(("DC","PR","GU","AS","VI","MP")):
        members.append({
            "bioguideId":f"C{i+1:06d}","chamber":"House","state":state,
            "district":0,"votingMember":False,"birthDate":"1966-06-01","ageYears":60})
    return {"asOf":"2026-10-29","source":"fixture-public-source",
            "sourceSha256":"fixture-digest","records":members}

class CensusRepresentationTests(unittest.TestCase):
    def test_population_baseline_reconciles(self):
        self.assertEqual(ACS["allResidents"],340110990)
        self.assertEqual(ACS["age25to34"],46198405)
        self.assertEqual(sum(v for k,v in ACS.items() if k!="allResidents"), ACS["allResidents"])
        self.assertEqual(sum(ACS[k] for k in ("age25to34","age35to44","age45to54","age55to64","age65plus")),235910719)
    def test_gap_and_nonvoting_exclusion(self):
        result=build(snapshot_fixture())
        self.assertEqual(result["houseVotingCount"],433)
        self.assertEqual(result["houseVotingAge25to34Count"],5)
        self.assertEqual(result["houseMinusPopulation25to34PercentagePoints"],-18.428)
        self.assertEqual(result["houseVsPopulation25to34Ratio"],0.059)
        self.assertEqual(result["houseVotingMeanAgeYears"],49.77)
    def test_reject_duplicate_bioguide_id(self):
        snap=snapshot_fixture()
        snap["records"][1]["bioguideId"]=snap["records"][0]["bioguideId"]
        with self.assertRaises(ValueError):build(snap)
    def test_reject_duplicate_house_seat(self):
        snap=snapshot_fixture()
        snap["records"][1]["district"]=snap["records"][0]["district"]
        with self.assertRaises(ValueError):build(snap)
    def test_reject_incorrect_age(self):
        snap=snapshot_fixture()
        snap["records"][0]["ageYears"]=31
        with self.assertRaises(ValueError):build(snap)
    def test_reject_nonvoting_delegate_counted_as_voting(self):
        snap=snapshot_fixture()
        snap["records"][-1]["votingMember"]=True
        with self.assertRaises(ValueError):build(snap)
    def test_reject_three_senators_from_one_state(self):
        snap=snapshot_fixture()
        senators=[r for r in snap["records"] if r["chamber"]=="Senate"]
        senators[0]["state"]=senators[2]["state"]
        with self.assertRaises(ValueError):build(snap)
    def test_reject_missing_birth_date(self):
        snap=snapshot_fixture()
        snap["records"][0]["birthDate"]=None
        with self.assertRaises(ValueError):build(snap)
    def test_reject_missing_senator(self):
        snap=snapshot_fixture()
        snap["records"]=[r for r in snap["records"] if r["bioguideId"]!="B000100"]
        with self.assertRaises(ValueError):build(snap)
    def test_published_snapshot_matches_checked_in_comparison(self):
        source=ROOT/"data/research/political-authenticity/members.json"
        comparison=ROOT/"data/research/political-authenticity/age-comparison.json"
        if not source.exists() or not comparison.exists():
            self.skipTest("Historical snapshot not present in checkout")
        computed=build(json.loads(source.read_text(encoding="utf-8")))
        expected=json.loads(comparison.read_text(encoding="utf-8"))
        self.assertEqual(computed,expected,"Persisted comparison must match persisted member source")
if __name__=="__main__":unittest.main()
