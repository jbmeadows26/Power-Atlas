"""Ensure the Consumer Watch visual language and sourced charts reach every production page."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIRS = [ROOT / "platform" / "unified", ROOT / "site"]


class VisualSystemTests(unittest.TestCase):
    def test_shared_assets_match_and_parse(self):
        for name in ("atlas-visual-system.css", "atlas-visual-system.js"):
            self.assertEqual((DIRS[0] / name).read_bytes(), (DIRS[1] / name).read_bytes())
        if shutil.which("node"):
            for directory in DIRS:
                checked = subprocess.run(["node", "--check", str(directory / "atlas-visual-system.js")],
                                         capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_all_existing_public_html_surfaces_have_shared_design(self):
        for directory in DIRS:
            pages = sorted(directory.glob("*.html"))
            self.assertGreaterEqual(len(pages), 7)
            for page in pages:
                if page.name == "consumer-practices.html":
                    # Consumer Watch is the source design system; keep its own approved styling.
                    continue
                with self.subTest(page=str(page.relative_to(ROOT))):
                    s = page.read_text(encoding="utf-8")
                    self.assertIn('href="atlas-visual-system.css"', s)
                    self.assertIn('src="atlas-visual-system.js"', s)

    def test_visuals_use_real_source_data_and_explain_limits(self):
        js = (DIRS[0] / "atlas-visual-system.js").read_text(encoding="utf-8")
        self.assertIn("cost-benchmark-drivers-v1.json", js)
        self.assertIn("fec-federal-cycle-overview-2002-2026.json", js)
        self.assertIn("brennan-top40-midterms-2014-2026.json", js)
        self.assertIn("consumer-class-actions/cases-v1.json", js)
        self.assertIn('coverage==="complete_24mo"', js)
        self.assertIn("No chart is shown without verified source values", js)
        self.assertIn("preliminary snapshot", js)
        self.assertIn("Same October 14 cutoff", js)
        self.assertNotIn("Math.random", js)
        self.assertNotIn("innerHTML", js)

    def test_mobile_chart_detail_does_not_force_wide_tables(self):
        css=(DIRS[0] / "atlas-visual-system.css").read_text(encoding="utf-8")
        self.assertIn(".pa3-chart details table", css)
        self.assertIn("table-layout:fixed!important", css)
        self.assertIn("min-width:0!important", css)
        self.assertIn("overflow-wrap:anywhere", css)

    def test_chart_sources_support_data(self):
        bls = json.loads((ROOT / "data" / "place-impact" / "cost-benchmark-drivers-v1.json").read_text())
        for key in ("housing", "transport", "groceries", "health", "schools"):
            self.assertGreater(bls["topics"][key]["headline"]["annual"], 0)
        fec = json.loads((ROOT / "data" / "money-influence" / "fec-federal-cycle-overview-2002-2026.json").read_text())
        self.assertGreaterEqual(len([x for x in fec["cycles"] if x["coverage"] == "complete_24mo" and
                                     isinstance(x.get("congressionalReceipts24M"), (float, int))]), 7)
        donors = json.loads((ROOT / "data" / "money-influence" / "brennan-top40-midterms-2014-2026.json").read_text())
        self.assertEqual(len({x["cycle"] for x in donors["records"]}), 4)


if __name__ == "__main__":
    unittest.main()
