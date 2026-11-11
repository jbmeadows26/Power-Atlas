"""ZIP-driven visual story checks: measured Census ZCTA data, not invented costs."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
UNIFIED=ROOT/"platform"/"unified"
RESEARCH=ROOT/"site"

class ZIPVisualContextTests(unittest.TestCase):
    def test_shared_visual_assets_match_on_both_sites(self):
        for filename in ("visual-story-v6.js","visual-story-v6.css"):
            self.assertEqual((UNIFIED/filename).read_bytes(),(RESEARCH/filename).read_bytes())

    def test_zip_lookup_updates_visual_on_success_and_failure(self):
        html=(UNIFIED/"my-life.html").read_text()
        self.assertIn('poweratlas:zip-visual-context',html)
        self.assertIn("updateZIPVisualSnapshot(zip,name.textContent)",html)
        self.assertEqual(html.count("updateZIPVisualSnapshot(zip,name.textContent)"),2)
        self.assertIn("const seq=++paZIPVisualSequence",html)
        self.assertIn("seq===paZIPVisualSequence",html)
        self.assertIn('json?.release?.id!==provider.release',html)
        self.assertIn('json.data?.[geoid]',html)
        self.assertIn('evaluateMeasure(m,area[m.table]?.estimate)',html)
        self.assertNotIn("history.pushState",html[html.index("async function updateZIPVisualSnapshot"):html.index("async function lookUpZIP")])

    def test_source_has_four_existing_acs_definitions(self):
        source=json.loads((ROOT/"data"/"place-impact"/"local-measures-v1.json").read_text())
        self.assertEqual(source["provider"]["release"],"acs2024_5yr")
        for issue,table in (("housing","B25064"),("transport","B08301"),
                            ("groceries","B22003"),("health","B27001")):
            with self.subTest(issue=issue):
                m=source["issues"][issue]["measures"][0]
                self.assertEqual(m["table"],table)
                self.assertTrue(m["originalTable"].startswith("https://api.census.gov/"))
                self.assertTrue(m["columns"])

    def test_visual_has_data_comparisons_and_accessibility(self):
        script=(UNIFIED/"visual-story-v6.js").read_text()
        style=(UNIFIED/"visual-story-v6.css").read_text()
        for token in ("attachZIPVisual(section);","vs6-zip-chart","poweratlas:zip-visual-context",
                      "vs6-zip-track","vs6-zip-fill--us","vs6-zip-tile-value",
                      "vs6-zip-tile-value--unavailable","ZIP-area","No estimate inferred.",
                      "vs6-zip-method","vs6-zip-detail"):
            with self.subTest(token=token):
                self.assertIn(token,script)
        self.assertIn("if(documentPath!==\"my-life.html\")return;",script)
        self.assertIn("if(open?.getAttribute(\"aria-expanded\")===\"false\")open.click()",script)
        self.assertIn("if(have)",script)
        self.assertIn("@media(max-width:570px)",style)

    @unittest.skipUnless(shutil.which("node"),"Node.js unavailable")
    def test_shared_javascript_syntax(self):
        for site in (UNIFIED,RESEARCH):
            p=subprocess.run(["node","--check",str(site/"visual-story-v6.js")],
                             capture_output=True,text=True,timeout=20)
            self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__":
    unittest.main()
