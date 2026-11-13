"""Cliffside Park documentary: original-rate values, disclosure, navigation and fail-closed API."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "platform" / "unified"

class CliffsideStoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = (SITE / "cliffside-housing.html").read_text(encoding="utf-8")

    def test_documentary_has_interactive_comparison_and_nine_stages(self):
        for key in ("data-rate=\"general\"", "data-rate=\"effective\"",
                    "id=\"r2024\"", "id=\"r2025\"", "id=\"delta\"",
                    "id=\"trail\"", "id=\"inspector\"", "aria-live=\"polite\"",
                    "prefers-reduced-motion:reduce"):
            with self.subTest(key=key):
                self.assertIn(key, self.story)
        self.assertEqual(len(re.findall(r'<button type="button" data-stage="\d+"', self.story)), 9)
        self.assertIn('trail.addEventListener("click"', self.story)
        self.assertIn('aria-pressed', self.story)

    def test_rates_exactly_match_official_2024_and_2025(self):
        from json import loads
        obj = loads((ROOT / "data" / "housing" / "official-tax-rate-cliffside-park-2024-2025.json").read_text())
        y2024, y2025 = obj["observations"]
        self.assertEqual((y2024["generalTaxRatePer100"], y2024["effectiveTaxRatePer100"]), (2.756,1.966))
        self.assertEqual((y2025["generalTaxRatePer100"], y2025["effectiveTaxRatePer100"]), (2.836,1.920))
        for row in (y2024,y2025):
            self.assertIn(row["source"]["url"], self.story)
        for value in ("general:{a:2.756,b:2.836,d:0.080",
                      "effective:{a:1.966,b:1.920,d:-0.046"):
            self.assertIn(value,self.story)

    def test_public_api_is_gated_and_unavailable_is_not_zero_evidence(self):
        for key in ('fetch("api/housing-evidence"', 'data.status!=="approved_only"',
                    'Array.isArray(data.evidence)', 'if(!r.ok)throw',
                    '"Publication database unavailable.', '"No parcel-specific or political-finance assertions'):
            self.assertIn(key,self.story)
        self.assertIn('document.createElement("div")',self.story)
        self.assertNotIn("item.assertion_text}</",self.story)  # no dynamic HTML interpolation
        self.assertIn("No unapproved or cached research claims",self.story)

    def test_no_inferred_misconduct_and_links_from_main_surfaces(self):
        for term in ("Unresolved", "not evidence of wrongdoing", "A higher general rate",
                     "does not establish", "not proof of control"):
            self.assertIn(term.lower(),self.story.lower())
        for surface in ("my-life.html","investigations.html","why-costs-more.html"):
            if surface=="my-life.html":
                doc=(SITE / "my-life.html").read_text(encoding="utf-8")
            else:
                doc=(SITE / surface).read_text(encoding="utf-8")
            self.assertIn('href="cliffside-housing.html"',doc)

if __name__ == "__main__": unittest.main()
