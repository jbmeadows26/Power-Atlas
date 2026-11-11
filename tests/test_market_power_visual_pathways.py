"""Regression gates for the Market Power story's Dark Money template parity."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTENDS = (ROOT / "site", ROOT / "platform" / "unified")
CANONICAL = json.loads((ROOT / "data" / "market-power" / "evidence-v1.json").read_text(encoding="utf-8"))
CASE_IDS = {case["id"] for case in CANONICAL["cases"]}


class MarketPowerVisualPathwaysTests(unittest.TestCase):
    def test_synchronized_market_component_assets(self):
        for name in ("market-power-pathways.js", "market-power-pathways.css"):
            self.assertEqual(
                (FRONTENDS[0] / name).read_bytes(),
                (FRONTENDS[1] / name).read_bytes(), name
            )

    def test_six_evidence_backed_stories(self):
        js = (FRONTENDS[0] / "market-power-pathways.js").read_text(encoding="utf-8")
        ids = re.findall(r'\{id:"([^"]+)",name:', js)
        self.assertEqual(ids, ["pbms", "beef", "hospitals", "jobs", "search", "tickets"])
        self.assertTrue(set(ids).issubset(CASE_IDS))
        self.assertIn('fetch("./market-power.json"', js)
        for token in ("c.metricLabel", "c.period", "c.kind", "c.scope", "c.source",
                      "c.status", "aria-pressed", "PowerAtlasMarketPower={mount}",
                      "Concept map:", "NOT ESTABLISHED"):
            self.assertIn(token, js)
        self.assertIn("market-power.html?case=", js)
        self.assertIn("aria-atomic", js)
        self.assertIn("Evidence status:", js)

    def test_template_structure_and_progressive_disclosure(self):
        template = (FRONTENDS[1] / "political-money-story.css").read_text(encoding="utf-8")
        new = (FRONTENDS[1] / "market-power-pathways.css").read_text(encoding="utf-8")
        for token in ("pathways", "chapter", "route", "route-arrow", "evidence",
                      "fact", "gap", "bridge", "method", "actions", "state"):
            self.assertIn(".pmx-" + token, template)
            self.assertIn(".mpx-" + token, new)
        for size in ("@media(max-width:850px)", "@media(max-width:480px)"):
            self.assertIn(size, template)
            self.assertIn(size, new)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", new)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", new)
        self.assertIn(".vs6-topic.vs6-topic--mpx", new)

    def test_component_mounts_in_v6_topic_not_standalone_dashboard(self):
        for root in FRONTENDS:
            html = (root / "market-power.html").read_text(encoding="utf-8")
            v6 = (root / "visual-story-v6.js").read_text(encoding="utf-8")
            self.assertIn('id="pa-global-header"', html)
            self.assertIn('href="global-navigation.css"', html)
            self.assertIn('href="market-power-pathways.css"', html)
            self.assertIn('src="market-power-pathways.js"', html)
            self.assertNotIn('<section class="mpx-section"', html)
            self.assertIn("PowerAtlasMarketPower.mount(section)", v6)
            self.assertIn('button.pa5-chapter-card[aria-controls="explore"]', v6)
            self.assertIn('id="market-power-pathways"', (root / "market-power-pathways.js").read_text(encoding="utf-8"))
            self.assertIn('id="household-bridge"', html)
            self.assertIn('id="explore"', html)
            self.assertIn('id="caseMenu"', html)
            self.assertIn("supportingSources", html)
            self.assertIn('a.href="market-power.html"', v6)

    def test_full_research_and_evidence_distinctions_remain(self):
        self.assertGreaterEqual(len(CANONICAL["cases"]), 12)
        kinds = {case["kind"] for case in CANONICAL["cases"]}
        self.assertTrue({"measured", "allegation", "finding", "context"}.issubset(kinds))
        for root in FRONTENDS:
            self.assertEqual(
                CANONICAL,
                json.loads((root / "market-power.json").read_text(encoding="utf-8"))
            )
            js = (root / "market-power-pathways.js").read_text(encoding="utf-8")
            self.assertIn("Source record", js)
            self.assertIn("allegation is not a finding", js)
            self.assertIn("source evidence", js.lower())


if __name__ == "__main__":
    unittest.main()
