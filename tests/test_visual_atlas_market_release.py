"""Production guardrails for the Nov 2026 market sell-off within the visual atlas."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"site"
U=ROOT/"platform"/"unified"

class AtlasMarketReleaseTests(unittest.TestCase):
    def test_published_data_is_dated_and_evidence_bounded(self):
        d=json.loads((S/"data/economic-fragility/2027-v1.json").read_text())
        self.assertEqual(d["publicationStatus"],"published")
        self.assertEqual(d["asOf"],"2026-11-09")
        m=d["marketStress"]
        self.assertEqual(m["asOf"],d["asOf"])
        self.assertEqual([(x["id"],x["drawdownPercent"]) for x in m["measures"]],[("sp500",3.44),("nasdaq",8.5),("sox",31.4)])
        self.assertEqual(len(m["historicalSp500Drawdowns"]),5)
        self.assertFalse(m["historicalSample"]["currentSp500InSample"])
        self.assertEqual(m["historicalSample"]["methodologyStatus"],"third_party_counts_not_independently_rebuilt")
        self.assertTrue(all(x["source"].startswith("https://") for x in m["measures"]))
        self.assertIn("not a model of future crash probability",m["historicalSample"]["description"])
    def test_live_page_integrates_clickable_market_bars_and_sources(self):
        h=(S/"economic-fragility.html").read_text()
        for key in ('id="markets"','id="marketBars"','id="historicBars"','id="marketPathways"','class="marketItem"','s.historicalSp500Drawdowns','id="financeChart"','src="atlas-visual-system.js"','href="atlas-visual-system.css"','href="favicon.svg"'):
            self.assertIn(key,h)
        self.assertIn('fetch("./data/economic-fragility/2027-v1.json"',h)
        self.assertIn('publicationStatus!=="published"',h)
        self.assertNotIn("UNPUBLISHED · REVIEW DRAFT",h)
        self.assertNotIn("review_only_not_approved",h)
    def test_new_visual_design_has_eight_stories_and_no_review_redirects(self):
        for folder in (S,U):
            js=(folder/"atlas-visual-system.js").read_text()
            css=(folder/"atlas-visual-system.css").read_text()
            for phrase in ('07 · Economic resilience','08 · Class actions','economic-fragility.html','class-actions.html','Eight paths into the evidence','const researchProductionBase='):
                self.assertIn(phrase,js)
            for forbidden in ('__PA4_UNIFIED_PREVIEW__','power-atlas-visual-review.vercel.app','Preview-only link rewrites:','DESIGN REVIEW · NOT PRODUCTION','noindex,nofollow'):
                self.assertNotIn(forbidden,js)
            self.assertIn(".pa4-tile:nth-child(7)",css)
            self.assertIn(".pa4-tile--claims",css)
            self.assertTrue((folder/"favicon.svg").is_file())
            self.assertIn('href="favicon.svg"', (folder/"index.html").read_text())
    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_js_syntax(self):
        for folder in (S,U):
            p=subprocess.run(["node","--check",str(folder/"atlas-visual-system.js")],capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__": unittest.main()
