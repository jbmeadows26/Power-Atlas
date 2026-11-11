"""Source and visual integrity checks for the Wealth Advantage comparison."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
SITES = [ROOT / "platform/unified", ROOT / "site"]

class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.inline = []
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_script = not dict(attrs).get("src")
    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
    def handle_data(self, data):
        if self.in_script and data.strip():
            self.inline.append(data)

class WealthAdvantageTests(unittest.TestCase):
    def test_pages_identical_and_linked(self):
        a, b = [(site / "wealth-advantage.html").read_text() for site in SITES]
        self.assertEqual(a, b)
        self.assertEqual(a.count('name:"'), 10)
        self.assertIn('href="atlas-visual-system.css"', a)
        self.assertIn('src="atlas-visual-system.js"', a)
        self.assertNotIn('href="my-life.html', a)
        self.assertIn('https://power-atlas-unified.vercel.app/take-action.html', a)
        for site in SITES:
            self.assertIn("wealth-advantage.html", (site / "visual-story-v6.js").read_text())
            self.assertIn('href="wealth-advantage.html"', (site / "consumer-practices.html").read_text())
        self.assertEqual((SITES[0]/"visual-story-v6.js").read_bytes(),
                         (SITES[1]/"visual-story-v6.js").read_bytes())

    def test_approved_v6_visual_first_shell_is_mandatory(self):
        """Pages must present the approved V6 story before the research cards."""
        for site in SITES:
            page = (site / "wealth-advantage.html").read_text()
            self.assertIn('class="vs6-topic vs6-topic--money wa-v6-cover"', page)
            self.assertIn('class="wa-v6-graphic"', page)
            self.assertIn('id="wa-v6-expand"', page)
            self.assertIn('aria-controls="wa-deep-dive"', page)
            self.assertIn('class="wa-case-head wa-case-open"', page)
            self.assertIn('class="wa-case-reveal"', page)
            self.assertIn('class="wa-case-glyph"', page)
            self.assertIn('vs6-topic-expanded', page)
            self.assertNotIn('<section class="wa-hero">', page)
            self.assertEqual(page.count('id="pa-global-header"'), 1)
            self.assertEqual(page.count('data-pa-nav='), 6)
            self.assertIn('src="visual-story-v6.js"', page)
            self.assertIn('href="visual-story-v6.css"', page)
            self.assertIn('src="bug-report.js"', page)

    def test_all_comparisons_have_three_profiles_and_primary_sources(self):
        page = (SITES[0] / "wealth-advantage.html").read_text()
        self.assertIn('Ordinary household', page)
        self.assertIn('Small business owner', page)
        self.assertIn('High-wealth owner', page)
        self.assertIn('data-filter="all"', page)
        self.assertIn('aria-pressed="true"', page)
        self.assertIn('aria-expanded', page)
        self.assertGreaterEqual(page.count("https://www.irs.gov/"), 20)
        for name in ("private jet", "car you need", "operating expenses", "20% pass-through",
                     "Paycheck income", "investment property", "Sell a home", "Passing appreciated",
                     "Retirement", "borrowed money"):
            self.assertIn(name.lower(), page.lower())
        self.assertIn("does <strong>not</strong> prove", page)
        self.assertIn("$20,300", page)
        self.assertIn("hypothetical", page)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_inline_js_parses(self):
        page = (SITES[0] / "wealth-advantage.html").read_text()
        parser = ScriptParser()
        parser.feed(page)
        self.assertEqual(len(parser.inline), 1)
        result = subprocess.run(["node", "--check", "-"], input=parser.inline[0],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
