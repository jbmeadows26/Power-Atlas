"""Original reference-first gap closure safeguards and bounded-source claims."""
import unittest
from urllib.parse import urlsplit

from scripts.build_reference_gap_progress import (
    ORIGINAL_GAPS, ORIGINAL_GATES, BACKLOG, CASES, OUT, build, load
)


class ReferenceFirstGapEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = load(OUT)
        cls.cases = load(CASES)["cases"]
        cls.case_map = {case["id"]: case for case in cls.cases}

    def test_ledger_in_sync_with_canonical_research(self):
        self.assertEqual(self.ledger, build())
        scope = self.ledger["scope"]
        self.assertEqual(scope["localGapCount"], 55)
        self.assertEqual(scope["nationalBlockingGateCount"], 9)
        self.assertEqual(scope["openTotal"], 64)
        self.assertEqual(scope["fullGapClosures"], 0)
        self.assertEqual(scope["boundedEvidenceCasesReviewed"], 3)
        self.assertEqual(scope["distinctGapsWithNewBoundedEvidence"], 4)
        self.assertTrue(all(not gap["originalGateClosed"] for gap in self.ledger["gaps"]))
        self.assertEqual(
            {g["gapId"] for g in self.ledger["gaps"] if g["category"] == "national"},
            set(load(ORIGINAL_GATES)["blockingGates"]),
        )
        self.assertEqual(
            {g["gapId"] for g in self.ledger["gaps"] if g["category"] == "local"},
            {g["id"] for g in load(ORIGINAL_GAPS)["gaps"]},
        )

    def test_nj_cross_report_agreement_is_bounded(self):
        case = self.case_map["nj-2024-bergen-presidential-official-cross-report"]
        self.assertFalse(case["originalGapClosureAllowed"])
        self.assertEqual(case["scope"]["county"], "Bergen")
        self.assertEqual(case["scope"]["electionDate"], "2024-11-05")
        self.assertEqual(len(case["checks"]), 2)
        for row in case["checks"]:
            self.assertEqual(row["countyReportVotes"], row["stateCandidateReportBergenVotes"])
            self.assertTrue(row["agrees"])
            self.assertGreater(row["countyReportVotes"], 0)
        self.assertEqual(
            {row["countyReportVotes"] for row in case["checks"]},
            {232660, 217096},
        )
        self.assertFalse(case["scope"]["allCandidatesReviewed"])
        self.assertFalse(case["scope"]["allNJCountiesReviewed"])

    def test_2026_nj_transit_fare_is_not_journey_specific(self):
        case = self.case_map["njt-northern-interstate-2026-two-zone-tariff"]
        self.assertFalse(case["originalGapClosureAllowed"])
        self.assertEqual(case["scope"]["pricingEffectiveDate"], "2026-07-01")
        self.assertIsNone(case["scope"]["originStop"])
        self.assertIsNone(case["scope"]["destinationStop"])
        self.assertEqual(case["checks"][0]["value"], 4.20)
        self.assertEqual(case["checks"][0]["currency"], "USD")
        self.assertEqual(case["checks"][0]["sourceTableRow"], 2)

    def test_sitewide_scan_is_scoped(self):
        case = self.case_map["sitewide-static-route-audit-2026-11-12"]
        counts = {r["metric"]: r["count"] for r in case["checks"]}
        self.assertEqual(counts["staticReferencesInspected"], 1150)
        self.assertEqual(counts["unresolvedStaticLinkIssues"], 0)
        self.assertFalse(case["originalGapClosureAllowed"])
        self.assertIn("third-party", " ".join(case["limits"]))

    def test_record_references_have_official_https_without_stored_file_hashes(self):
        for case in self.cases:
            for source in case["sourceDocuments"]:
                url = urlsplit(source["url"])
                self.assertEqual(url.scheme, "https")
                self.assertIsNone(url.username)
                self.assertIsNone(url.password)
                self.assertIsNone(source["sha256"])
            self.assertTrue(case["limits"])
            self.assertFalse(case["originalGapClosureAllowed"])

    def test_evidence_ui_is_read_only_and_explicit_about_open_gaps(self):
        from scripts.build_reference_gap_progress import ROOT
        page = (ROOT / "platform/unified/source-audit.html").read_text(encoding="utf-8")
        js = (ROOT / "platform/unified/verified-evidence-cases.js").read_text(encoding="utf-8")
        self.assertIn('id="verifiedEvidenceCards"', page)
        self.assertIn('<script src="verified-evidence-cases.js" defer></script>', page)
        self.assertIn("reference-gap-progress-v1.json", js)
        self.assertIn("reference-first-evidence-cases-v1.json", js)
        self.assertIn("originalGapClosureAllowed !== false", js)
        self.assertIn("does not close the full research gap", js)
        self.assertNotIn("archiveCandidateURL", js)

    def test_all_verified_case_ids_link_to_real_open_gaps(self):
        ids = {g["gapId"] for g in self.ledger["gaps"]}
        for case in self.cases:
            self.assertTrue(
                set(case["relatedLocalGapIds"] + case["relatedNationalGateIds"]).issubset(ids)
            )
        for g in self.ledger["gaps"]:
            for case_id in g["boundedCaseIds"]:
                self.assertIn(case_id, self.case_map)
                self.assertIn(g["gapId"],
                              self.case_map[case_id]["relatedLocalGapIds"] +
                              self.case_map[case_id]["relatedNationalGateIds"])


if __name__ == "__main__":
    unittest.main()
