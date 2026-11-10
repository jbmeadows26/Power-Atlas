"""Regression and data-integrity checks for the evidence-first two-place Cost Gap."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "platform/unified/cost-gap.html"
JS = ROOT / "platform/unified/cost-gap.js"
CSS = ROOT / "platform/unified/cost-gap.css"
LIFE = ROOT / "platform/unified/my-life.html"
INDEX = ROOT / "platform/unified/index.html"
RESEARCH = ROOT / "site/index.html"

class CostGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.js = JS.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")

    def test_navigation_integration(self):
        self.assertIn('href="cost-gap.html"', LIFE.read_text(encoding="utf-8"))
        self.assertIn('href="cost-gap.html"', INDEX.read_text(encoding="utf-8"))
        self.assertIn("power-atlas-unified.vercel.app/cost-gap.html", RESEARCH.read_text(encoding="utf-8"))
        self.assertIn("cost-gap.css", LIFE.read_text(encoding="utf-8"))
        self.assertIn("cost-gap.css", INDEX.read_text(encoding="utf-8"))

    def test_controls_and_accessibility(self):
        for token in ['id="cg-form"', 'id="cg-zip-a"', 'id="cg-zip-b"', 'id="cg-view"', 'aria-live="polite"',
                      'data-topic="housing"', 'data-topic="transport"', 'data-topic="groceries"',
                      'data-topic="health"', 'data-topic="utilities"', 'data-topic="schools"',
                      'data-a="10001" data-b="19103"', 'id="cg-method-title"']:
            self.assertIn(token, self.html)
        self.assertIn('data-bedroom', self.js)
        self.assertIn('aria-pressed', self.js)
        self.assertIn('@media(max-width:520px)', self.css)

    def test_evidence_safeguards_and_no_calculator(self):
        for phrase in ["not a budget or relocation calculator", "not a statistical attribution",
                       "not apartment listings", "No ZIPs are stored", "Multifamily Today", "CC BY 4.0"]:
            self.assertIn(phrase.lower(), self.html.lower())
        for token in ["d.fy!==2027", "records=d.zips[place.zip]", "Array.isArray(row[2])",
                      "Different source years", "No figures have been inferred", "No validated identical city-level measure"]:
            self.assertIn(token, self.js)
        for blocked in ["localStorage", "sessionStorage", "navigator.geolocation", "sendBeacon", "grossTotal", "salaryInput"]:
            self.assertNotIn(blocked, self.js)

    def test_official_hud_derived_snapshot(self):
        expected = {"NY": ("10001", 4460), "PA": ("19103", 2790),
                    "NJ": ("07010", 2340), "IL": ("60601", 3020),
                    "CA": ("90012", 3150)}
        for state, (zip_code, two_bed) in expected.items():
            with self.subTest(state=state):
                d = json.loads((ROOT / "data/housing/bedroom-rents" / (state+".json")).read_text(encoding="utf-8"))
                self.assertEqual(d["fy"], 2027)
                self.assertEqual(d["effective"], "2026-10-01")
                self.assertEqual(d["officialSource"], "https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html")
                self.assertEqual(d["license"], "CC BY 4.0")
                self.assertEqual(d["zips"][zip_code][0][1][2], two_bed)
        self.assertEqual(4460-2790, 1670)

    def test_source_urls_and_methodology(self):
        self.assertIn("https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html", self.html)
        self.assertIn("https://multifamily.today/data/", self.html)
        self.assertIn("https://www.bls.gov/news.release/cesan.htm", self.html)
        self.assertIn("https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/housing/bedroom-rents/", self.js)

    def test_js_and_dom_smoke(self):
        if not shutil.which("node"):
            self.skipTest("Node unavailable")
        for cmd in (["node", "--check", str(JS)], ["node", str(ROOT / "tests/cost-gap-dom-smoke.cjs")]):
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=25)
            self.assertEqual(p.returncode, 0, p.stdout+"\n"+p.stderr)

if __name__ == "__main__":
    unittest.main()
