"""Cheap design/source contract checks; live browser QA remains a separate gate."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "platform" / "unified"
CATALOG = ROOT / "data" / "health" / "sitewide-missing-sources-v1.json"

class V6SiteAcceptanceTests(unittest.TestCase):
    def test_common_shell_is_loaded_on_all_unified_pages(self):
        html_files = sorted(WEB.glob("*.html"))
        self.assertGreaterEqual(len(html_files), 25)
        for page in html_files:
            body = page.read_text(encoding="utf-8")
            with self.subTest(page=page.name):
                self.assertIn("atlas-visual-system.js", body,
                              "Unshared shell can produce a competing design")
                self.assertIn("bug-report.js", body,
                              "Bug report entry point must exist on every page")

    def test_single_journey_and_real_action_destination(self):
        shell = (WEB / "atlas-visual-system.js").read_text(encoding="utf-8")
        v6 = (WEB / "visual-story-v6.js").read_text(encoding="utf-8")
        self.assertIn('["action","take-action.html","Actions"]', shell)
        self.assertNotIn('["action","my-life.html#how","Actions"]', shell)
        self.assertIn('actionLink.href=local?"take-action.html"', v6)
        for label in ("Start Here", "Issues", "Costs", "The Why", "Actions", "Research"):
            self.assertIn(label, shell)

    def test_v6_is_the_first_layer_on_all_research_topics(self):
        legacy = (WEB / "visual-first-v5.js").read_text(encoding="utf-8")
        v6 = (WEB / "visual-story-v6.js").read_text(encoding="utf-8")
        css = (WEB / "visual-story-v6.css").read_text(encoding="utf-8")
        self.assertIn('js.src="visual-story-v6.js"', legacy)
        self.assertIn('css.href="visual-story-v6.css"', legacy)
        self.assertIn('if(!former&&documentPath!=="corporate-ownership.html")return;', v6)
        self.assertNotIn('function topic(){if(documentPath==="corporate-ownership.html")return;', v6)
        self.assertIn("vs6-topic-mode > header.hero", css,
                      "Original hero must not precede the approved V6 cover")
        self.assertIn("vs6-evidence-status", css)

    def test_evidence_gaps_cannot_disappear_from_presentation(self):
        v6 = (WEB / "visual-story-v6.js").read_text(encoding="utf-8")
        audit = (WEB / "source-audit.html").read_text(encoding="utf-8")
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertIn('function evidenceStatus(){', v6)
        self.assertIn('a.href="source-audit.html"', v6)
        self.assertIn("sitewide-missing-sources-v1.json", audit)
        self.assertGreater(len(catalog["gaps"]), 0)
        self.assertTrue(all(g["requiredJoin"] and g["status"] != "resolved_by_source_verified_data"
                            for g in catalog["gaps"]))

if __name__ == "__main__":
    unittest.main()
