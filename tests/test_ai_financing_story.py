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

    def test_megaspeed_evidence_trail(self):
        for token in ('data-mega="singapore"', 'data-mega="malaysia"', 'data-mega="us"',
                      'data-mega="money"', 'insufficient evidence', 'six others',
                      'November 13, 2026', 'Speedmatrix', 'not about espionage',
                      'not a finding', 'not proven losses'):
            self.assertIn(token.lower(), self.story.lower())
        self.assertIn('getElementById("megaSources").replaceChildren(', self.story)
        self.assertIn("https://www.mha.gov.sg/", self.story)
        self.assertIn("https://www.reuters.com/world/asia-pacific/malaysia-", self.story)
        self.assertEqual(4, len(re.findall(r'data-mega="(?:singapore|malaysia|us|money)"', self.story)))

    def test_federal_oversight_claim_boundaries(self):
        for term in ('data-oversight="bis"', 'data-oversight="cabinet"',
                     'data-oversight="hardware"', 'data-oversight="court"',
                     'Kistenmacher', 'undersecretary', 'November 13, 2026',
                     'does not prove that Nvidia caused the pause',
                     'not a judicial finding', 'not proven illicit transfers'):
            self.assertIn(term.lower(), self.story.lower())
        self.assertEqual(4, len(re.findall(r'data-oversight="(?:bis|cabinet|hardware|court)"', self.story)))
        self.assertIn('getElementById("oversightSources").replaceChildren(', self.story)

    def test_interactive_documentary_primary_journey(self):
        for token in ('id="evidence-stage"', 'data-investigation="chips"',
                      'data-investigation="oversight"', 'data-investigation="money"',
                      'data-discovery="0"', 'data-discovery="3"',
                      'id="investigationNext"', 'id="investigationPrevious"',
                      'id="deepResearch" hidden', 'aria-controls="deepResearch"',
                      'class="investigate-rail"', '50,000-processor discrepancy',
                      'Not a confirmed smuggling tally', 'q("investigationSources").replaceChildren'):
            self.assertIn(token.lower(), self.story.lower())
        self.assertEqual(3, len(re.findall(r'data-investigation="(?:chips|oversight|money)"', self.story)))
        self.assertEqual(4, len(re.findall(r'data-discovery="[0-3]"', self.story)))
        self.assertIn("openArchive(true)", self.story)
        self.assertIn('href="#evidence-stage"', self.story)

    def test_homepage_embeds_interactive_investigation(self):
        for token in ('id="featuredAiInvestigation"', 'data-home-ai-trail="chips"',
                      'data-home-ai-trail="oversight"', 'data-home-ai-trail="money"',
                      'data-home-ai-node="0"', 'data-home-ai-node="3"',
                      'id="homeAiTitle"', 'id="homeAiMetric"',
                      'href="ai-financing-shock.html#evidence-stage"',
                      'q("homeAiSource")', 'a.href=r[8]'):
            self.assertIn(token.lower(), self.home.lower())
        self.assertEqual(3,len(re.findall(r'data-home-ai-trail="(?:chips|oversight|money)"',self.home)))
        self.assertEqual(4,len(re.findall(r'data-home-ai-node="[0-3]"',self.home)))
        self.assertEqual(1,len(re.findall(r'id="featuredAiInvestigation"',self.home)))

    def test_sources_and_links(self):
        self.assertIn('href="economic-fragility.html"', self.story)
        self.assertIn('href="banking-power.html"', self.story)
        self.assertIn('href="take-action.html"', self.story)

if __name__ == "__main__":
    unittest.main()
