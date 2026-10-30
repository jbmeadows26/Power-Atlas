"""State-level research must not confuse authority links with verified ingested facts."""
import unittest
from scripts.build_six_gap_coverage import build,DOMAINS

class SixGaps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=build()
    def test_50_state_six_domain_grid(self):
        self.assertEqual(self.data["jurisdictions"],50)
        self.assertEqual(len(self.data["records"]),300)
        self.assertEqual(len({r["id"] for r in self.data["records"]}),300)
        self.assertEqual(set(self.data["coverage"]),set(DOMAINS))
        self.assertTrue(all(v["jurisdictionsIndexed"]==50 for v in self.data["coverage"].values()))
    def test_no_false_claims_of_inferred_completeness(self):
        self.assertTrue(all(v["jurisdictionsCompleted"]==0 for v in self.data["coverage"].values()))
        self.assertTrue(all(r["recordsIngested"]==0 for r in self.data["records"]))
        self.assertTrue(all(r["reviewRequired"] for r in self.data["records"]))
        self.assertIn("not_coverage_completion",self.data["publicationStatus"])
    def test_official_source_discovery_distinct_from_record_collection(self):
        geo=[x for x in self.data["records"] if x["domain"].startswith("state_legislative_district_polygons")]
        self.assertEqual(len(geo),50)
        self.assertTrue(all("censusLayerIndex" in r["sourceDiscovery"] for r in geo))
        self.assertTrue(all(r["coverageStatus"]!="complete" for r in geo))
    def test_jurisdiction_exclusions_are_explicit(self):
        self.assertTrue(self.data["additionalDistrictOfColumbiaElectionAuthorityKnown"])
        self.assertFalse(any(r["state"]=="DC" for r in self.data["records"]))

if __name__=="__main__":
    unittest.main()
