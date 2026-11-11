"""Production acceptance checks for the Power Atlas visual atlas redesign.

Uses repository sources only; never alters production and does not make network calls.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
UNIFIED=ROOT/"platform"/"unified"
RESEARCH=ROOT/"site"
SITES=(UNIFIED,RESEARCH)
PAGES_UNIFIED=("index.html","my-life.html","corporate-ownership.html",
               "consumer-practices.html","dark-money.html","source-audit.html",
               "reform-lab.html","class-actions.html","election-money.html",
               "money-sources.html","donor-intelligence.html","compare.html",
               "service-accountability.html","telecom-promotions.html")
PAGES_RESEARCH=("index.html","consumer-practices.html","service-accountability.html",
                "telecom-promotions.html","economic-fragility.html")
FORBIDDEN=("power-atlas-visual-review.vercel.app",
           "power-atlas-research-git-review",
           "__PA4_UNIFIED_PREVIEW__",
           "DESIGN REVIEW · NOT PRODUCTION",
           "pa4-review-ribbon",
           "noindex,nofollow")

class ProductionVisualAtlasTests(unittest.TestCase):
    def test_required_page_coverage_and_assets(self):
        for folder,pages in ((UNIFIED,PAGES_UNIFIED),(RESEARCH,PAGES_RESEARCH)):
            for name in pages:
                with self.subTest(page=str(folder.name+"/"+name)):
                    page=folder/name
                    self.assertTrue(page.exists(), f"Missing {page}")
                    html=page.read_text(encoding="utf-8")
                    self.assertIn('atlas-visual-system.css',html)
                    self.assertIn('atlas-visual-system.js',html)
                    self.assertIn("</html>",html.lower())

    def test_shared_design_assets_identical(self):
        for name in ("atlas-visual-system.js","atlas-visual-system.css"):
            with self.subTest(name=name):
                self.assertEqual((UNIFIED/name).read_bytes(),(RESEARCH/name).read_bytes())

    def test_no_preview_artifacts_in_production_design(self):
        check=[
            UNIFIED/"atlas-visual-system.js",
            RESEARCH/"atlas-visual-system.js",
            UNIFIED/"atlas-visual-system.css",
            RESEARCH/"atlas-visual-system.css",
            UNIFIED/"class-actions.html",
            UNIFIED/"class-actions-visual.css",
            UNIFIED/"class-actions-visual.js",
            UNIFIED/"consumer-practices.html",
            RESEARCH/"consumer-practices.html",
        ]
        for path in check:
            with self.subTest(path=str(path.relative_to(ROOT))):
                content=path.read_text(encoding="utf-8")
                for bad in FORBIDDEN:
                    self.assertNotIn(bad,content)
        self.assertFalse((UNIFIED/"redesign-preview.html").exists())
        self.assertFalse((RESEARCH/"redesign-preview.html").exists())

    def test_all_ten_visual_entry_points_route_to_real_pages(self):
        script=(UNIFIED/"atlas-visual-system.js").read_text(encoding="utf-8")
        pattern=r'\["(?:0[1-9]|10) · [^"]+","[^"]+","[^"]+","([^"]+\.html)","#[a-fA-F0-9]+"\]'
        matches=re.findall(pattern,script)
        self.assertEqual(len(matches),10,f"Expected ten visual topic routes: {matches!r}")
        for name in matches:
            self.assertTrue((UNIFIED/name).exists() or (RESEARCH/name).exists(),f"Broken visual entry point: {name}")
        self.assertIn('class-actions.html',matches)
        self.assertIn('https://power-atlas-unified.vercel.app/',script)
        self.assertIn('https://power-atlas-research.vercel.app/',script)

    def test_charts_are_clickable_with_explanation_and_source(self):
        for folder in SITES:
            script=(folder/"atlas-visual-system.js").read_text(encoding="utf-8")
            with self.subTest(folder=folder.name):
                self.assertIn('make("button","pa3-chart-row")',script)
                self.assertIn('outer.addEventListener("click"',script)
                self.assertIn('setAttribute("aria-pressed"',script)
                self.assertIn('aria-live',script)
                self.assertIn('source(links,src',script)
                self.assertIn('Not household bill dollars.',script)

    def test_latest_price_graph_matches_current_atlas_data(self):
        data=json.loads((ROOT/"data/place-impact/connected-metrics-v1.json").read_text(encoding="utf-8"))
        script=(UNIFIED/"atlas-visual-system.js").read_text(encoding="utf-8")
        for key,topic in (("transport","transport"),("housing","housing"),
                          ("groceries","groceries"),("health","health")):
            with self.subTest(topic=key):
                m=re.search(r'\{key:"'+key+r'",label:"[^"]+",value:([0-9.]+)',script)
                self.assertIsNotNone(m)
                self.assertAlmostEqual(float(m.group(1)),float(data["national"][topic]["yoyPct"]),places=2)

    def test_market_power_uses_single_platform_nav_and_visual_story(self):
        for folder in SITES:
            with self.subTest(site=folder.name):
                html=(folder/"market-power.html").read_text(encoding="utf-8")
                self.assertEqual(html.count('id="pa-global-header"'),1)
                self.assertNotIn('class="navlinks"',html)
                self.assertNotIn('<header><div class="wrap top">',html)
                self.assertIn('class="market-related-nav"',html)
                self.assertIn('href="global-navigation.css"',html)
                self.assertIn('src="atlas-visual-system.js"',html)
                self.assertIn('id="marketBars"',html)
                self.assertIn('id="explore"',html)
                self.assertEqual(html.count('data-pa-nav='),6)
                self.assertEqual(html.count('<main>'),1)
                self.assertIn('market-power-pathways.js',html)
                self.assertIn('market-power-household.js',html)
                theme=(folder/"market-power-pathways.css").read_text(encoding="utf-8")
                self.assertIn('background:var(--vs6-cream,#faf6ed)',theme)
                self.assertNotIn("#ddf1e5",theme)
                self.assertNotIn('body[data-pa-page="market-power"] > header',theme)
        unified=(UNIFIED/"market-power.html").read_text(encoding="utf-8")
        self.assertIn('data-pa-nav="research" aria-current="page"',unified)
        script=(UNIFIED/"visual-story-v6.js").read_text(encoding="utf-8")
        self.assertIn('documentPath==="market-power.html"',script)
        self.assertIn('PowerAtlasMarketPower.mount(section)',script)

    def test_class_actions_visual_is_filing_sourced(self):
        html=(UNIFIED/"class-actions.html").read_text(encoding="utf-8")
        script=(UNIFIED/"class-actions-visual.js").read_text(encoding="utf-8")
        data=json.loads((ROOT/"data/consumer-class-actions/cases-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"],"power-atlas.consumer-class-actions.v1")
        self.assertIn("class-actions-visual.css",html)
        self.assertIn('src="class-actions-visual.js"',html)
        self.assertIn("poweratlas:class-actions-loaded",html)
        self.assertIn("poweratlas:class-actions-loaded",script)
        self.assertIn('claimStatus==="open-as-of-review"',script)
        self.assertIn("Check official settlement notices",script)

    def test_preserve_service_accountability_update(self):
        html=(RESEARCH/"consumer-practices.html").read_text(encoding="utf-8")
        self.assertIn("service-accountability.html",html)
        self.assertTrue((RESEARCH/"service-accountability.html").exists())

    @unittest.skipUnless(shutil.which("node"),"Node.js not available")
    def test_java_script_syntax(self):
        paths=[folder/"atlas-visual-system.js" for folder in SITES]
        paths.append(UNIFIED/"class-actions-visual.js")
        for path in paths:
            with self.subTest(path=path.name):
                proc=subprocess.run(["node","--check",str(path)],capture_output=True,text=True,timeout=20)
                self.assertEqual(proc.returncode,0,proc.stderr)

if __name__=="__main__":
    unittest.main()
