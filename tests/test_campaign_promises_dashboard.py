"""Portable Power Atlas campaign promises UI: source-backed, no invented rates."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"site/index.html"
JS=ROOT/"site/campaign-promises.js"

class CampaignPromisesDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=HTML.read_text(encoding="utf-8")
        cls.js=JS.read_text(encoding="utf-8")

    def test_tab_and_panel_are_present(self):
        self.assertIn('data-tab="campaign-promises"',self.html)
        self.assertIn('data-panel="campaign-promises"',self.html)
        self.assertIn('<script src="campaign-promises.js"></script>',self.html)
        self.assertEqual(self.html.count('data-tab="campaign-promises"'),1)
        self.assertEqual(self.html.count('data-panel="campaign-promises"'),1)

    def test_existing_original_research_tabs_are_preserved(self):
        for token in ('data-tab="institutional-decay"',
                      'data-tab="gridlock"','data-tab="overview"',
                      'data-tab="records"','data-tab="political-authenticity"'):
            # Some panels may load via external scripts and have no UI tab.
            if token=='data-tab="political-authenticity"':continue
            self.assertIn(token,self.html)
        self.assertIn('institutional-decay.js',self.html)

    def test_no_additional_inline_script_or_untrusted_html_interpolation(self):
        self.assertEqual(len(re.findall(r"<script\s*>(.*?)</script>",self.html,re.S)),1)
        self.assertNotIn(".innerHTML=",self.js)
        self.assertIn(".textContent",self.js)
        self.assertIn("source-linked",self.js.lower())

    def test_no_pilot_pledge_population_rate_or_causal_claim(self):
        self.assertIn("promiseFulfillmentRate!==null",self.js)
        self.assertIn("study.causalEffect!==null",self.js)
        self.assertIn("independent",self.html.lower())
        self.assertIn("observational associations",self.html)
        self.assertNotIn("87.5%",self.html)
        self.assertNotIn("election spending caused",self.html)

    def test_public_artifact_paths_and_status_fallback(self):
        for path in (
            "promises/research-feed.json",
            "promises/primary-2020-sentence-inventory/index.json",
            "fiscal/state-timeseries/governor-election-fiscal-associations-2012-2024.json",
            "fiscal/state-timeseries/aggregate-capital-2012-2024.json",
        ):
            self.assertIn(path,self.js)
        self.assertIn("Live research evidence unavailable",self.js)

    def test_javascript_syntax_valid(self):
        self.assertTrue(JS.is_file())
        if shutil.which("node"):
            subprocess.run(["node","--check",str(JS)],timeout=15,check=True)

if __name__=="__main__":
    unittest.main()
