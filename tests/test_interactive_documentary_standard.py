"""Regression checks for the approved visual documentary pilot and member email testing.

Static safety checks are not substitutes for browser interaction and email-transport QA.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "platform" / "unified"


class InteractiveDocumentaryStandardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = (SITE / "why-costs-more.html").read_text(encoding="utf-8")
        cls.action = (SITE / "take-action.html").read_text(encoding="utf-8")
        cls.action_js = (SITE / "take-action.js").read_text(encoding="utf-8")
        cls.tester = (SITE / "contact-tester.html").read_text(encoding="utf-8")
        cls.design = (ROOT / "docs/design-system/interactive-documentary-standard.md").read_text(encoding="utf-8")

    def test_approved_story_standard_and_global_shell_reference(self):
        shell = (ROOT / "docs/design-system/single-shell-contract.md").read_text(encoding="utf-8")
        for item in ("interactive visual documentary", "Interaction must reveal knowledge",
                     "Member-contact exception", "verified observation",
                     "reduced-motion", "take action"):
            with self.subTest(item=item):
                self.assertIn(item.lower(), self.design.lower())
        self.assertIn("interactive-documentary-standard.md", shell)

    def test_first_story_interactions_are_real_controls(self):
        for item in ('id="yearRange"', 'range.addEventListener("input",updateYear)',
                     'data-topic="housing"', 'data-topic="food"', 'data-topic="phone"',
                     'data-lever="government"', 'data-lever="business"',
                     'network.appendChild(b)', 'id="detailBody"',
                     'id="leverBody"', 'prefers-reduced-motion:reduce'):
            with self.subTest(item=item):
                self.assertIn(item, self.story)
        cpi = {int(y): float(v) for y, v in re.findall(r"(20\d{2}):(\d{3}\.\d{3})", self.story)}
        self.assertEqual(cpi[2020], 258.811)
        self.assertEqual(cpi[2025], 321.943)
        self.assertAlmostEqual(100 * cpi[2025] / cpi[2020], 124.39, places=2)

    def test_member_letter_is_email_ready_but_test_only(self):
        for item in ('id="email-subject"', 'id="message-preview"',
                     'id="email-recipient"', 'id="write-member"',
                     'href="contact-tester.html"', 'id="official-member"',
                     'id="copy-message"', '500 characters'):
            with self.subTest(item=item):
                self.assertIn(item, self.action)
        self.assertIn("function makeEmail()", self.action_js)
        self.assertIn("subject:", self.action_js)
        self.assertIn("body.slice(0,500)", self.action_js)
        self.assertIn('const payload={', self.action_js)
        self.assertIn('sessionStorage.setItem("power-atlas:member-email-test:v1"', self.action_js)
        self.assertNotIn('fetch("contact-tester.html"', self.action_js)
        self.assertNotIn('mailto:', self.action_js)
        self.assertNotIn('navigator.sendBeacon(', self.action_js)

    def test_tester_is_an_honest_non_sending_preview(self):
        for marker in ("Nothing has been sent.", "Preview only",
                       'id="preview-subject"', 'id="preview-body"',
                       "sessionStorage.getItem(KEY)", "safeOfficeLink",
                       'id="copy-email"', 'id="clear-test"',
                       "No outbound email", "not a connected"):
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.tester.lower())
        for blocked in ("send_message(", "sendEmail(", "POST /api/send", "mailto:"):
            self.assertNotIn(blocked, self.tester)


if __name__ == "__main__":
    unittest.main()
