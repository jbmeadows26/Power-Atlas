"""Power Atlas product-acceptance smoke checks; no API keys or paid services.

These are static contract checks, NOT substitutes for live-browser/UX QA.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "platform" / "unified"
DATA = ROOT / "data"


class ProductAcceptanceTests(unittest.TestCase):
    def test_public_root_starts_at_zip_first_journey(self):
        html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("data-pa-root-entry", html)
        self.assertIn('window.location.pathname === "/"', html)
        self.assertIn('window.location.replace("my-life.html"', html)
        self.assertTrue((SITE / "my-life.html").exists())
        # Explicit /index.html remains available for the full research archive.
        self.assertIn("Research Intelligence", html)

    def test_canonical_design_is_loaded_for_critical_modules(self):
        pages = (
            "index.html", "my-life.html", "take-action.html",
            "consumer-practices.html", "dark-money.html",
            "market-power.html", "business-influence.html",
            "corporate-ownership.html", "wealth-advantage.html",
            "class-actions.html", "source-audit.html",
        )
        for name in pages:
            with self.subTest(page=name):
                text = (SITE / name).read_text(encoding="utf-8")
                self.assertIn("atlas-visual-system.js", text)
                self.assertIn("global-navigation.css", text)
                self.assertIn('id="pa-global-header"', text)
        layer = (SITE / "atlas-visual-system.js").read_text(encoding="utf-8")
        v5 = (SITE / "visual-first-v5.js").read_text(encoding="utf-8")
        v6 = (SITE / "visual-story-v6.css").read_text(encoding="utf-8")
        self.assertIn("visual-first-v5.js", layer)
        self.assertIn("visual-story-v6.js", v5)
        self.assertIn("QA 2026-11-11", v6)
        self.assertIn("vs6-topic-mode .pa3-story", v6)

    def test_requested_research_modules_are_accessible(self):
        modules = [
            "business-influence.html", "dark-money.html",
            "corporate-ownership.html", "market-power.html",
            "consumer-practices.html", "class-actions.html",
            "service-accountability.html", "wealth-advantage.html",
            "economic-fragility-review.html", "cost-gap.html",
            "public-trading.html", "financial-flows.html",
            "compare.html", "take-action.html", "source-audit.html",
        ]
        discovery = (SITE / "qa-evidence-hub.js").read_text(encoding="utf-8")
        place = (SITE / "my-life.html").read_text(encoding="utf-8")
        self.assertIn('src="qa-evidence-hub.js"', place)
        for filename in modules:
            with self.subTest(module=filename):
                self.assertTrue((SITE / filename).exists(), filename)
                self.assertIn(filename, discovery, filename)
        self.assertIn("pa-coverage-discovery", discovery)
        self.assertIn("sitewide-audit-v1.json", discovery)

    def test_original_evidence_gaps_are_not_misreported_as_complete(self):
        catalog = json.loads((DATA / "health" / "sitewide-missing-sources-v1.json").read_text(encoding="utf-8"))
        audit = json.loads((DATA / "health" / "sitewide-audit-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema"], "power-atlas.sitewide-missing-source-catalog.v1")
        self.assertEqual(audit["schema"], "power-atlas.sitewide-static-source-audit.v1")
        self.assertEqual(len(catalog["gaps"]), audit["summary"]["unresolvedOriginalSourceGaps"])
        self.assertTrue(all(item["status"] for item in catalog["gaps"]))
        self.assertEqual(len([g for g in catalog["gaps"] if g["issue"] != "platform-wide"]), 36)
        self.assertEqual(len([g for g in catalog["gaps"] if g["issue"] == "platform-wide"]), 19)
        self.assertGreater(audit["summary"]["unresolvedOriginalSourceGaps"], 0)

    def test_public_dataset_does_not_disappear_between_redesigns(self):
        items = (
            ("consumer-practices/cases-v1.json", "cases", 18),
            ("consumer-class-actions/cases-v1.json", "cases", 6),
            ("market-power/evidence-v1.json", "cases", 12),
            ("place-impact/life-issues-v1.json", "issues", 9),
            ("consumer-practices/shrinkflation-v1.json", "reportedPackageChanges", 3),
        )
        for filename, field, minimum in items:
            with self.subTest(dataset=filename):
                data = json.loads((DATA / filename).read_text(encoding="utf-8"))
                self.assertGreaterEqual(len(data[field]), minimum)

    def test_core_accessibility_and_civic_actions(self):
        place = (SITE / "my-life.html").read_text(encoding="utf-8")
        action = (SITE / "take-action.html").read_text(encoding="utf-8")
        self.assertIn('id="what"', place)
        self.assertIn('id="where"', place)
        self.assertIn('id="why"', place)
        self.assertIn('id="how"', place)
        self.assertIn('data-chamber="house"', action)
        self.assertIn('data-chamber="senate"', action)
        self.assertIn("congress.gov", action)
        self.assertRegex(action, r'aria-pressed="false"')
        for filename in ("my-life.html", "take-action.html", "market-power.html"):
            self.assertIn("bug-report.js", (SITE / filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
