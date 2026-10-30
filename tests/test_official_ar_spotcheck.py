"""Keep official Arkansas 2021 redistricting evidence distinct from keyword-index coverage."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArkansasOfficialSourceChecks(unittest.TestCase):
    def test_official_2021_acts_expose_keyword_false_negative_without_fabricated_candidates(self):
        doc = json.loads((ROOT / "data/legislation/official-arkansas-redistricting-2021.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((ROOT / "data/legislation/state-redistricting-jurisdictions.json").read_text(encoding="utf-8"))
        indexed = json.loads((ROOT / "data/legislation/state-redistricting-bills.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["jurisdiction"], "AR")
        self.assertEqual(doc["queryDiscrepancy"]["reportedMatches"], 0)
        self.assertEqual(checkpoint["jurisdictions"]["AR"]["totalMatchesReported"], 0)
        self.assertEqual(checkpoint["jurisdictions"]["AR"]["persistedCandidateRows"], 0)
        self.assertFalse(any(row["state"] == "AR" for row in indexed["records"]))
        rows = doc["records"]
        self.assertEqual({r["identifier"]: r["actNumber"] for r in rows}, {"HB 1982": 1114, "SB 743": 1116})
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        for row in rows:
            self.assertTrue(row["source"].startswith("https://"))
            self.assertTrue(row["officialAct"].startswith("https://"))
            self.assertIn("spotcheck", row["reviewStatus"])
            self.assertFalse(row["legalOutcomeVerified"])
            self.assertNotIn("contributor_name", row)
            self.assertNotIn("contributor_address", row)
        self.assertEqual(doc["relation"]["type"], "official_summary_reports_identical_acts")
        feed = json.loads((ROOT / "data/app-feed.json").read_text(encoding="utf-8"))
        self.assertEqual(feed["legislation"]["officialArkansasHistoricalRedistricting"]["records"], rows)
        self.assertEqual(feed["coverage"]["officialArkansasHistoricalSpotcheckRows"], len(rows))
        self.assertEqual(feed["legislation"]["officialArkansasHistoricalRedistricting"]["keywordIndexCandidateRows"], 0)
        self.assertEqual(doc["publicationStatus"], "official_legislative_archive_metadata_spotcheck_not_keyword_index_or_exhaustive_session")


if __name__ == "__main__":
    unittest.main()
