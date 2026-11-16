"""Power Atlas six-link community-first navigation regression checks."""
from pathlib import Path
import re
import unittest

UI = Path(__file__).resolve().parents[1] / "platform" / "unified"
PAGES = (
    "my-life.html", "compare.html", "dark-money.html",
    "reform-lab.html", "business-candidates.html", "donor-intelligence.html",
    "money-sources.html", "election-2026.html", "business-influence.html",
    "election-money.html", "navatek.html", "investigations.html",
    "consumer-practices.html", "telecom-promotions.html",
    "service-accountability.html", "corporate-ownership.html",
    "source-audit.html",
)
EXPECTED = (
    ("place", "my-life.html#where"),
    ("issues", "my-life.html#what"),
    ("why", "my-life.html#why"),
    ("action", "my-life.html#how"),
    ("research", "index.html"),
    ("consumer", "consumer-practices.html"),
)


class GlobalNavigationTests(unittest.TestCase):
    def test_same_six_links_on_all_primary_pages(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = (UI / name).read_text(encoding="utf-8")
                self.assertEqual(text.count('id="pa-global-header"'), 1)
                self.assertIn('href="global-navigation.css"', text)
                nav = re.search(r'<div id="pa-global-header"[\s\S]*?</nav></div></div>', text)
                self.assertIsNotNone(nav)
                links = re.findall(
                    r'<a href="([^"]+)" data-pa-nav="([^"]+)"[^>]*>',
                    nav.group(0),
                )
                self.assertEqual([(key, href) for href, key in links], list(EXPECTED))
                self.assertEqual(len(re.findall(r'data-pa-nav=', nav.group(0))), 6)
                self.assertIn('<span class="pa-short">', nav.group(0))
                self.assertIn('<span class="pa-long">', nav.group(0))
                self.assertNotIn('data-pa-nav="overview"', nav.group(0))

    def test_destinations_and_anchors(self):
        life = (UI / "my-life.html").read_text(encoding="utf-8")
        for key, href in EXPECTED:
            target, _, fragment = href.partition("#")
            self.assertTrue((UI / target).is_file())
            if fragment:
                self.assertIn('id="' + fragment + '"', life)
        self.assertIn("pageSections.has(hash)", life)
        self.assertIn("markPrimaryNav", life)
        self.assertIn('aria-current","location"', life)
        self.assertIn("hashchange", life)
        self.assertIn("window.history.replaceState", life)
        self.assertIn("power-atlas:visitor-zip:v1", life)
        self.assertIn("savedHomeZIP", life)
        self.assertIn('id="clearSavedZIP"', life)

    def test_dashboard_is_the_canonical_home_and_research_remains_accessible(self):
        home = (UI / "index.html").read_text(encoding="utf-8")
        dashboard = (UI / "dashboard.html").read_text(encoding="utf-8")
        archive = (UI / "research-archive.html").read_text(encoding="utf-8")
        self.assertIn('location.replace("dashboard.html"', home)
        self.assertIn('href="dashboard.html"', home)
        for anchor in ('id="costs"', 'id="investigations"', 'id="topics"',
                       'id="sources"', 'id="action"'):
            self.assertIn(anchor, dashboard)
        self.assertIn('href="research-archive.html"', dashboard)
        self.assertIn('href="take-action.html#find"', dashboard)
        self.assertIn("research", archive.lower())
        self.assertIn("authenticity", archive.lower())
        self.assertIn('href:"consumer-practices.html"', (UI / "dashboard.js").read_text(encoding="utf-8"))

    def test_responsive_shared_navigation_and_accessibility(self):
        css = (UI / "global-navigation.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:repeat(6,minmax(0,1fr))", css)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", css)
        self.assertIn("Consumer Watch", (UI / "consumer-practices.html").read_text(encoding="utf-8"))
        self.assertIn("min-height:44px", css)
        self.assertIn("max-width:830px", css)
        self.assertIn("max-width:400px", css)
        self.assertIn(".pa-short{display:inline}", css)
        self.assertIn("a[aria-current]", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("pa-research-drawer", css)
        self.assertIn("top:0;z-index:9999", css)


if __name__ == "__main__":
    unittest.main()
