"""Canonical Power Atlas My Place experience must not regress into old stacked designs."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"platform"/"unified"

class MyPlaceDocumentaryDiscoverabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=(SITE/"my-life.html").read_text(encoding="utf-8")
        cls.visual=(SITE/"visual-story-v6.js").read_text(encoding="utf-8")
        cls.css=(SITE/"visual-story-v6.css").read_text(encoding="utf-8")
        cls.loader=(SITE/"atlas-visual-system.js").read_text(encoding="utf-8")

    def test_home_has_no_competing_static_hero(self):
        self.assertNotIn('<div class="hero"><div class="wrapper">',self.home)
        self.assertIn('id="where"',self.home)
        self.assertIn('id="what"',self.home)
        self.assertLess(self.home.index('id="where"'),self.home.index('id="what"'))

    def test_home_does_not_inject_v3_v4_v5_presentation(self):
        self.assertIn('if(path==="my-life.html")return;',self.loader)
        self.assertIn('const standalone=/\\/my-life\\.html$/.test(location.pathname);',self.loader)
        self.assertIn('style.href="visual-story-v6.css"',self.loader)
        self.assertIn('script.src="visual-story-v6.js"',self.loader)
        self.assertIn('if(!former&&documentPath!=="my-life.html")return;',self.visual)

    def test_documentary_routes_are_immediate_visible_links(self):
        for href in ("why-costs-more.html","banking-power.html","take-action.html"):
            with self.subTest(href=href):
                self.assertIn('link.href=href;',self.visual)
                self.assertIn('"'+href+'"',self.visual)
        self.assertIn('intro.append(shortcuts)',self.visual)
        self.assertIn('class="pa-visual-story-feature" href="why-costs-more.html"',self.home)
        self.assertIn('class="pa-banking-feature" href="banking-power.html"',self.home)

    def test_obsolete_wildcard_hide_rule_is_deleted(self):
        self.assertNotIn('main > #what > :not(.section-head)',self.css)
        self.assertIn('main > #what > :is(#issueResult,#issueMetrics',self.css)
        self.assertIn('.vs6-story-routes',self.css)
        self.assertIn('prefers-reduced-motion',self.css)

    def test_canonical_frontends_share_visual_assets(self):
        for asset in ('atlas-visual-system.js','visual-story-v6.css','visual-story-v6.js'):
            self.assertEqual((SITE/asset).read_bytes(),(ROOT/"site"/asset).read_bytes())

if __name__=="__main__":
    unittest.main()
