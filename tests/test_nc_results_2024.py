"""Official North Carolina 2024 precinct-results QA and certified statewide spotchecks."""
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/elections/nc-2024"
class NC2024OfficialResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta=json.loads((BASE/"reconciliation.json").read_text())
        cls.county=json.loads((BASE/"county-choice-totals.json").read_text())
        cls.judges=json.loads((BASE/"judicial-candidate-totals.json").read_text())
    def test_source_integrity(self):
        raw=(BASE/"original-results-2024.zip").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
          "2fab44e9b12e03c0d88ef832c2e6dc8c569e2b020d64df06a8b551b62bbdb426")
        self.assertEqual(self.meta["sourceZIPOriginalBytes"],len(raw))
        self.assertEqual(self.meta["state"],"NC")
        self.assertEqual(self.meta["electionDate"],"2024-11-05")
    def test_all_one_hundred_counties_represented(self):
        counties={r["county"] for r in self.county}
        self.assertEqual(len(counties),100)
        self.assertEqual(self.meta["countiesWithVotes"],100)
        self.assertGreater(self.meta["precinctCandidateRowsInspected"],50000)
        self.assertEqual(self.meta["countyContestChoiceRows"],len(self.county))
        self.assertEqual(len(set((r["county"],r["contest"],r["choice"],r["party"]) for r in self.county)),len(self.county))
    def test_certified_statewide_spot_checks(self):
        checks=self.meta["certifiedSpotChecks"]
        self.assertEqual(len(checks),4)
        self.assertTrue(self.meta["spotChecksAllMatch"],"Mismatch must be investigated against certified canvass")
        self.assertTrue(all(r["difference"]==0 for r in checks))
        expected={("US PRESIDENT","Donald J. Trump"):2898424,("US PRESIDENT","Kamala D. Harris"):2715378,
                  ("NC GOVERNOR","Josh Stein"):3069499,("NC GOVERNOR","Mark Robinson"):2241310}
        self.assertEqual({(r["contest"],r["choice"]):r["certifiedVotes"] for r in checks},expected)
    def test_judicial_outcomes_are_source_based_not_falsely_certified(self):
        self.assertGreater(len(self.judges),5)
        self.assertEqual(self.meta["judicialContestChoiceRows"],len(self.judges))
        self.assertTrue(all("not_independently_certified" in r["certificationStatus"] for r in self.judges))
        self.assertTrue(all(r["votes"]>=0 for r in self.judges))
        self.assertIn("NOT proof every local race",self.meta["reconciliationInterpretation"])
    def test_source_avoids_privacy_noised_precinct_sorts(self):
        self.assertIn("noised",self.meta["exclusions"])
        self.assertTrue(self.meta["certifiedCanvassSourceURL"].startswith("https://s3.amazonaws.com/dl.ncsbe.gov/"))
if __name__=="__main__": unittest.main()
