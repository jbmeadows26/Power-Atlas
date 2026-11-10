"""Power Atlas v6 infographic-first review gate.
Guards against returning to text-heavy cards, hidden chart labels, lost evidence links,
and broken research controls. Does not change any dataset.
"""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SITES=(ROOT/"platform/unified",ROOT/"site")

class VisualStoriesV6Tests(unittest.TestCase):
    def test_shared_assets_match_across_projects(self):
        for file in ("visual-story-v6.js","visual-story-v6.css","visual-first-v5.js"):
            self.assertEqual((SITES[0]/file).read_bytes(),(SITES[1]/file).read_bytes())

    def test_graphics_and_progressive_detail_present(self):
        for site in SITES:
            js=(site/"visual-story-v6.js").read_text()
            css=(site/"visual-story-v6.css").read_text()
            loader=(site/"visual-first-v5.js").read_text()
            for marker in ("vs6-metrics","vs6-owned","vs6-phone-viz","vs6-money-viz","vs6-market-viz",
                           "vs6-case-viz","vs6-wave","vs6-story","vs6-topic","vs6-research-button",
                           "vs6-expand","vs6-metric-label","Original data"):
                with self.subTest(site=site.name,marker=marker):
                    self.assertIn(marker,js)
            for marker in ('button.vs6-metric[aria-pressed="true"]',
                           ".vs6-metric-label",".vs6-metric-value",".vs6-gallery",
                           "vs6-home-mode",".vs6-topic"):
                self.assertIn(marker,css)
            self.assertIn("visual-story-v6.css",loader)
            self.assertIn("visual-story-v6.js",loader)

    def test_cpi_values_are_not_replaced_by_illustrative_data(self):
        data=json.loads((ROOT/"data/place-impact/connected-metrics-v1.json").read_text())
        js=(SITES[0]/"visual-story-v6.js").read_text()
        for key in ("transport","housing","groceries","health"):
            self.assertEqual(data["national"][key]["period"],"2026-09")
        self.assertIn("readMetrics(original)",js)
        self.assertIn('old.querySelectorAll(".pa4-graphic .pa4-bar")',js)
        self.assertIn("National index changes—not your personal bill",js)
        self.assertIn("local rent effects",js)

    def test_original_community_zip_and_evidence_routes_preserved(self):
        page=(SITES[0]/"my-life.html").read_text()
        self.assertIn('id="zipForm"',page)
        self.assertIn('id="zipInput"',page)
        self.assertIn('autocomplete="postal-code"',page)
        for name in ("dark-money.html","corporate-ownership.html","consumer-practices.html",
                     "class-actions.html","market-power.html"):
            self.assertTrue((SITES[0]/name).is_file())
        self.assertIn("vs6-topic-expanded",(SITES[0]/"visual-story-v6.js").read_text())

    def test_corporate_ownership_has_valid_main_and_visual_route(self):
        page=(SITES[0]/"corporate-ownership.html").read_text()
        self.assertNotIn("<main<main",page)
        self.assertIn('<main class="wrap">',page)
        script=(SITES[0]/"visual-story-v6.js").read_text()
        self.assertIn("corporate-ownership.html",script)
        self.assertIn("Explore the evidence",script)
        style=(SITES[0]/"visual-story-v6.css").read_text()
        self.assertIn("body.vs6-topic-mode > .hero",style)

    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_javascript_syntax(self):
        for site in SITES:
            for name in ("visual-story-v6.js","visual-first-v5.js"):
                with self.subTest(site=site.name,name=name):
                    p=subprocess.run(["node","--check",str(site/name)],capture_output=True,text=True,timeout=20)
                    self.assertEqual(0,p.returncode,p.stderr)

if __name__=="__main__":
    unittest.main()
