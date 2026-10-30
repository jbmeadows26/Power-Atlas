"""Washington PDC grouped finance only, no individual contributor data."""
import json,unittest
from scripts.collect_wa_campaign_finance_aggregate import parse,BASE,YEARS

def fake():
    return json.dumps([
        {"election_year":"2020","filer_type":"Candidate","rows":"6","contributions":"10000.12","expenditures":"9500.30"},
        {"election_year":"2022","filer_type":"Candidate","rows":"8","contributions":"20000","expenditures":"19000"},
        {"election_year":"2024","filer_type":"Candidate","rows":"12","contributions":"30000.2","expenditures":"29000.12"},
        {"election_year":"2024","filer_type":"Other","rows":"1","contributions":"100000000","expenditures":"5000000"},
    ]).encode()
URL=BASE+"?$select=aggregates"

class WAGroupedFinance(unittest.TestCase):
    def test_no_identity_fields(self):
        d=parse(fake(),URL)
        self.assertEqual(d["state"],"WA")
        self.assertEqual(d["categoryRows"],3)
        self.assertEqual(d["suppressedSmallGroupsCount"],1)
        self.assertFalse(d["campaignFinanceCompleteForWA"])
        self.assertTrue(all(v["publishedSummaryRows"]>=5 for v in d["records"]))
        self.assertTrue(all(set(v)=={"electionYear","filerType","publishedSummaryRows",
                  "sumOfPublishedContributionsUSD","sumOfPublishedExpendituresUSD","status"} for v in d["records"]))
    def test_amounts_and_dollar_units_preserved(self):
        d=parse(fake(),URL)
        r=next(x for x in d["records"] if x["electionYear"]==2020)
        self.assertEqual(r["sumOfPublishedContributionsUSD"],"10000.12")
        self.assertEqual(r["sumOfPublishedExpendituresUSD"],"9500.30")
    def test_duplicated_source_group_fails(self):
        d=json.loads(fake())
        d.append(d[0])
        with self.assertRaisesRegex(ValueError,"Duplicated"):
            parse(json.dumps(d).encode(),URL)
    def test_missing_year_fails(self):
        d=[x for x in json.loads(fake()) if x["election_year"]!="2022"]
        with self.assertRaisesRegex(ValueError,"missing expected"):
            parse(json.dumps(d).encode(),URL)
    def test_license_gate_visible(self):
        d=parse(fake(),URL)
        self.assertIn("noncommercial",d["licensingGate"])
        self.assertNotIn("donor",str(d["records"]).lower())
        self.assertEqual(d["groupBy"],"election_year, filer_type")
if __name__=="__main__":unittest.main()
