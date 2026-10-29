"""Behavioral, not fabricated-data, tests for political representation collector."""
import datetime as dt
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from collect_political_authenticity import age_at, valid_term, collect

class RepresentationCollectorTests(unittest.TestCase):
    def setUp(self):
        self.day=dt.date(2026,10,29)
        self.roster={"records":[
            {"bioguideId":"A000001","name":"Synthetic A","chamber":"House","state":"NJ","district":5,"party":"Democrat","source":"https://bioguide.congress.gov/search/bio/A000001"},
            {"bioguideId":"B000002","name":"Synthetic B","chamber":"Senate","state":"CA","party":"Republican","source":"https://bioguide.congress.gov/search/bio/B000002"}
        ]}
        self.biographies=[
            {"id":{"bioguide":"A000001"},"bio":{"birthday":"1980-10-29"},"terms":[{"type":"rep","state":"NJ","district":5,"start":"2025-01-03","end":"2027-01-03"}]},
            {"id":{"bioguide":"B000002"},"bio":{"birthday":"1955-10-30"},"terms":[{"type":"sen","state":"CA","start":"2025-01-03","end":"2031-01-03"}]}
        ]
    def test_age_boundary(self):
        self.assertEqual(age_at("1980-10-29",self.day),46)
        self.assertEqual(age_at("1955-10-30",self.day),70)
    def test_term_and_district_must_match(self):
        self.assertTrue(valid_term(self.roster["records"][0],self.biographies[0],self.day))
        self.biographies[0]["terms"][0]["district"]=4
        self.assertFalse(valid_term(self.roster["records"][0],self.biographies[0],self.day))
    def test_duplicate_identity_rejected_before_publication(self):
        self.roster["records"]*=270
        with self.assertRaises(ValueError):
            collect(self.roster,self.biographies,self.day,"sha")
    def test_incomplete_sources_rejected(self):
        with self.assertRaises(ValueError):
            collect(self.roster,self.biographies,self.day,"sha")
    def test_no_estimated_political_or_wealth_data(self):
        self.roster["records"]=[dict(self.roster["records"][0],bioguideId=f"A{i:06d}",name=f"Synthetic {i}") for i in range(501)]
        self.biographies=[dict(self.biographies[0],id={"bioguide":f"A{i:06d}"}) for i in range(501)]
        snapshot,coverage=collect(self.roster,self.biographies,self.day,"sha")
        self.assertEqual(coverage["ageKnown"],501)
        self.assertEqual(coverage["wealthKnown"],0)
        self.assertTrue(all(x["wealthIntervalUsd"] is None and x["occupationBeforePolitics"] is None for x in snapshot["records"]))
if __name__=="__main__":unittest.main()
