"""Safety and navigation checks for Power Atlas civic action page."""
from pathlib import Path
import subprocess
import shutil
import unittest

ROOT=Path(__file__).resolve().parents[1]
PAGE=(ROOT/"platform/unified/take-action.html").read_text()
SCRIPT=(ROOT/"platform/unified/take-action.js").read_text()
CSS=(ROOT/"platform/unified/take-action.css").read_text()

class CivicActionTests(unittest.TestCase):
    def test_member_finder_and_official_handoffs(self):
        self.assertIn("https://www.congress.gov/members/find-your-member",PAGE)
        self.assertIn("https://www.house.gov/representatives/find-your-representative",PAGE)
        self.assertIn("https://www.senate.gov/",PAGE)
        self.assertIn("https://repscontact.com/api/reps?zip=",SCRIPT)
        self.assertIn('credentials:"omit"',SCRIPT)
        self.assertIn("ambiguous=data.ambiguous===true",SCRIPT)
        self.assertIn("ziplook.house.gov/htbin/findrep_house?ZIP=",SCRIPT)
        self.assertIn("ambiguous-notice",PAGE)
        self.assertIn("house.length>1",SCRIPT)
        self.assertIn("senateLookup",SCRIPT)

    def test_constrained_issue_and_question_selection(self):
        self.assertEqual(PAGE.count("data-issue="),8)
        self.assertEqual(PAGE.count("data-question="),3)
        self.assertIn('textarea id="message-preview" readonly',PAGE)
        self.assertIn('slice(0,500)',SCRIPT)
        self.assertIn("navigator.clipboard.writeText",SCRIPT)
        self.assertNotIn("localStorage",SCRIPT)
        self.assertNotIn("sessionStorage",SCRIPT)
        self.assertNotIn("method=\"post\"",PAGE.lower())
        self.assertNotIn("fetch(office",SCRIPT)
        self.assertNotIn("mailto:",SCRIPT)

    def test_matching_nav_and_design_shell(self):
        self.assertIn('data-pa-nav="action" aria-current="page"',PAGE)
        self.assertIn('href="take-action.html"',PAGE)
        self.assertIn("ta-visual",PAGE)
        self.assertIn("@media(max-width:650px)",CSS)
        unified=(ROOT/"platform/unified/visual-story-v6.js").read_bytes()
        research=(ROOT/"site/visual-story-v6.js").read_bytes()
        self.assertEqual(unified,research)
        self.assertIn('["action","Actions","take-action.html"]',unified.decode())
        self.assertIn('documentPath==="take-action.html"?"action"',unified.decode())

    @unittest.skipUnless(shutil.which("node"),"Node.js unavailable")
    def test_javascript_syntax(self):
        for path in (ROOT/"platform/unified/take-action.js",ROOT/"platform/unified/visual-story-v6.js"):
            result=subprocess.run(["node","--check",str(path)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)

if __name__=="__main__": unittest.main()
