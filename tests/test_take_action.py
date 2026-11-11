"""Power Atlas Take Action release checks: privacy-first official contact handoff."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
UNIFIED=ROOT/"platform"/"unified"
RESEARCH=ROOT/"site"

class TakeActionTests(unittest.TestCase):
    def test_both_frontends_have_identical_page_and_assets(self):
        for filename in ("take-action.css","take-action.js"):
            with self.subTest(filename=filename):
                self.assertEqual((UNIFIED/filename).read_bytes(),(RESEARCH/filename).read_bytes())

    def test_single_canonical_page(self):
        self.assertTrue((UNIFIED/"take-action.html").exists())
        self.assertFalse((RESEARCH/"take-action.html").exists())

    def test_visual_shell_and_navigational_journey(self):
        html=(UNIFIED/"take-action.html").read_text()
        self.assertEqual(html.count('id="pa-global-header"'),1)
        self.assertIn('aria-current="page"',html)
        self.assertIn('href="global-navigation.css"',html)
        self.assertIn('href="atlas-visual-system.css"',html)
        self.assertIn('src="atlas-visual-system.js"',html)
        self.assertIn('href="take-action.css"',html)
        self.assertIn('src="take-action.js"',html)
        self.assertIn('src="bug-report.js"',html)
        self.assertIn('id="zipForm"',html)
        self.assertIn('id="memberGrid"',html)
        self.assertIn('id="issues"',html)
        self.assertIn('id="copyMessage"',html)
        self.assertIn('id="contactMember"',html)
        for path in (UNIFIED/"atlas-visual-system.js",RESEARCH/"atlas-visual-system.js"):
            nav=path.read_text()
            self.assertIn('["action","take-action.html","Actions"]',nav)
            self.assertNotIn('["action","my-life.html#how"',nav)
        for path in (UNIFIED/"visual-story-v6.js",RESEARCH/"visual-story-v6.js"):
            self.assertIn('["action","Actions","take-action.html"]',path.read_text())

    def test_member_lookup_has_error_fallbacks_and_no_guesses(self):
        js=(UNIFIED/"take-action.js").read_text()
        self.assertIn("https://openamerica.io/api/zip-lookup/",js)
        self.assertIn("https://www.house.gov/representatives/find-your-representative",js)
        self.assertIn("https://www.congress.gov/members/find-your-member",js)
        self.assertIn("https://www.senate.gov/senators/contact/",js)
        self.assertIn("representatives.length>1",js)
        self.assertIn("Confirm your full address",js)
        self.assertIn("data.current_member!==true",js)
        self.assertIn('host.endsWith(".house.gov")',js)
        self.assertIn('host.endsWith(".senate.gov")',js)

    def test_civic_guardrails(self):
        html=(UNIFIED/"take-action.html").read_text()
        js=(UNIFIED/"take-action.js").read_text()
        self.assertIn('maxlength="280"',html)
        self.assertIn('maxlength="5"',html)
        self.assertIn('type="submit" id="findButton"',html)
        self.assertIn('No platform inbox',html)
        self.assertIn("blockedNote",js)
        self.assertIn("navigator.clipboard",js)
        self.assertIn('credentials:"omit"',js)
        self.assertIn("No current members returned",js)
        self.assertNotIn("fetch('/send",js)
        self.assertNotIn("method:'POST'",js)
        self.assertNotIn('type="file"',html)
        self.assertGreaterEqual(js.count('page:"'),8)

    @unittest.skipUnless(shutil.which("node"),"Node.js unavailable")
    def test_both_site_scripts_parse(self):
        for root in (UNIFIED,RESEARCH):
            p=subprocess.run(["node","--check",str(root/"take-action.js")],
                capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__":
    unittest.main()
