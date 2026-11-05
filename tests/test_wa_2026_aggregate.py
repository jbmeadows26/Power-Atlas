"""WA 2026 PDC aggregation privacy and source-schema regression tests."""
import unittest
from scripts import collect_wa_2026_aggregate as m

class Wa2026GroupTests(unittest.TestCase):
    def sample(self,n=9,year="2026"):
        return [{"election_year":year,"filer_type":"Statewide political committees",
                 "rows":str(n),"contributions":"70000.10","expenditures":"40000.25",
                 "contributor_name":"PRIVATE PERSON MUST BE DISCARDED",
                 "street_address":"PRIVATE ADDRESS MUST BE DISCARDED"}]
    def test_server_aggregated_only(self):
        data=m.parse(self.sample())
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]["sumOfPublishedContributionsUSD"],"70000.10")
        self.assertNotIn("PRIVATE",str(data))
        self.assertTrue(all(x["publishedSummaryRows"]>=5 for x in data))
    def test_small_group_suppressed(self):
        with self.assertRaises(ValueError):m.parse(self.sample(n=2))
    def test_wrong_year_rejected(self):
        with self.assertRaises(ValueError):m.parse(self.sample(year="2024"))
    def test_duplicate_class_rejected(self):
        with self.assertRaises(ValueError):m.parse(self.sample()+self.sample())

if __name__=="__main__": unittest.main()
