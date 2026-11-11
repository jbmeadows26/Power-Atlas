"""Regression tests for every Power Atlas page, data schema and source-gap register."""
from pathlib import Path
import json
import unittest
from scripts.audit_power_atlas_site import audit, resolve_link, PageParser, ROOT

CATALOG = ROOT / "data/health/sitewide-missing-sources-v1.json"
EXPECTED = {"housing", "groceries", "energy", "health", "work", "schools",
            "transport", "public-services", "representation"}

class SitewideAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit()
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_data_schema_and_all_research_mappings(self):
        r = self.report
        self.assertGreaterEqual(r["summary"]["htmlPagesAudited"], 17)
        self.assertGreaterEqual(r["summary"]["jsonDataFilesChecked"], 200)
        self.assertEqual(r["invalidDataFiles"], [])
        self.assertEqual(r["structuralErrors"], [])
        self.assertEqual(r["summary"]["lifeCategories"], 9)
        self.assertEqual(r["summary"]["deepResearchTracksMapped"], 25)
        self.assertGreaterEqual(r["summary"]["corporateEntitiesIndexed"], 80)
        self.assertGreaterEqual(r["summary"]["corporateRelationsSourceAttributed"], 60)
        self.assertEqual(r["summary"]["transparencyCostCaseStudies"], 7)

    def test_all_nine_issues_have_original_sources_for_price_owner_decisions_outcomes(self):
        gaps = self.catalog["gaps"]
        for issue in sorted(EXPECTED):
            records = [g for g in gaps if g["issue"] == issue]
            self.assertEqual({g["kind"] for g in records},
                             {"price", "ownership", "decisions", "outcomes"})
            for g in records:
                self.assertTrue(g["sourceIds"],g["id"])
                self.assertTrue(g["requiredJoin"],g["id"])
                self.assertNotEqual(g["status"],"resolved_by_source_verified_data",
                                    "Do not mark the gap complete without real source ingestion")
        s = self.report["sourceIntegrity"]
        self.assertGreaterEqual(s["sourceCount"], 50)
        self.assertEqual(s["brokenSourceReferences"], [])
        self.assertEqual(s["missingSourceURLs"], [])
        self.assertTrue(s["nineIssuesCovered"])

    def test_sitewide_link_integrity_and_bug_report_button(self):
        # Every static path on every page must exist after publishing.
        self.assertEqual(self.report["brokenStaticReferences"], [])
        self.assertEqual(self.report["unresolvedLiteralDataPointers"], [])
        self.assertEqual(self.report["missingBugReportScripts"], [])

    def test_bounded_research_unfinished_status_is_honest(self):
        r = self.report
        self.assertEqual(r["overall"], "research_partially_connected_not_nationwide_complete")
        self.assertGreater(r["summary"]["unresolvedOriginalSourceGaps"], 0)
        self.assertGreater(r["summary"]["blockingExistingResearchGates"], 0)
        self.assertEqual(r["corporateGraph"]["brokenRelations"], [])
        self.assertEqual(r["summary"]["queuedIngestionTasks"], 0)
        self.assertEqual(r["summary"]["stalePageTwoQueueEntries"], 0)
        self.assertEqual(r["summary"]["boundedKeywordPageTasksReconciled"], 10)

    def test_verified_hud_benchmark_remains_partial_not_local_market_rent(self):
        item = next(g for g in self.catalog["gaps"] if g["id"] == "housing__price")
        self.assertEqual(item["status"], "partial_program_benchmark_verified_actual_prices_unresolved")
        evidence = item["verifiedPartialIntegration"]
        self.assertEqual(evidence["sourceObjectCount"], 51895)
        self.assertEqual(evidence["sourceZctaCount"], 38601)
        self.assertIn("Actual year-matched local rents", evidence["missingToResolve"])
        shard = json.loads((ROOT / "data/housing/hud-safmr-fy2026-0.json").read_text())
        self.assertEqual(shard["sourceObjectCount"], evidence["sourceObjectCount"])
        self.assertEqual(shard["uniqueZctas"], evidence["sourceZctaCount"])
        self.assertEqual(shard["fiscalYear"], 2026)
        local = [r for r in shard["rows"] if r["zip"] == "07010"]
        self.assertTrue(local)
        self.assertTrue(all(r["usdByBedroom"]["1"] > 0 and r["usdByBedroom"]["2"] > 0 for r in local))
        self.assertEqual(self.report["sourceIntegrity"]["unresolvedGapCount"], 55)

    def test_static_url_resolution(self):
        p = ROOT / "platform/unified/my-life.html"
        link = {"platform/unified/my-life.html": {"where", "what", "why", "how"}}
        self.assertIsNone(resolve_link(p, "index.html", link))
        self.assertIsNone(resolve_link(p, "my-life.html#why", link))
        self.assertIsNone(resolve_link(p, "https://www.fec.gov/data/", link))
        self.assertEqual(resolve_link(p, "not-in-site.json", link)["kind"], "missing_static_link")
        self.assertEqual(resolve_link(p, "my-life.html#missing", link)["kind"],
                         "missing_static_target_anchor")

if __name__ == "__main__":
    unittest.main()
