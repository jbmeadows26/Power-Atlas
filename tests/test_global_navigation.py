"""Power Atlas five-link community-first navigation regression checks."""
from pathlib import Path
import re
import unittest

UI = Path(__file__).resolve().parents[1] / "platform" / "unified"
PAGES = (
    "index.html", "my-life.html", "compare.html", "dark-money.html",
    "reform-lab.html", "business-candidates.html", "donor-intelligence.html",
    "money-sources.html", "election-2026.html", "business-influence.html",
    "election-money.html", "navatek.html", "investigations.html",
)
EXPECTED = (
    ("place", "my-life.html#where"),
    ("issues", "my-life.html#what"),
    ("why", "my-life.html#why"),
    ("action", "my-life.html#how"),
    ("research", "index.html"),
)


class GlobalNavigationTests(unittest.TestCase):
    def test_same_five_links_on_all_primary_pages(self):
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
                self.assertEqual(len(re.findall(r'data-pa-nav=', nav.group(0))), 5)
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
        self.assertNotIn("localStorage", life)

    def test_research_archive_is_collapsed_not_lost(self):
        home = (UI / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="pa-research-drawer"', home)
        self.assertIn("Browse all research sections", home)
        for key in ("redistricting", "authenticity", "promises", "decay", "research", "sources"):
            self.assertIn('data-page="' + key + '"', home)
        self.assertIn("function page(id)", home)
        self.assertIn('data-pa-nav="research" aria-current="page"', home)

    def test_responsive_shared_navigation_and_accessibility(self):
        css = (UI / "global-navigation.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:repeat(5,minmax(0,1fr))", css)
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
