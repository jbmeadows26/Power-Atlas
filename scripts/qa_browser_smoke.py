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

    def test_all_20_research_threads_are_discoverable(self):
        self.visit("/my-life.html")
        section = self.page.locator("#pa-coverage-discovery")
        self.assertEqual(section.count(), 1)
        self.assertEqual(section.locator(".pa-coverage-card").count(), 20)
        self.assertTrue(self.page.locator("#what .section-head h2").is_visible(),
                        "What matters most heading must stay visible above the investigation cards")
        self.assertTrue(section.locator(".pa-coverage-card").first.is_visible(),
                        "Featured source-backed stories should be visible on the first V6 screen")
        summary = section.locator("summary")
        self.assertTrue(summary.is_visible(), "The evidence directory is hidden behind a legacy chapter")
        summary.click(timeout=10000)
        self.assertTrue(section.locator("details.pa-coverage-more").get_attribute("open") is not None)
        for slug in ["dark-money.html", "business-influence.html", "market-power.html",
                     "wealth-advantage.html", "take-action.html", "source-audit.html",
                     "voting-access.html", "economic-fragility.html", "research-archive.html"]:
            self.assertTrue(section.locator(f'a[href="{slug}"]').count() >= 1, slug)
        self.assert_no_horizontal_overflow()
        self.assertEqual(section.locator(".pa-coverage-jump").count(), 0,
                         "Issue invitations belong only in the dedicated issue section")
        self.assertFalse(summary.is_visible(),
                         "Expanded investigation list should hide the now-redundant summary")
        section.locator(".pa-coverage-collapse").click()
        self.assertTrue(summary.is_visible())
        self.page.wait_for_function(
            "() => document.querySelectorAll('#issueGrid > button.issue-card').length === 9"
            " && document.querySelectorAll('#issueGrid > details.pa-social-card').length === 21",
            timeout=20000)
        self.assertTrue(self.page.locator("#issueGrid").is_visible(),
                        "The 30 issue cards must continue immediately below investigations")
        self.assertTrue(self.page.locator(".pa-coverage-issues-lead").is_visible())
        self.assertTrue(self.page.evaluate(
            "() => document.getElementById('issueGrid').getBoundingClientRect().top"
            " >= document.getElementById('pa-coverage-discovery').getBoundingClientRect().top"),
            "Issues must follow investigations, not precede them")
        # Clicking a primary life topic must still reveal its full evidence panel.
        self.page.locator('#issueGrid button[data-topic="housing"]').click()
        self.assertTrue(self.page.locator("#issueResult").is_visible(),
                        "Selecting a life issue must not lead to hidden legacy research")

    def test_zip_preserves_first_section(self):
        self.visit("/my-life.html")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type=submit]").click()
        self.assertEqual(self.page.locator("#zipInput").input_value(), "07010")
        # This is a journey regression, not a requirement that third-party ACS APIs be online.
        self.assertTrue(self.page.evaluate(
            "() => !!(document.getElementById('where').compareDocumentPosition("
            "document.getElementById('what')) & Node.DOCUMENT_POSITION_FOLLOWING)"))

    def test_mobile_percentage_charts_use_shared_zero_axes_and_direct_labels(self):
        """A 20.4% share must not appear as an unqualified 100%-width bar."""
        self.visit("/my-life.html")
        # Synthetic QA fixtures only; never displayed as public research data.
        self.page.evaluate("""() => {
            window.dispatchEvent(new CustomEvent('poweratlas:zip-visual-context', {detail: {
                zip: '07010', place: 'QA fixture', status: 'ready',
                survey: 'U.S. Census ACS 2020–2024 5-year',
                metrics: [
                    {key:'transport', localValue:20.4, usValue:3.2,
                     localText:'20.4%', usText:'3.2%', format:'share'},
                    {key:'groceries', localValue:7.8, usValue:12.1,
                     localText:'7.8%', usText:'12.1%', format:'share'},
                    {key:'health', localValue:7.7, usValue:8.4,
                     localText:'7.7%', usText:'8.4%', format:'share'}
                ]
            }}));
        }""")
        transport = self.page.locator(".vs6-zip-tile").filter(
            has=self.page.locator(".vs6-zip-tile-label", has_text="TRANSPORT"))
        grocery = self.page.locator(".vs6-zip-tile").filter(
            has=self.page.locator(".vs6-zip-tile-label", has_text="FOOD"))
        health = self.page.locator(".vs6-zip-tile").filter(
            has=self.page.locator(".vs6-zip-tile-label", has_text="HEALTH"))
        self.assertEqual(transport.locator(".vs6-zip-comparison-value").all_text_contents(),
                         ["20.4%", "3.2%"])
        self.assertFalse(transport.locator(".vs6-zip-tile-value").is_visible(),
                         "Directly labeled bars replace the duplicate standalone ZIP percentage")
        self.assertEqual(transport.locator(".vs6-zip-axis-ticks span").all_text_contents(),
                         ["0%", "12.5%", "25%"])
        self.assertAlmostEqual(transport.locator(".vs6-zip-fill").first.evaluate(
            "node => parseFloat(node.style.width)"), 81.6, places=1,
            msg="The local bar must not normalize to the 20.4% observed maximum")
        self.assertAlmostEqual(transport.locator(".vs6-zip-fill--us").evaluate(
            "node => parseFloat(node.style.width)"), 12.8, places=1)
        self.assertIn("17.2 percentage points above U.S.", transport.inner_text())
        self.assertIn("same 0%–25% axis", transport.locator(".vs6-zip-comparison").get_attribute("aria-label"))
        self.assertEqual(grocery.locator(".vs6-zip-axis-ticks span").all_text_contents(),
                         ["0%", "7.5%", "15%"])
        self.assertEqual(health.locator(".vs6-zip-axis-ticks span").all_text_contents(),
                         ["0%", "5%", "10%"])
        self.assertIn("4.3 percentage points below U.S.", grocery.inner_text())
        # Each comparison receives the full phone width instead of two cramped
        # adjacent mini-bars that are difficult to read or tap.
        tx, gx = transport.bounding_box(), grocery.bounding_box()
        self.assertLess(abs(tx["x"] - gx["x"]), 5)
        self.assertGreater(gx["y"], tx["y"])
        self.assertGreater(transport.locator(".vs6-zip-track").first.bounding_box()["width"], 140)
        self.assert_no_horizontal_overflow()

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

    def test_ai_ecosystem_nodes_reveal_source_backed_examples(self):
        self.visit("/ai-crash.html")
        for node, title in (("lenders", "CoreWeave"), ("builders", "47 projects"),
                            ("suppliers", "Grid connection"), ("models", "Anthropic"),
                            ("buyers", "Adoption ahead")):
            with self.subTest(node=node):
                self.page.locator('[data-node="' + node + '"]').click()
                self.assertTrue(self.page.locator("#nodeCaseList .node-case").count() >= 2)
                self.assertIn(title, self.page.locator("#nodeCaseList").inner_text())
                self.assertEqual(self.page.locator("#nodeCaseList a[target='_blank']").count(), 2)
                self.assertIn("Not established", self.page.locator("#nodeSystemGap").inner_text())
        self.assert_no_horizontal_overflow()

    def test_market_power_and_consumer_watch_have_v6_and_mobile_fit(self):
        for path in ["/market-power.html", "/consumer-practices.html", "/dark-money.html"]:
            with self.subTest(page=path):
                self.visit(path)
                self.assertTrue(self.page.locator("#pa-global-header").is_visible())
                self.assert_no_horizontal_overflow()


    def test_all_canonical_routes_have_a_single_visible_v6_entry(self):
        """Accept approved visual-documentary chapters while rejecting legacy-only shells."""
        pages = sorted(p.name for p in (Path(__file__).resolve().parents[1] / "platform" / "unified").glob("*.html"))
        self.assertGreaterEqual(len(pages), 30)
        for name in pages:
            with self.subTest(page=name):
                self.visit("/" + name)
                header = self.page.locator("#pa-global-header")
                self.assertEqual(header.count(), 1, name + ": missing/duplicate global navigation")
                self.assertTrue(header.is_visible(), name + ": brand not visible")
                entry = self.page.locator(
                    "main > .vs6-topic, main .threadGallery, main .ta-hero, main #vs6-home, main > .story-hero, main > #evidence-stage, main .letter, main > .bank-hero, main > header.hero[data-pa-story-hero]")
                self.assertGreater(entry.count(), 0,
                    name + ": missing an approved V6 or interactive-documentary visual entry")
                self.assertTrue(entry.first.is_visible(), name + ": empty or hidden entry")
                self.assert_no_horizontal_overflow()

    def test_zip_preference_persists_across_routes_and_can_be_cleared(self):
        """Remember locally without a user account, URL parameter or automatic page jump."""
        self.visit("/my-life.html")
        self.assertEqual(self.page.locator("#zipInput").input_value(), "")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type=submit]").click()
        self.assertEqual(self.page.evaluate(
            "() => localStorage.getItem('power-atlas:visitor-zip:v1')"), "07010")
        self.visit("/dark-money.html")
        chip = self.page.locator("#pa-global-header .pa-remembered-zip")
        chip.wait_for(state="visible", timeout=10000)
        self.assertTrue(chip.is_visible())
        self.assertIn("07010", chip.inner_text())
        chip.click()
        self.page.wait_for_url("**/my-life.html#where")
        self.page.wait_for_function(
            "() => document.documentElement.dataset.vs6 === 'active'")
        self.assertEqual(self.page.locator("#zipInput").input_value(), "07010")
        self.assertTrue(self.page.locator("#zipForm").is_visible(),
                        "ZIP chip must open the edit form on the dedicated home section")
        self.assertNotIn("vs6-topic-expanded",
            self.page.locator("body").get_attribute("class") or "",
            "ZIP navigation reopened legacy deep research")
        clear = self.page.locator("#clearSavedZIP")
        self.assertTrue(clear.is_visible())
        clear.click()
        self.page.wait_for_function(
            "() => !localStorage.getItem('power-atlas:visitor-zip:v1') && document.getElementById('zipInput')?.value === ''",
            timeout=16000)
        self.assertEqual(self.page.locator(".pa-remembered-zip").count(), 0)
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
        self.assertFalse(self.page.locator("#where").is_visible(),
                         "A remembered ZIP must collapse the original entry card")
        self.assertFalse(self.page.locator("#clearSavedZIP").is_visible())
        self.assertIn("Change ZIP", self.page.locator(".vs6-zip-link").inner_text())
        self.assertNotIn("07010", self.page.url)
        self.page.locator(".vs6-zip-link").click()
        self.assertTrue(self.page.locator("#where").is_visible())
        self.assertTrue(self.page.locator("#clearSavedZIP").is_visible())
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=20000):
            self.page.locator("#clearSavedZIP").click()
        self.page.wait_for_function("() => !!window.PowerAtlasZIP?.get && window.PowerAtlasZIP.get() === null", timeout=15000)
        self.assertEqual(self.page.locator("#zipInput").input_value(), "")
        self.assertFalse(self.page.locator("#clearSavedZIP").is_visible())
        self.assert_no_horizontal_overflow()

    def test_changing_saved_zip_updates_another_page(self):
        self.visit("/my-life.html")
        self.page.wait_for_function("() => !!window.PowerAtlasZIP?.get")
        self.page.locator("#zipInput").fill("07010")
        self.page.locator("#zipForm button[type='submit']").click()
        self.page.wait_for_function("() => window.PowerAtlasZIP?.get() === '07010'")
        self.assertFalse(self.page.locator("#zipForm").is_visible())
        self.page.locator(".vs6-zip-link").click()
        self.assertTrue(self.page.locator("#zipForm").is_visible())
        self.page.locator("#zipInput").fill("10001")
        self.page.locator("#zipForm button[type='submit']").click()
        self.page.wait_for_function("() => window.PowerAtlasZIP?.get() === '10001'")
        self.visit("/take-action.html")
        self.page.wait_for_function("() => document.getElementById('zip')?.value === '10001'")
        self.assertNotIn("10001", self.page.url)



    def test_deep_linked_evidence_opens_instead_of_generic_cover(self):
        self.visit("/consumer-practices.html?story=amazon")
        self.page.wait_for_function(
            "() => document.getElementById('pcStoryTitle')?.textContent?.toLowerCase().includes('subscription')",
            timeout=25000)
        self.assertIn("vs6-topic-expanded", self.page.locator("body").get_attribute("class") or "")
        self.assertTrue(self.page.locator("#pcStoryTitle").is_visible())
        self.assert_no_horizontal_overflow()

        self.visit("/market-power.html?case=jobs")
        self.page.wait_for_function(
            "() => document.getElementById('caseDetail')?.textContent?.includes('Employer power over wages')",
            timeout=25000)
        self.assertIn("vs6-topic-expanded", self.page.locator("body").get_attribute("class") or "")
        self.assertTrue(self.page.locator("#caseDetail").is_visible())
        self.assert_no_horizontal_overflow()

    def test_corporate_ownership_food_alias_shows_grocery_context(self):
        self.visit("/corporate-ownership.html?issue=food")
        self.page.wait_for_function("() => document.querySelector('#topicFilter button[data-issue=groceries]') !== null", timeout=25000)
        self.assertEqual(
            self.page.locator('#topicFilter button[data-issue="groceries"]').get_attribute("aria-pressed"), "true")
        self.assert_no_horizontal_overflow()

    def test_disclosures_identify_controlled_content_and_navigation_is_consistent(self):
        self.visit("/market-power.html")
        trigger=self.page.locator("main > .vs6-topic .vs6-expand")
        target=trigger.get_attribute("aria-controls")
        self.assertTrue(target, "Evidence expander has no aria-controls")
        self.assertEqual(self.page.locator("#"+target).count(), 1)

        self.visit("/ai-crash.html")
        self.assertEqual(self.page.locator(".story-navlinks a").all_inner_texts(),
                         ["Start Here","Issues","Costs","The Why","Actions","Research"])
        self.assertEqual(self.page.locator("#pa-global-header").count(), 1)

        self.visit("/banking-power.html")
        self.assertEqual(self.page.locator(".pa-global-links a").all_inner_texts(),
                         ["Start Here","Issues","Costs","The Why","Actions","Research"])
        self.assert_no_horizontal_overflow()


if __name__ == "__main__":
    unittest.main(verbosity=2)
