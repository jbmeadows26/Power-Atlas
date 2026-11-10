"""Release validation for Power Atlas visual atlas v4.

Run: python -m unittest discover -s tests -p 'test_visual_atlas_review.py'
No paid services or secret credentials required; cross-site links are checked statically.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "platform" / "unified"
RESEARCH = ROOT / "site"
EXEMPT = {"redesign-preview.html"}


class VisualAtlasReviewTests(unittest.TestCase):
    def test_all_active_pages_use_shared_visual_assets(self):
        for folder in (UNIFIED, RESEARCH):
            pages = [p for p in folder.glob("*.html") if p.name not in EXEMPT]
            self.assertGreater(len(pages), 5, str(folder))
            for page in pages:
                with self.subTest(page=page.relative_to(ROOT)):
                    html = page.read_text(encoding="utf-8")
                    self.assertIn('href="atlas-visual-system.css"', html)
                    self.assertIn('src="atlas-visual-system.js"', html)
                    self.assertIn("</html>", html.lower())

    def test_all_gallery_destinations_exist_in_unified(self):
        destinations = [
            "my-life.html", "corporate-ownership.html", "consumer-practices.html",
            "dark-money.html", "source-audit.html", "reform-lab.html",
            "business-influence.html", "class-actions.html", "compare.html",
        ]
        for destination in destinations:
            with self.subTest(destination=destination):
                self.assertTrue((UNIFIED / destination).is_file())

    def test_cpi_example_matches_official_source_snapshot(self):
        metrics = json.loads(
            (ROOT / "data/place-impact/connected-metrics-v1.json").read_text(encoding="utf-8")
        )
        script = (UNIFIED / "atlas-visual-system.js").read_text(encoding="utf-8")
        expected = {
            "transport": "transport",
            "housing": "housing",
            "groceries": "groceries",
            "health": "health",
        }
        for key, metric_id in expected.items():
            source_value = metrics["national"][metric_id]["yoyPct"]
            pattern = rf'\{{key:"{re.escape(key)}",label:"[^"]+",value:([0-9.]+)'
            found = re.search(pattern, script)
            self.assertIsNotNone(found, f"No visual index value for {key}")
            self.assertAlmostEqual(float(found.group(1)), float(source_value), places=2)
        self.assertIn("not household bill dollars", script.lower())

    def test_clickable_chart_and_evidence_preservation(self):
        for folder in (UNIFIED, RESEARCH):
            script = (folder / "atlas-visual-system.js").read_text(encoding="utf-8")
            css = (folder / "atlas-visual-system.css").read_text(encoding="utf-8")
            with self.subTest(folder=folder):
                self.assertIn('make("button","pa3-chart-row")', script)
                self.assertIn('"aria-pressed"', script)
                self.assertIn(".pa4-chart-takeaway", css)
                self.assertIn("source(links,src", script)
                self.assertIn('https://power-atlas-unified.vercel.app/', script)
                self.assertIn('class-actions.html', script)
                self.assertIn('Seven paths into the evidence.', script)
                self.assertIn('pa4-tile--claims', script)
                self.assertNotIn('noindex,nofollow', script)
                self.assertNotIn('Preview-only link rewrites:', script)
                self.assertNotIn('DESIGN REVIEW · NOT PRODUCTION', script)
                self.assertNotIn('__PA4_UNIFIED_PREVIEW__', script)
                self.assertNotIn('power-atlas-visual-review.vercel.app', script)
                self.assertNotIn('.pa4-review-ribbon', css)

    def test_class_actions_source_links_and_visual_integrity(self):
        html = (UNIFIED / "class-actions.html").read_text(encoding="utf-8")
        visual_js = (UNIFIED / "class-actions-visual.js").read_text(encoding="utf-8")
        consumer = (UNIFIED / "consumer-practices.html").read_text(encoding="utf-8")
        preview = (UNIFIED / "redesign-preview.html").read_text(encoding="utf-8")
        for asset in ("class-actions-visual.css", "class-actions-visual.js"):
            self.assertIn(asset, html)
            self.assertTrue((UNIFIED / asset).is_file())
        self.assertIn("poweratlas:class-actions-loaded", visual_js)
        self.assertIn('id="caDeadlineTimeline"', html)
        self.assertIn('id="caDonut"', html)
        self.assertIn('href="class-actions.html"', consumer)
        self.assertIn('href="class-actions.html"', preview)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_shared_javascript_parses(self):
        for folder in (UNIFIED, RESEARCH):
            with self.subTest(folder=folder):
                result = subprocess.run(
                    ["node", "--check", str(folder / "atlas-visual-system.js")],
                    capture_output=True, text=True, check=False, timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
