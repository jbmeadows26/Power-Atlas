"""Official California records are not interchangeable with secondary keyword index coverage."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class CaliforniaOfficialSpotcheckTests(unittest.TestCase):
    def test_official_ab604_and_ca_keyword_gap_remain_separate(self):
        doc = read("data/legislation/official-california-redistricting-2025.json")
        checkpoint = read("data/legislation/state-redistricting-jurisdictions.json")
        indexed = read("data/legislation/state-redistricting-bills.json")
        self.assertEqual(doc["jurisdiction"], "CA")
        self.assertEqual(doc["queryDiscrepancy"]["reportedMatches"], 21)
        self.assertEqual(checkpoint["jurisdictions"]["CA"]["totalMatchesReported"], 21)
        self.assertEqual(checkpoint["jurisdictions"]["CA"]["persistedCandidateRows"], 0)
        self.assertFalse(any(r["state"] == "CA" for r in indexed["records"]))
        self.assertEqual(len(indexed["records"]), 617)
        self.assertEqual(len(doc["records"]), 1)
        row = doc["records"][0]
        self.assertEqual((row["identifier"], row["chapterNumber"]), ("AB 604", 96))
        self.assertEqual(row["approvedByGovernor"], "2025-08-21")
        self.assertTrue(row["source"].startswith("https://elections.cdn.sos.ca.gov/"))
        self.assertTrue(row["sourceIndex"].startswith("https://aelc.assembly.ca.gov/"))
        self.assertTrue(row["legislativeDispositionVerified"])
        self.assertFalse(row["currentLegalValidityAdjudicated"])
        self.assertIn("not_independently_verified", row["voteTalliesStatus"])
        self.assertEqual({x["identifier"] for x in doc["relatedLegislationLeads"]}, {"ACA 8", "SB 280"})
        for r in doc["records"] + doc["relatedLegislationLeads"]:
            self.assertTrue(r["source"].startswith("https://"))
            self.assertFalse({"contributor_name", "contributor_address", "email", "phone"} & set(r))
        self.assertIn("not_secondary_keyword_candidate", doc["publicationStatus"])
        feed = read("data/app-feed.json")
        self.assertEqual(feed["legislation"]["officialCaliforniaRedistrictingSpotcheck"]["records"], doc["records"])
        self.assertEqual(feed["coverage"]["officialCaliforniaRedistrictingSpotcheckRows"], 1)
        self.assertEqual(feed["legislation"]["officialCaliforniaRedistrictingSpotcheck"]["keywordIndexCandidateRows"], 0)

if __name__ == "__main__":
    unittest.main()
