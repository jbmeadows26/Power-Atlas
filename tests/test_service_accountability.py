"""Evidence and frontend integrity checks for corporate service accountability."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "service-accountability" / "service-access-v1.json"
PAGE = ROOT / "platform" / "unified" / "service-accountability.html"
SCRIPT = ROOT / "platform" / "unified" / "service-accountability.js"
LIFE = ROOT / "platform" / "unified" / "my-life.html"


class ServiceAccountabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.life = LIFE.read_text(encoding="utf-8")

    def test_data_schema_and_asof(self):
        self.assertEqual(self.data["schema"], "power-atlas.service-accountability.v1")
        self.assertEqual(self.data["asOf"], "2026-11-09")
        self.assertEqual(self.data["case"]["name"], "Virgin Atlantic")

    def test_survey_has_conditional_denominator(self):
        s = self.data["sample"]
        self.assertEqual(s["sampleSize"], 275)
        self.assertEqual(s["organizationsWithAIAttributedAgentCutsPercent"], 21)
        self.assertEqual(s["meanWorkforceReductionAmongCuttersPercent"], 16.7)
        self.assertEqual(s["rehiredAfterPriorReductionsPercent"], 7)
        self.assertIn("not across all surveyed", s["footnote"])
        self.assertTrue(s["source"].startswith("https://www.gartner.com/"))

    def test_bls_projection_not_actual_layoffs(self):
        b = self.data["labor"]
        self.assertEqual((b["baseEmployment"], b["projectedEmployment"]), (2666000, 2524100))
        self.assertEqual(b["projectedChangePercent"], -5)
        self.assertEqual(b["projectedYear"], 2035)
        self.assertIn("projections, not layoffs", b["footnote"])

    def test_virgin_annual_disclosures_and_guardrails(self):
        c = self.data["case"]
        d = c["companyDisclosure"]
        self.assertEqual((d["totalHeadcount2024"], d["totalHeadcount2025"]), (8760, 9313))
        self.assertEqual((d["reservationsSalesRetailFte2024"], d["reservationsSalesRetailFte2025"]), (1404, 1496))
        self.assertEqual((d["directorsRemunerationGbpM2024"], d["directorsRemunerationGbpM2025"]), (4.7, 13.0))
        self.assertEqual((d["statutoryLossGbpM2024"], d["statutoryLossGbpM2025"]), (94.9, 205.3))
        self.assertIn("not a disclosed telephone-agent count", d["limitations"])
        self.assertIn("does not prove", d["directorContext"])
        self.assertEqual(c["published"]["phone"], "+1 800 862 8621")
        self.assertIn("not independently", c["reported"]["evidenceLevel"])
        self.assertGreaterEqual(len(c["notEstablished"]), 5)
        self.assertIn("US airport", c["legal"]["summary"])
        self.assertTrue(d["source"].endswith(".pdf"))

    def test_credible_sources_and_specific_statuses(self):
        for obj in (self.data["sample"], self.data["labor"]):
            self.assertTrue(obj["source"].startswith("https://"))
        for item in self.data["pathways"]:
            self.assertTrue(item["url"].startswith("https://"))
        for audit in self.data["case"]["audit"]:
            self.assertIn("status", audit)
            self.assertNotEqual(audit["status"], "verified")
        self.assertIn("No company accountability score", self.data["methodology"]["noCompositeScore"])

    def test_dashboard_references_every_dynamic_node(self):
        nodes = set(re.findall(r'\$\("([A-Za-z][A-Za-z0-9]*)"\)', self.script))
        ids = set(re.findall(r'\bid="([^"]+)"', self.page))
        self.assertTrue(nodes.issubset(ids), nodes - ids)
        self.assertIn('src="service-accountability.js?v=', self.page)
        self.assertIn('src="bug-report.js"', self.page)
        self.assertIn('href="global-navigation.css"', self.page)
        self.assertIn("data-pa-nav=\"issues\"", self.page)
        self.assertIn("aria-live", self.page)

    def test_entry_point_keeps_benchmark_before_promo(self):
        self.assertIn('id="humanServiceCard"', self.life)
        self.assertIn('href="service-accountability.html"', self.life)
        self.assertLess(self.life.index('id="benchmarkStory"'), self.life.index('id="humanServiceCard"'))
        self.assertLess(self.life.index('id="humanServiceCard"'), self.life.index('id="compareYourCosts"'))

    def test_frontend_fails_closed_without_source_feed(self):
        self.assertIn("unexpected evidence schema", self.script)
        self.assertIn("live IVR and individual service outcomes remain unverified", self.script)
        self.assertIn("no missing company measurements have been invented", self.script)
        self.assertNotIn("localStorage", self.script)
        self.assertNotIn("sendBeacon", self.script)

    def test_javascript_syntax_if_node_available(self):
        if shutil.which("node") is None:
            self.skipTest("Node.js not available")
        result = subprocess.run(["node", "--check", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)



    def test_editorial_visual_integration_and_working_charts(self):
        """Consumer Watch entry, data-bound charts, source limits and accessible controls."""
        site = (ROOT / "site" / "service-accountability.html").read_text(encoding="utf-8")
        site_js = (ROOT / "site" / "service-accountability.js").read_text(encoding="utf-8")
        consumer = (ROOT / "site" / "consumer-practices.html").read_text(encoding="utf-8")
        for markup in (site, self.page):
            self.assertIn('id="saSurveyChart"', markup)
            self.assertIn('id="saWorkforceChart"', markup)
            self.assertIn('class="sa-editorial"', markup)
            self.assertIn('id="saQuestions"', markup)
            self.assertIn('not independently', markup)
        for script in (site_js, self.script):
            self.assertIn("staffPair(", script)
            self.assertIn("surveyBar(", script)
            self.assertIn('g.totalHeadcount2024,g.totalHeadcount2025', script)
            self.assertIn('s.organizationsWithAIAttributedAgentCutsPercent', script)
            self.assertIn('independently observed call', script)
        self.assertIn('href="service-accountability.html"', consumer)
        self.assertIn('cw-service-panel', consumer)

if __name__ == "__main__":
    unittest.main()
