"""Acceptance gates for the AI Crash interactive documentary and its QA fixes."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "platform" / "unified"
STORY = ROOT / "ai-crash.html"
BUG_CLIENT = ROOT / "bug-report.js"
BUG_API = ROOT / "api" / "bug-report.js"


class AICrashStoryQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = STORY.read_text(encoding="utf-8")

    def test_all_chapter_links_have_real_destinations(self):
        ids = re.findall(r'\bid="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)), "Duplicate IDs impair navigation and controls")
        anchors = re.findall(r'\bhref="#([^"]+)"', self.html)
        self.assertTrue(anchors)
        self.assertFalse(set(anchors) - set(ids), "Unresolved in-page destinations")
        chapterbar = re.search(r'<nav class="chapterbar"[^>]*>(.*?)</nav>', self.html, re.S)
        self.assertIsNotNone(chapterbar)
        for index, anchor in enumerate(("bet", "connections", "spark", "simulate",
                                        "home", "who", "watch", "evidence"), 1):
            expected = rf'<a href="#{anchor}">{index:02d} · '
            self.assertIn(expected, chapterbar.group(1))

    def test_all_interactive_controls_are_labeled(self):
        self.assertEqual(5, len(re.findall(r'<button[^>]+data-node="', self.html)))
        self.assertEqual(4, len(re.findall(r'<button[^>]+data-spark="', self.html)))
        self.assertEqual(5, len(re.findall(r'<button[^>]+data-stage="', self.html)))
        self.assertEqual(3, len(re.findall(r'<button[^>]+data-severity="', self.html)))
        for field in ("balance", "exposure", "decline"):
            self.assertIn(f'<label for="{field}">', self.html)
            self.assertIn(f'id="{field}"', self.html)

    def test_network_detail_is_legible_in_dark_chapter(self):
        # Rules must explicitly override the dark parent's inherited white text.
        self.assertIn(".network-detail,.network-detail .why,.network-detail h3{color:#17323c}", self.html)
        self.assertIn(".network-detail .label{color:#20695e}", self.html)
        self.assertIn(".network-detail .next{color:#344d52}", self.html)
        self.assertIn(".storyclock .tiny,.dark .tiny{color:#cadbd9}", self.html)
        self.assertIn(".numberproof{color:#4c656b}", self.html)
        self.assertIn("08 / EVIDENCE NOTEBOOK", self.html)

    def test_mobile_navigation_remains_available(self):
        self.assertIn('id="mobileMenuToggle"', self.html)
        self.assertIn('aria-controls="mobileNav"', self.html)
        self.assertIn('aria-expanded="false"', self.html)
        self.assertIn('id="mobileNav"', self.html)
        self.assertIn('.mobile-nav[hidden]{display:none!important}', self.html)
        self.assertIn('menuButton.addEventListener("click"', self.html)
        self.assertIn('event.key==="Escape"', self.html)

    def test_preview_overlay_does_not_cover_mobile_controls(self):
        self.assertIn("@media(max-width:550px){vercel-live-feedback{display:none!important}}",
                      self.html)

    def test_bug_reports_are_shipped_with_preview(self):
        self.assertIn('<script src="bug-report.js" defer></script>', self.html)
        self.assertTrue(BUG_CLIENT.exists())
        self.assertTrue(BUG_API.exists())
        self.assertIn("fetch('/api/bug-report'", BUG_CLIENT.read_text(encoding="utf-8"))
        self.assertIn("POSTHOG_PUBLIC_TOKEN", BUG_API.read_text(encoding="utf-8"))
        self.assertIn('id="mobileReportTrigger"', self.html)
        self.assertIn('position:static!important', BUG_CLIENT.read_text(encoding="utf-8"))

    def test_evidence_protects_readers_from_false_predictions(self):
        for phrase in ("$300B", "$650B", "$1.4T", "not a forecast",
                       "not probabilities", "not investment advice",
                       "https://www.imf.org", "https://www.bankofengland.co.uk"):
            self.assertIn(phrase.lower(), self.html.lower())


if __name__ == "__main__":
    unittest.main()
