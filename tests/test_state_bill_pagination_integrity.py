"""Guard persistence and scope of bounded state legislative keyword pagination.

All checks are offline; no API keys, network requests or paid resources.
"""
import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class StateBillPaginationIntegrityTests(unittest.TestCase):
    def test_page_checkpoint_matches_persisted_candidates(self):
        bills = read("data/legislation/state-redistricting-bills.json")
        pagination = read("data/legislation/state-redistricting-pagination.json")
        checkpoint = read("data/legislation/state-redistricting-jurisdictions.json")
        rows = bills["records"]
        self.assertEqual(len(rows), len({r["id"] for r in rows}))
        self.assertEqual(pagination["candidateBillRows"], len(rows))
        self.assertEqual(pagination["additionalPagesIndexed"],
                         sum(len(p) for p in pagination["pages"].values()))
        self.assertEqual(pagination["jurisdictionsWithAdditionalPages"],
                         sum(bool(p) for p in pagination["pages"].values()))
        self.assertEqual(checkpoint["jurisdictionsScanned"],
                         len(checkpoint["jurisdictions"]))
        self.assertEqual(checkpoint["jurisdictionsScanned"], 51)
        self.assertEqual(len(checkpoint["jurisdictions"]), 51)
        for state, pages in pagination["pages"].items():
            self.assertIn(state, checkpoint["jurisdictions"])
            for page, metadata in pages.items():
                self.assertGreaterEqual(int(page), 2)
                self.assertGreaterEqual(metadata["rowsReturned"], 0)
                self.assertLessEqual(metadata["rowsReturned"], 20)
                self.assertGreaterEqual(metadata["newUniqueRows"], 0)
                self.assertLessEqual(metadata["newUniqueRows"], metadata["rowsReturned"])
                parsed = urlparse(metadata["source"])
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.hostname, "api.billcommons.org")
                args = parse_qs(parsed.query)
                self.assertEqual(args.get("jurisdiction"), [state])
                self.assertEqual(args.get("page"), [page])
                self.assertEqual(args.get("q"), ["redistricting"])

    def test_feed_matches_source_and_does_not_claim_exhaustive_coverage(self):
        bills = read("data/legislation/state-redistricting-bills.json")
        feed = read("data/app-feed.json")
        coverage = read("data/coverage.json")["coverage"]
        self.assertEqual(feed["legislation"]["stateRedistrictingBillCandidates"],
                         bills["records"])
        self.assertEqual(coverage["stateBillCandidateRows"], len(bills["records"]))
        self.assertEqual(coverage["stateBillFullSweepJurisdictions"], 0)
        self.assertEqual(feed["coverage"]["stateBillCandidateRows"],
                         coverage["stateBillCandidateRows"])
        self.assertIn("not an exhaustive", bills["coverageWarning"].lower())
        self.assertIn("licensing", bills["coverageWarning"].lower())
        for row in bills["records"]:
            self.assertTrue(row["source"].startswith("https://"))
            self.assertEqual(row["reviewStatus"],
                             "third_party_index_official_source_review_required")
            scope = row["retrievalScope"]
            self.assertTrue(
                scope == "top_40_per_query_no_complete_jurisdiction_census"
                or scope.startswith("first_")
                or scope.startswith("redistricting_state_keyword_page_"),
                msg=f"Unexpected retrieval scope for {row['id']}: {scope}"
            )



if __name__ == "__main__":
    unittest.main()
