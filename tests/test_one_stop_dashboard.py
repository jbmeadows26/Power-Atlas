"""Regression checks for the Power Atlas consolidated civic dashboard.

These structural tests complement (and do not replace) a browser interaction audit.
The dashboard must never invent local prices, merge incompatible denominators,
or imply a constituent message has been sent.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "platform" / "unified"


class OneStopDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (SITE / "dashboard.html").read_text(encoding="utf-8")
        cls.js = (SITE / "dashboard.js").read_text(encoding="utf-8")
        cls.css = (SITE / "dashboard.css").read_text(encoding="utf-8")
        cls.action = (SITE / "take-action.js").read_text(encoding="utf-8")
        cls.index = (SITE / "index.html").read_text(encoding="utf-8")
        cls.spending = json.loads((SITE / "household-market-bridge.json").read_text(encoding="utf-8"))
        cls.market = json.loads((SITE / "market-power.json").read_text(encoding="utf-8"))
        cls.cases = json.loads((SITE / "investigations-data.json").read_text(encoding="utf-8"))
        cls.refs = json.loads((SITE / "data" / "source-reference-index-v1.json").read_text(encoding="utf-8"))

    def test_entrypoints_return_to_the_dashboard(self):
        self.assertIn('location.replace("dashboard.html"', self.index)
        self.assertIn('href="dashboard.html"', self.index)
        self.assertIn('brand.href="dashboard.html"', (SITE / "atlas-visual-system.js").read_text(encoding="utf-8"))
        self.assertIn('dashboard.html?edit-zip=1', (SITE / "pa-zip-persistence.js").read_text(encoding="utf-8"))

    def test_navigation_and_dashboard_targets_exist(self):
        for section in ("overview", "costs", "investigations", "topics", "sources", "action"):
            self.assertIn('id="' + section + '"', self.html)
        for script in ("dashboard.js", "pa-zip-persistence.js", "bug-report.js"):
            self.assertIn('src="' + script, self.html)
            self.assertTrue((SITE / script).is_file())
        for css in ("dashboard.css",):
            self.assertIn('href="' + css, self.html)
            self.assertTrue((SITE / css).is_file())
        for route in ("my-life.html", "market-power.html", "investigations.html",
                      "research-archive.html", "take-action.html", "source-audit.html"):
            self.assertIn(route, self.html)
            self.assertTrue((SITE / route).is_file())

    def test_data_sources_are_declared_and_not_fabricated(self):
        self.assertEqual(self.spending["schema"], "power-atlas.market-power.household-bridge.v1")
        self.assertEqual(self.spending["baseline"]["period"], "calendar year 2025")
        self.assertEqual(self.market["schema"], "power-atlas.market-power.v1")
        self.assertEqual(self.cases["schema"], "power-atlas.public-integrity-case-index.v1")
        self.assertEqual(self.cases["totals"]["cases"], len(self.cases["cases"]))
        self.assertEqual(self.refs["schema"], "power-atlas.source-reference-index.v1")
        self.assertEqual(self.refs["activeMode"], "reference")
        self.assertIn('loadJSON("household-market-bridge.json"', self.js)
        self.assertIn('loadJSON("market-power.json"', self.js)
        self.assertIn('loadJSON("investigations-data.json"', self.js)
        self.assertIn('loadJSON("data/source-reference-index-v1.json"', self.js)
        self.assertNotIn("fake", self.js.lower())
        self.assertNotIn("placeholderdata", self.js.lower())

    def test_evidence_distinctions_and_chart_denominators(self):
        self.assertIn("not a ZIP-level rent quote", self.html)
        self.assertIn("A charge is not proof of guilt", self.js)
        self.assertIn("Each percentage has a different denominator", self.js)
        self.assertIn("Housing includes utilities", self.js)
        self.assertIn("not presented as facts", self.html)
        self.assertIn("references", self.html.lower())
        self.assertTrue(self.refs["integrityPolicy"]["noImplicitGapClosure"])
        self.assertTrue(self.spending["interpretationRules"])

    def test_zip_persistence_and_contact_are_opt_in(self):
        self.assertIn('power-atlas:visitor-zip:v1', self.js)
        self.assertIn('manager?.save', self.js)
        self.assertIn('new URLSearchParams(location.search).get("edit-zip")', self.js)
        self.assertNotIn("navigator.geolocation", self.js)
        self.assertNotIn("sendBeacon(", self.js)
        self.assertNotRegex(self.js, r'fetch\([^\n]*method\s*:\s*["\\\']POST')
        self.assertIn('id="actionIssue"', self.html)
        self.assertIn('id="actionButton"', self.html)
        self.assertIn('const inboundIssue=params.get("issue")', self.action)
        self.assertIn("Object.prototype.hasOwnProperty.call(issueData,inboundIssue)", self.action)
        self.assertIn("does not send a message", self.html.lower())

    def test_mobile_and_accessibility_basics(self):
        for token in ("mobile-dock", "focus-visible", "prefers-reduced-motion:reduce",
                      "max-width:530px", "max-width:760px"):
            self.assertIn(token, self.css)
        for token in ('href="#main"', 'id="main"', 'role="status"', 'aria-live="polite"',
                      'aria-pressed="true"', 'autocomplete="postal-code"'):
            self.assertIn(token, self.html)
        self.assertIn('id="toggleTopics"', self.html)
        self.assertIn('id="toggleCases"', self.html)


if __name__ == "__main__":
    unittest.main()
