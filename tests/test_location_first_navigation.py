"""Regression tests for the location-first onboarding and shared visitor journey."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "platform" / "unified"
RESEARCH = ROOT / "site"


class LocationFirstNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (UNIFIED / "my-life.html").read_text(encoding="utf-8")
        cls.navigation = (UNIFIED / "atlas-visual-system.js").read_text(encoding="utf-8")
        cls.css = (UNIFIED / "global-navigation.css").read_text(encoding="utf-8")

    def test_zip_entry_is_first_real_step_before_hero_and_issues(self):
        page = self.page
        self.assertLess(page.index('id="where"'), page.index('<div class="hero">'))
        self.assertLess(page.index('id="zipForm"'), page.index('id="what"'))
        for marker in ('id="zipInput"', 'id="placeName"', 'id="placeStatus"', 'id="zipPrivacy"'):
            self.assertEqual(page.count(marker), 1, marker)
        self.assertIn('aria-describedby="zipPrivacy"', page)
        self.assertIn('autocomplete="postal-code"', page)
        self.assertIn('inputmode="numeric"', page)

    def test_privacy_text_is_brief_with_full_details_available(self):
        self.assertIn('class="pa-zip-privacy"', self.page)
        self.assertIn('<details class="pa-zip-disclosure">', self.page)
        self.assertIn("Zippopotam.us", self.page)
        self.assertIn("Census Reporter", self.page)
        self.assertIn("does not store", self.page)
        self.assertNotIn("localStorage", self.page)

    def test_six_menu_items_appear_in_customer_journey_order(self):
        js = self.navigation
        keys = ['["place","my-life.html#where","Start Here"]',
                '["issues","my-life.html#what","Issues"]',
                '["costs","my-life.html#benchmarkStory","Costs"]',
                '["why","my-life.html#why","The Why"]',
                '["action","take-action.html","Actions"]',
                '["research","index.html","Research"]']
        positions = [js.index(key) for key in keys]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('link.dataset.paNav==="consumer"?"costs"', js)
        self.assertIn("nav.append(link)", js)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", self.css)

    def test_costs_points_to_actual_cost_benchmarks(self):
        self.assertIn('id="benchmarkStory"', self.page)
        self.assertIn('benchmarkStory:"costs"', self.page)
        self.assertIn('href="consumer-practices.html"', self.page)

    def test_active_menu_follows_scroll_and_initial_screen(self):
        page = self.page
        for token in ("syncPrimaryNavWithScroll", "schedulePrimaryNavSync",
                      'window.addEventListener("scroll"', 'window.addEventListener("resize"',
                      '"where","what","benchmarkStory","why","how"',
                      'location.hash?"what":"where"'):
            self.assertIn(token, page)
        self.assertIn("Boolean(hash)&&!pageSections.has(hash)", page)

    def test_shared_visual_js_remains_in_sync(self):
        self.assertEqual((UNIFIED / "atlas-visual-system.js").read_bytes(),
                         (RESEARCH / "atlas-visual-system.js").read_bytes())


if __name__ == "__main__":
    unittest.main()
