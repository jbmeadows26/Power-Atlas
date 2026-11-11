"""Ensure the Market Power interactive stories remain sourced, navigable and synchronized."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTENDS = [ROOT / "site", ROOT / "platform" / "unified"]
CASES = json.loads((ROOT / "data" / "market-power" / "evidence-v1.json").read_text(encoding="utf-8"))["cases"]
CASE_IDS = {item["id"] for item in CASES}


class MarketPowerVisualPathwaysTests(unittest.TestCase):
    def test_same_source_copies_on_two_frontends(self):
        for name in ("market-power-pathways.js", "market-power-pathways.css",
                     "visual-story-v6.js", "visual-story-v6.css"):
            self.assertEqual(
                (FRONTENDS[0] / name).read_text(encoding="utf-8"),
                (FRONTENDS[1] / name).read_text(encoding="utf-8"), name
            )

    def test_all_new_sector_tabs_have_an_original_evidence_case(self):
        js = (FRONTENDS[0] / "market-power-pathways.js").read_text(encoding="utf-8")
        ids = re.findall(r'\{id:"([^"]+)",short:', js)
        self.assertEqual(ids, ["pbms", "beef", "hospitals", "jobs", "search"])
        self.assertTrue(set(ids) <= CASE_IDS)
        self.assertIn('fetch("market-power.json"', js)
        self.assertIn("c.metricLabel", js)
        self.assertIn("c.scope", js)
        self.assertIn("c.kind", js)
        self.assertIn("c.source", js)
        self.assertIn('aria-pressed', js)

    def test_expanded_story_is_visible_with_working_paths(self):
        for root in FRONTENDS:
            html = (root / "market-power.html").read_text(encoding="utf-8")
            self.assertIn('id="market-power-pathways"', html)
            self.assertIn('id="mpxTabs"', html)
            self.assertIn('id="mpxMeasure"', html)
            self.assertIn('id="mpxDetail"', html)
            self.assertIn('id="mpxExtra"', html)
            self.assertIn('href="#market-power-pathways"', html)
            self.assertIn('src="market-power-pathways.js"', html)
            self.assertIn('href="market-power-pathways.css"', html)
            self.assertLess(html.index('id="market-power-pathways"'), html.index('id="household-bridge"'))
            self.assertLess(html.index('id="household-bridge"'), html.index('id="explore"'))
            self.assertIn("different years and denominators", html)
            self.assertIn("not comparable market rankings", html.lower())

    def test_home_card_shows_sourced_not_fabricated_measures(self):
        for root in FRONTENDS:
            script = (root / "visual-story-v6.js").read_text(encoding="utf-8")
            self.assertIn("85%", script)
            self.assertIn("~80%", script)
            self.assertIn("USDA 2024", script)
            self.assertIn("FTC 2023", script)
            self.assertIn("Separate markets, not price markups", script)
            self.assertIn('a.href="market-power.html#market-power-pathways"', script)
            css = (root / "market-power-pathways.css").read_text(encoding="utf-8")
            self.assertIn("@media(max-width:520px)", css)
            self.assertIn("prefers-reduced-motion", css)


if __name__ == "__main__":
    unittest.main()
