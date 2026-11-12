"""Free browser acceptance checks against the static Power Atlas site.

Run with: pip install playwright && python -m playwright install chromium
          python -m http.server 8765 --directory platform/unified &
          python scripts/qa_browser_smoke.py
Does not send civic correspondence, collect personal data, or invoke paid APIs.
"""
from __future__ import annotations
import os
import re
import json
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

    def test_market_asking_rent_leads_and_hud_is_separate(self):
        # Source-specific market snapshot is verified, static, citywide and NOT
        # substituted with HUD or a historical all-bedroom ACS median.
        root = Path(__file__).resolve().parents[1]
        market = json.loads((root / "data/housing/market-asking-rent-cliffside-park-2026-11.json").read_text())
        self.assertEqual(market["geography"]["relatedZipCode"], "07010")
        self.assertFalse(market["geography"]["zipSpecific"])
        self.assertEqual(market["propertyTypes"]["all"]["bedrooms"]["4"], 5500)
        self.page.route(
            "**/data/housing/market-asking-rent-cliffside-park-2026-11.json",
            lambda route: route.fulfill(status=200, content_type="application/json",
                headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(market)))
        nj = json.loads((root / "data/housing/bedroom-rents/NJ.json").read_text())
        hud = {k: nj[k] for k in ("state", "fy", "areas")}
        hud["zips"] = {"07010": nj["zips"]["07010"]}
        self.page.route(
            "**/data/housing/bedroom-rents/NJ.json",
            lambda route: route.fulfill(status=200, content_type="application/json",
                headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(hud)))
        self.visit("/my-life.html")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type=submit]").click()
        tile = self.page.locator(".vs6-zip-tile--housing")
        tile.locator(".vs6-zip-bedroom-cell").first.wait_for(timeout=20000)
        self.assertEqual(tile.locator(".vs6-zip-bedroom-cell").count(), 4)
        displayed = tile.inner_text()
        for number in ["$2,000", "$2,850", "$4,200", "$5,500"]:
            self.assertIn(number, displayed)
        for invalid in ["$1,837", "$2,340", "$3,590", "HUD FY2027"]:
            self.assertNotIn(invalid, displayed)
        self.assertIn("Cliffside Park citywide", displayed)
        self.assertIn("not exact ZIP", displayed)
        self.assertIn("average advertised rents", displayed)
        control = tile.locator("select.vs6-zip-market-select")
        control.select_option("apartment_condo")
        self.assertIn("$3,678", tile.inner_text())
        self.assertIn("$3,200", tile.inner_text())
        control.select_option("townhouse")
        self.assertIn("Not reported", tile.inner_text())
        self.assertIn("$5,200", tile.inner_text())
        control.select_option("all")
        # The HUD program figures are in their separate lower panel.
        hud_panel = self.page.locator("#pa-hud-safmr")
        self.assertTrue(hud_panel.is_visible())
        self.assertIn("4 bedrooms", hud_panel.inner_text())
        self.assertIn("not current apartment listings", hud_panel.inner_text())
        self.assertIn("$3,590", hud_panel.inner_text())
        self.assert_no_horizontal_overflow()
        tile.scroll_into_view_if_needed()
        self.page.screenshot(path=str(REPORTS / "asking-rent-vs-hud-mobile.png"), full_page=False)

    def test_market_not_inferred_for_unverified_zip(self):
        self.visit("/my-life.html")
        tile = self.page.locator(".vs6-zip-tile--housing")
        tile.wait_for(state="attached", timeout=15000)
        # Wait for both dynamic listeners, not only the initial CSS state.
        self.page.wait_for_function(
            "() => !!document.querySelector('.vs6-zip-market-select')", timeout=15000)
        self.page.evaluate("""() => window.dispatchEvent(new CustomEvent(
            'poweratlas:zip-visual-context',
            {detail:{zip:'10001',place:'New York',status:'loading',metrics:[]}}))""")
        self.page.wait_for_function(
            "() => !!document.querySelector('.vs6-zip-tile--housing .vs6-zip-compare')?.textContent.includes('No verified, recent asking-rent figures')",
            timeout=12000)
        self.assertIn("HUD values are not substituted", tile.inner_text())
        self.assertEqual(tile.locator(".vs6-zip-bedroom-cell").count(), 0)
        self.assert_no_horizontal_overflow()

    def test_local_basic_needs_gap_not_mistaken_for_poverty_eligibility(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/"data/affordability/bergen-basic-needs-2026.json").read_text())
        self.page.route("**/data/affordability/bergen-basic-needs-2026.json",
            lambda route: route.fulfill(status=200,content_type="application/json",
                headers={"Access-Control-Allow-Origin":"*"},body=json.dumps(data)))
        self.visit("/my-life.html")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type=submit]").click()
        panel=self.page.locator("#pa-basic-needs")
        panel.get_by_text("Above poverty. Still short.").wait_for(timeout=15000)
        self.assertTrue(panel.is_visible())
        self.assertIn("$27,320",panel.inner_text())
        self.assertIn("$95,330",panel.inner_text())
        self.assertIn("3.49×",panel.inner_text())
        self.assertIn("county",panel.inner_text().lower())
        control=self.page.locator("#pa-basic-family")
        control.select_option("one-adult-0")
        self.assertIn("$15,960",panel.inner_text())
        self.assertIn("$59,784",panel.inner_text())
        control.select_option("two-adults-both-working-1")
        self.assertIn("$120,077",panel.inner_text())
        control.select_option("two-adults-one-worker-1")
        disclosure=panel.locator("details.pa-basic-expense-detail")
        disclosure.locator("summary").click()
        self.assertIn("$29,764",disclosure.inner_text())
        self.assertIn("$0",disclosure.inner_text())
        self.assert_no_horizontal_overflow()

    def test_unknown_zip_shows_no_inferred_local_living_wage(self):
        self.visit("/my-life.html")
        panel=self.page.locator("#pa-basic-needs")
        panel.wait_for(state="attached",timeout=12000)
        self.page.evaluate("""() => window.dispatchEvent(new CustomEvent(
            'poweratlas:zip-visual-context',
            {detail:{zip:'10001',place:'New York',status:'ready',metrics:[]}}))""")
        panel.get_by_text("No verified local basic-needs model is connected for this ZIP yet.",exact=False).wait_for(timeout=10000)
        self.assertTrue(panel.locator("#pa-basic-family").is_disabled())
        self.assertNotIn("$95,330",panel.inner_text())
        self.assert_no_horizontal_overflow()

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


    def test_v6_editorial_covers_match_on_mobile_and_desktop(self):
        """Visual contract: page-specific stories may vary, outer V6 shell may not."""
        covers = {
            "/dark-money.html": ("main > .vs6-topic", "main > .vs6-topic > h1"),
            "/market-power.html": ("main > .vs6-topic", "main > .vs6-topic > h1"),
            "/consumer-practices.html": ("main > .vs6-topic", "main > .vs6-topic > h1"),
            "/take-action.html": (".ta-hero", ".ta-hero h1"),
        }
        for width, height in ((390, 844), (1440, 900)):
            self.page.set_viewport_size({"width": width, "height": height})
            for path, (cover_selector, headline_selector) in covers.items():
                with self.subTest(path=path, width=width):
                    self.visit(path)
                    cover = self.page.locator(cover_selector)
                    heading = self.page.locator(headline_selector)
                    self.assertTrue(cover.is_visible(), f"{path}: missing V6 cover")
                    self.assertTrue(heading.is_visible(), f"{path}: missing readable headline")
                    appearance = cover.evaluate("""node => ({
                        background: getComputedStyle(node).backgroundColor,
                        width: node.getBoundingClientRect().width,
                        font: parseFloat(getComputedStyle(node.querySelector('h1')).fontSize)
                    })""")
                    self.assertEqual(appearance["background"], "rgb(250, 246, 237)",
                        f"{path}: competing theme instead of canonical V6 cream")
                    self.assertLessEqual(appearance["width"], 1192,
                        f"{path}: cover exceeds canonical maximum width")
                    self.assertGreaterEqual(appearance["font"], 38,
                        f"{path}: headline too small to work as the leading graphic")
                    self.assertLessEqual(appearance["font"], 76,
                        f"{path}: headline exceeds canonical type scale")
                    self.assertEqual(self.page.locator("#pa-global-header").count(), 1)
                    self.assert_no_horizontal_overflow()
                    name = path.strip("/").replace(".html", "")
                    self.page.screenshot(path=str(REPORTS / f"v6-{name}-{width}.png"),
                                         full_page=False)

    def test_consumer_watch_evidence_is_reachable_after_explore(self):
        self.visit("/consumer-practices.html")
        cta = self.page.locator("main > .vs6-topic .vs6-expand")
        self.assertTrue(cta.is_visible())
        self.assertEqual(cta.get_attribute("aria-expanded"), "false")
        cta.click()
        self.assertEqual(cta.get_attribute("aria-expanded"), "true")
        self.assertIn("vs6-topic-expanded", self.page.locator("body").get_attribute("class") or "")
        chapters = self.page.locator("main > .pa5-explorer .pa5-chapter-card")
        self.assertGreater(chapters.count(), 0, "Consumer Watch evidence has no discoverable chapters")
        self.assertTrue(self.page.locator("main > .pa5-explorer").is_visible())
        self.assert_no_horizontal_overflow()


    def test_zip_remains_between_pages_return_visits_and_can_be_cleared(self):
        """One saved ZIP; no ZIP query params, auto-scroll or civic request on revisit."""
        self.visit("/my-life.html")
        self.page.wait_for_function("() => !!window.PowerAtlasZIP?.get", timeout=15000)
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type='submit']").click()
        self.page.wait_for_function("() => window.PowerAtlasZIP?.get() === '07010'")
        self.assertIn("07010", self.page.locator("#zipInput").input_value())
        self.assertNotIn("07010", self.page.url)

        self.visit("/take-action.html")
        self.page.wait_for_function("() => document.getElementById('zip')?.value === '07010'")
        self.assertEqual(self.page.locator("#member-results").inner_text().strip(), "",
                         "Reopening Take Action must not contact third parties automatically")
        self.assertNotIn("07010", self.page.url)

        self.visit("/cost-gap.html")
        self.page.wait_for_function("() => document.getElementById('cg-zip-a')?.value === '07010'")
        self.assertNotIn("07010", self.page.url)

        self.visit("/my-life.html")
        self.page.wait_for_function("() => document.getElementById('zipInput')?.value === '07010'")
        self.assertTrue(self.page.locator("#clearSavedZIP").is_visible())
        self.assertNotIn("07010", self.page.url)
        self.page.locator("#clearSavedZIP").click()
        self.page.wait_for_function("() => window.PowerAtlasZIP?.get() === null", timeout=15000)
        self.assertEqual(self.page.locator("#zipInput").input_value(), "")
        self.assertFalse(self.page.locator("#clearSavedZIP").is_visible())
        self.assert_no_horizontal_overflow()

    def test_changing_saved_zip_updates_another_page(self):
        self.visit("/my-life.html")
        self.page.wait_for_function("() => !!window.PowerAtlasZIP?.get")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type='submit']").click()
        self.page.wait_for_function("() => window.PowerAtlasZIP?.get() === '07010'")
        self.page.locator("#zipInput").fill("10001")
        self.page.locator("#zipForm button[type='submit']").click()
        self.page.wait_for_function("() => window.PowerAtlasZIP?.get() === '10001'")
        self.visit("/take-action.html")
        self.page.wait_for_function("() => document.getElementById('zip')?.value === '10001'")
        self.assertNotIn("10001", self.page.url)



if __name__ == "__main__":
    unittest.main(verbosity=2)
