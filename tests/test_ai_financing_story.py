"""Acceptance checks for the November 2026 AI-financing visual documentary."""
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[1] / "platform" / "unified"
STORY = BASE / "ai-financing-shock.html"
HOME = BASE / "my-life.html"
FRAGILITY = BASE / "economic-fragility.html"

class AIFinancingStoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = STORY.read_text(encoding="utf-8")
        cls.home = HOME.read_text(encoding="utf-8")
        cls.fragility = FRAGILITY.read_text(encoding="utf-8")

    def test_story_is_integrated(self):
        self.assertIn('href="ai-financing-shock.html"', self.home)
        self.assertIn('href="ai-financing-shock.html"', self.fragility)

    def test_three_scenarios_are_interactive(self):
        for name in ("contained", "squeeze", "contagion"):
            self.assertIn('data-scenario="' + name + '"', self.story)
            self.assertIn(name + ":{", self.story)
        self.assertIn('aria-pressed="true"', self.story)
        self.assertIn('replaceChildren(', self.story)

    def test_key_evidence_and_cautions(self):
        for token in ("November 12, 2026", "$300B", "$650B", "$1.4T",
                      "https://www.imf.org", "https://apnews.com", "https://www.reuters.com",
                      "not directly comparable", "Not a live market feed",
                      "not yet established", "HYPOTHETICAL", "realized losses"):
            self.assertIn(token.lower(), self.story.lower())

    def test_no_unverified_live_or_crash_claim(self):
        self.assertNotIn("guaranteed crash", self.story.lower())
        self.assertNotIn("real-time feed", self.story.lower())
        self.assertIn('src="bug-report.js"', self.story)
        self.assertEqual(3, len(re.findall(r'data-scenario="(?:contained|squeeze|contagion)"', self.story)))

    def test_sources_and_links(self):
        self.assertIn('href="economic-fragility.html"', self.story)
        self.assertIn('href="banking-power.html"', self.story)
        self.assertIn('href="take-action.html"', self.story)

if __name__ == "__main__":
    unittest.main()
