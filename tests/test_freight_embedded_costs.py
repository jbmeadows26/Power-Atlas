"""Regression checks for freight costs embedded in everyday goods.
Review-only. Run python -m unittest discover -s tests -p test_freight_embedded_costs.py
"""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
FREIGHT=ROOT/"data/place-impact/freight-embedded-costs-v1.json"
UNIFIED=ROOT/"platform/unified"
RESEARCH=ROOT/"site"

class FreightEmbeddedCostsTests(unittest.TestCase):
    def test_measures_have_different_dates_and_bases(self):
        data=json.loads(FREIGHT.read_text())
        self.assertEqual(data["schema"],"power-atlas.freight-embedded-costs.v1")
        x=data["verified"]
        self.assertEqual(x["truckFreightPpiYoY"]["value"],14.3)
        self.assertEqual(x["truckFreightPpiYoY"]["period"],"2026-08")
        self.assertEqual(x["transportationConsumerCpiYoY"]["period"],"2026-09")
        self.assertAlmostEqual(x["foodAtHomeFarmShare"]["value"]+x["foodAtHomeMarketingShare"]["value"],100)
        self.assertEqual(x["foodAtHomeFarmShare"]["period"],"2024")
        for item in x.values():
            self.assertTrue(item["source"].startswith("https://"))
            self.assertTrue(item["basis"])
            self.assertTrue(item["geography"])
    def test_no_double_count_or_unverified_pass_through(self):
        data=json.loads(FREIGHT.read_text())
        text=" ".join(data["principles"]).lower()
        self.assertIn("retail goods cpi already embeds freight",text)
        self.assertIn("no unobserved pass-through",text)
        self.assertIn("not equate usda marketing share with freight share",text)
    def test_research_explorer_same_on_both_sites(self):
        a=(UNIFIED/"freight-impact.html").read_text()
        b=(RESEARCH/"freight-impact.html").read_text()
        self.assertEqual(a,b.replace('href="https://power-atlas-unified.vercel.app/my-life.html"','href="my-life.html"'))
        for token in ("data-sector=\"groceries\"","data-sector=\"medicine\"",
                      "data-sector=\"housing\"","data-sector=\"shopping\"",
                      "81.5¢","18.5¢","+14.3%","+7.77%",
                      "81.5¢ freight charge","not a measured freight share",
                      "aria-pressed","fred.stlouisfed.org","ers.usda.gov","bts.gov"):
            self.assertIn(token,a)
    def test_integrated_into_home_and_cross_category_surfaces(self):
        for site in (UNIFIED,RESEARCH):
            js=(site/"visual-first-v5.js").read_text()
            css=(site/"visual-first-v5.css").read_text()
            atlas=(site/"atlas-visual-system.js").read_text()
            self.assertIn("freightFeature(",js)
            self.assertIn('card.href="freight-impact.html"',js)
            self.assertIn('"my-life.html","consumer-practices.html","corporate-ownership.html","market-power.html"',js)
            self.assertIn(".pa5-freight-feature",css)
            self.assertIn('key:"transport",label:"Transportation"',atlas)
            self.assertTrue((site/"freight-impact.html").exists())
    @unittest.skipUnless(shutil.which("node"),"Node.js unavailable")
    def test_javascript_syntax(self):
        for site in (UNIFIED,RESEARCH):
            for name in ("atlas-visual-system.js","visual-first-v5.js"):
                path=site/name
                p=subprocess.run(["node","--check",str(path)],capture_output=True,text=True,timeout=20)
                self.assertEqual(p.returncode,0,p.stderr)
if __name__=="__main__":
    unittest.main()
