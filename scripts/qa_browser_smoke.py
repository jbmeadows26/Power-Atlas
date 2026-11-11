"""Free browser acceptance checks against the static Power Atlas site.

Run with: pip install playwright && python -m playwright install chromium
          python -m http.server 8765 --directory platform/unified &
          python scripts/qa_browser_smoke.py
Does not send civic correspondence, collect personal data, or invoke paid APIs.
"""
from __future__ import annotations
import os
import re
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get("POWER_ATLAS_QA_URL", "http://127.0.0.1:8765").rstrip("/")
REPORTS = Path(os.environ.get("POWER_ATLAS_QA_REPORT_DIR", "/tmp/power-atlas-qa"))
REPORTS.mkdir(parents=True, exist_ok=True)


class BrowserJourneyQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.play = sync_playwright().start()
        cls.browser = cls.play.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.play.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        self.page = self.context.new_page()
        self.page.on("pageerror", lambda exc: print("Browser page error:", exc))

    def tearDown(self):
        self.context.close()

    def visit(self, path):
        self.page.goto(BASE + path, wait_until="domcontentloaded", timeout=40000)
        self.page.wait_for_function("document.documentElement.dataset.vs6 === 'active'", timeout=22000)
        self.page.wait_for_timeout(250)

    def assert_no_horizontal_overflow(self):
        self.assertTrue(self.page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth + 3"),
            "Horizontal overflow at 390px on " + self.page.url)

    def test_root_is_zip_first_and_no_duplicate_hero(self):
        self.visit("/")
        self.assertTrue(self.page.url.split("?")[0].endswith("/my-life.html"), self.page.url)
        self.assertTrue(self.page.locator("#where #zipInput").is_visible())
        self.assertTrue(self.page.locator("#what h2").inner_text().strip() == "What matters most right now?")
        self.assertEqual(self.page.locator(".hero:visible").count(), 0,
                         "Legacy intro is still visibly competing with the approved V6 hero")
        self.assert_no_horizontal_overflow()
        self.page.screenshot(path=str(REPORTS / "zip-first-mobile.png"), full_page=False)

    def test_navigation_is_canonical_and_action_is_direct(self):
        self.visit("/my-life.html")
        nav = self.page.locator("#pa-global-header .pa-global-links a")
        self.assertEqual(nav.count(), 6)
        labels = [x.strip() for x in self.page.locator("#pa-global-header .pa-short").all_text_contents()]
        self.assertEqual(labels, ["Start Here", "Issues", "Costs", "The Why", "Actions", "Research"])
        action = self.page.locator("#pa-global-header a[data-pa-nav='action']")
        self.assertTrue(action.get_attribute("href").endswith("take-action.html"))
        self.assert_no_horizontal_overflow()

    def test_all_16_research_threads_are_discoverable(self):
        self.visit("/my-life.html")
        section = self.page.locator("#pa-coverage-discovery")
        self.assertEqual(section.count(), 1)
        self.assertEqual(section.locator(".pa-coverage-card").count(), 16)
        summary = section.locator("summary")
        self.assertTrue(summary.is_visible(), "The evidence directory is hidden behind a legacy chapter")
        summary.click(timeout=10000)
        self.assertTrue(section.locator("details.pa-coverage-more").get_attribute("open") is not None)
        for slug in ["dark-money.html", "business-influence.html", "market-power.html",
                     "wealth-advantage.html", "take-action.html", "source-audit.html"]:
            self.assertTrue(section.locator(f'a[href="{slug}"]').count() >= 1, slug)
        self.assert_no_horizontal_overflow()

    def test_zip_preserves_first_section(self):
        self.visit("/my-life.html")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type=submit]").click()
        self.assertEqual(self.page.locator("#zipInput").input_value(), "07010")
        # This is a journey regression, not a requirement that third-party ACS APIs be online.
        self.assertTrue(self.page.evaluate(
            "() => !!(document.getElementById('where').compareDocumentPosition("
            "document.getElementById('what')) & Node.DOCUMENT_POSITION_FOLLOWING)"))

    def test_take_action_chamber_buttons_and_mobile_layout(self):
        self.visit("/take-action.html")
        house = self.page.locator('[data-chamber="house"]')
        senate = self.page.locator('[data-chamber="senate"]')
        self.assertEqual(house.count(), 1)
        self.assertEqual(senate.count(), 1)
        house.click()
        self.assertEqual(house.get_attribute("aria-pressed"), "true")
        senate.click()
        self.assertEqual(senate.get_attribute("aria-pressed"), "true")
        self.assert_no_horizontal_overflow()

    def test_market_power_and_consumer_watch_have_v6_and_mobile_fit(self):
        for path in ["/market-power.html", "/consumer-practices.html", "/dark-money.html"]:
            with self.subTest(page=path):
                self.visit(path)
                self.assertTrue(self.page.locator("#pa-global-header").is_visible())
                self.assert_no_horizontal_overflow()


if __name__ == "__main__":
    unittest.main(verbosity=2)
