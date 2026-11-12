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
        self.assertIn("ambiguous=one?.ambiguous===true",SCRIPT)
        self.assertIn("https://openamerica.io/api/zip-lookup/",SCRIPT)
        self.assertIn("const conflict=",SCRIPT)
        self.assertIn("houseOne.size!==houseTwo.size",SCRIPT)
        self.assertIn("Independent sources disagreed",SCRIPT)
        self.assertIn("ziplook.house.gov/htbin/findrep_house?ZIP=",SCRIPT)
        self.assertIn("ambiguous-notice",PAGE)
        self.assertIn("house.length>1",SCRIPT)
        self.assertIn("senateLookup",SCRIPT)

    def test_constrained_issue_and_question_selection(self):
        self.assertEqual(PAGE.count("data-issue="),8)
        self.assertEqual(PAGE.count("data-question="),4)
        self.assertIn('textarea id="message-preview" readonly',PAGE)
        self.assertIn('slice(0,500)',SCRIPT)
        self.assertIn("navigator.clipboard.writeText",SCRIPT)
        # ZIP is persistent locally, but the approved testing-only constituent
        # email may be staged in tab-scoped sessionStorage. No server storage,
        # verified office send, or unbounded browser persistence is allowed.
        self.assertIn('ZIP_KEY="power-atlas:visitor-zip:v1"',SCRIPT)
        self.assertIn("localStorage.setItem(ZIP_KEY,code)",SCRIPT)
        self.assertEqual(SCRIPT.count("localStorage.setItem("),1)
        self.assertNotIn('localStorage.setItem("message',SCRIPT)
        self.assertNotIn('localStorage.setItem("issue',SCRIPT)
        self.assertIn('sessionStorage.setItem("power-atlas:member-email-test:v1"',SCRIPT)
        self.assertEqual(SCRIPT.count("sessionStorage.setItem("),1)
        self.assertIn('status:"preview-only"',SCRIPT)
        self.assertIn('href="contact-tester.html"',PAGE)
        self.assertTrue((ROOT/"platform/unified/contact-tester.html").is_file())
        self.assertNotIn("method=\"post\"",PAGE.lower())
        self.assertNotIn("fetch(office",SCRIPT)
        self.assertNotIn("mailto:",SCRIPT)

    def test_citizen_influence_playbook_and_stronger_accountability(self):
        self.assertIn('class="ta-civic-lobby"', PAGE)
        self.assertIn('id="civic-power-title"', PAGE)
        self.assertIn('id="follow-through"', PAGE)
        self.assertIn('href="#contact"', PAGE)
        self.assertIn('data-question="meeting"', PAGE)
        self.assertIn('Request a staff meeting', PAGE)
        self.assertIn('id="copy-brief"', PAGE)
        self.assertIn('id="brief-preview"', PAGE)
        self.assertIn('https://www.house.gov/visitors/meeting-with-your-member', PAGE)
        self.assertIn('https://www.senate.gov/senators/contact/', PAGE)
        self.assertIn('Constituent accountability:', SCRIPT)
        self.assertIn('Identify concrete action you have taken', SCRIPT)
        self.assertIn('Identify the hearings, reports', SCRIPT)
        self.assertIn('I request a meeting with you', SCRIPT)
        self.assertIn('Please give a substantive written response with specific next steps and a timeline', SCRIPT)
        self.assertIn('function makeBrief()', SCRIPT)
        self.assertIn('Copy my issue brief', SCRIPT)
        self.assertIn('This is a starting brief, not evidence that an office received', SCRIPT)
        self.assertIn('.ta-lobby-track', CSS)
        self.assertIn('data-question-jump="meeting"', PAGE)
        self.assertIn('data-question-jump="action"', PAGE)
        self.assertIn('document.querySelectorAll("[data-question-jump]")', SCRIPT)
        self.assertIn('button.click()', SCRIPT)
        self.assertIn('href="atlas-visual-system.css"', PAGE)
        self.assertIn('href="visual-story-v6.css"', PAGE)
        self.assertIn('src="atlas-visual-system.js"', PAGE)
        self.assertIn('src="visual-story-v6.js"', PAGE)
        self.assertIn('var(--vs6-cream,#faf6ed)', CSS)
        self.assertIn('var(--vs6-night,#102d3d)', CSS)
        self.assertIn('color:#148c7e', CSS)

        self.assertIn('.ta-brief-disclosure', CSS)
        self.assertNotIn('type="file"', PAGE)

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

    def test_hero_chamber_cards_are_real_keyboard_controls(self):
        for chamber in ("house", "senate"):
            self.assertIn('class="ta-chamber-link" data-chamber="'+chamber+'" aria-pressed="false"', PAGE)
        self.assertIn('aria-controls="member-results"', PAGE)
        self.assertNotIn('class="ta-visual" aria-hidden="true"', PAGE)
        self.assertIn('.ta-visual-nodes>.ta-chamber-link', CSS)
        self.assertIn('.ta-member--selected-chamber', CSS)
        self.assertIn('min-height:68px', CSS)

    def test_house_and_senate_taps_run_the_correct_lookup_flow(self):
        for token in (
            'document.querySelectorAll(".ta-chamber-link")',
            'button.addEventListener("click"',
            'selectedChamber=chamber',
            'card.dataset.chamber=m.chamber',
            'card.tabIndex=-1',
            'status.textContent=chamber==="house"',
            '$("find").scrollIntoView',
            'input.focus({preventScroll:true})',
            'locate(code).then(()=>focusChosenChamber(chamber))',
            'focusChosenChamber(selectedChamber)',
            'matches[0].scrollIntoView',
            'card.classList.toggle("ta-member--selected-chamber"',
        ):
            with self.subTest(token=token):
                self.assertIn(token,SCRIPT)

    @unittest.skipUnless(shutil.which("node"),"Node.js unavailable")
    def test_javascript_syntax(self):
        for path in (ROOT/"platform/unified/take-action.js",ROOT/"platform/unified/visual-story-v6.js"):
            result=subprocess.run(["node","--check",str(path)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)

if __name__=="__main__": unittest.main()
