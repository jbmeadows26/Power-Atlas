"""Visual-first v5 review gates. No network or consumer/source data changes."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SITES=(ROOT/"platform"/"unified", ROOT/"site")
REQUIRED_UNIFIED=("index.html","my-life.html","corporate-ownership.html","consumer-practices.html","class-actions.html","dark-money.html","market-power.html","money-scale.html","reform-lab.html","cost-gap.html")
REQUIRED_RESEARCH=("index.html","consumer-practices.html","market-power.html","service-accountability.html","economic-fragility.html")

class VisualFirstReviewTests(unittest.TestCase):
    def test_shared_assets_identical_on_both_sites(self):
        for name in ("visual-first-v5.js","visual-first-v5.css","atlas-visual-system.js"):
            with self.subTest(asset=name):
                self.assertEqual((SITES[0]/name).read_bytes(),(SITES[1]/name).read_bytes())

    def test_required_pages_load_visual_first_enhancement(self):
        for folder,pages in ((SITES[0],REQUIRED_UNIFIED),(SITES[1],REQUIRED_RESEARCH)):
            script=(folder/"atlas-visual-system.js").read_text()
            self.assertIn('script.src="visual-first-v5.js"',script)
            self.assertIn('style.href="visual-first-v5.css"',script)
            for page in pages:
                with self.subTest(page=page):
                    self.assertTrue((folder/page).is_file())
                    self.assertIn("atlas-visual-system.js",(folder/page).read_text())

    def test_transportation_visible_and_sourced(self):
        for folder in SITES:
            script=(folder/"visual-first-v5.js").read_text()
            chart=(folder/"atlas-visual-system.js").read_text()
            css=(folder/"visual-first-v5.css").read_text()
            with self.subTest(folder=str(folder)):
                self.assertIn('pa5-transport-spotlight',script)
                self.assertIn('"+7.77%"',script)
                self.assertIn('Sep 2026',script)
                self.assertIn('fred.stlouisfed.org/data/CPITRNSL',script)
                self.assertIn('key:"transport",label:"Transportation",value:7.77',chart)
                self.assertIn('.pa5-transport-spotlight',css)
                self.assertIn('html[data-pa5] .pa4-bar',css)

    def test_research_is_never_deleted_and_has_explicit_controls(self):
        for folder in SITES:
            script=(folder/"visual-first-v5.js").read_text()
            for required in ('pa5-home-hidden','pa5-hidden-chapter','aria-expanded','aria-controls','reveal(', 'pa5-library-button', 'pa5-chapter-card', 'scrollIntoView'):
                with self.subTest(folder=str(folder),control=required):
                    self.assertIn(required,script)
            self.assertIn('const path=(location.pathname.split("/")',script)
            self.assertNotIn("document.body.innerHTML=",script)
            self.assertNotIn("data-pa5-loader",script) # loader lives in shared JS

    def test_active_routes_and_data_sources_not_overwritten(self):
        for page in ("dark-money.html","class-actions.html","source-audit.html","my-life.html","consumer-practices.html"):
            self.assertTrue((SITES[0]/page).exists())
        assert (ROOT/"data"/"place-impact"/"connected-metrics-v1.json").exists()

    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_js_parses(self):
        for folder in SITES:
            for name in ("atlas-visual-system.js","visual-first-v5.js"):
                with self.subTest(folder=str(folder),js=name):
                    p=subprocess.run(["node","--check",str(folder/name)],capture_output=True,text=True,timeout=20)
                    self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__":
    unittest.main()
