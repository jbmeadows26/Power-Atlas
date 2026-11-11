"""Regression checks for the location-to-category reading flow.

The category choice must reveal the category-specific Step 2 content before
allowing the reader to advance to the deeper Step 3 evidence.
"""
from pathlib import Path
import unittest

PAGE = Path(__file__).resolve().parents[1] / "platform" / "unified" / "my-life.html"


class LocationCategoryScrollTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_location_submission_shows_zip_visual_before_category_choices(self):
        # ZIP submission now anchors the visual summary instead of skipping it.
        self.assertIn('const visualOverview=document.querySelector("main > .vs6-topic");', self.html)
        self.assertIn('scrollToSection("where","where");', self.html)
        self.assertNotIn('scrollToSection("what","what");', self.html)
        self.assertIn('id="step2Place"', self.html)
        self.assertIn('Looking up ZIP "+zip+', self.html)

    def test_category_selection_shows_step_two_explainer_not_step_three(self):
        self.assertIn('id="issueResult"', self.html)
        self.assertIn('id="issueQuestion" tabindex="-1"', self.html)
        self.assertIn('if(scroll){scrollToSection("issueResult","what");', self.html)
        self.assertNotIn('if(scroll)$("why").scrollIntoView', self.html)
        self.assertIn('markPrimaryNav(scroll?"what":', self.html)

    def test_step_three_is_an_explicit_accessible_next_action(self):
        self.assertIn('id="continueToWhy" href="#why"', self.html)
        self.assertIn('Next: Follow the evidence', self.html)
        self.assertIn('prefers-reduced-motion: reduce', self.html)
        self.assertIn('focus({preventScroll:true})', self.html)


if __name__ == "__main__":
    unittest.main()
