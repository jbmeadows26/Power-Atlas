"""Daily Life cost explorer: source boundaries, interactive wiring, and privacy."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "platform" / "unified" / "my-life.html"
SCRIPT = ROOT / "platform" / "unified" / "personal-cost-explorer.js"

EXPECTED = {
    "housing", "groceries", "energy", "health", "work",
    "schools", "transport", "public-services", "representation",
}


class PersonalCostExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = HTML.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")

    def test_all_nine_category_ids_match_selected_issue(self):
        topics = set(re.findall(
            r'(?m)^\s*(housing|groceries|energy|health|work|schools|transport|representation|"public-services"):\{',
            self.script,
        ))
        self.assertEqual({x.strip('"') for x in topics}, EXPECTED)
        self.assertGreaterEqual(self.script.count('part("'), 30)

    def test_mounted_in_step_two_and_category_changes_update_the_inputs(self):
        self.assertIn('id="personalCostExplorer"', self.page)
        self.assertLess(
            self.page.index('id="personalCostExplorer"'),
            self.page.index('id="why"'),
        )
        self.assertIn('src="personal-cost-explorer.js" defer', self.page)
        self.assertIn("PowerAtlasCostExplorer?.setTopic(id)", self.page)
        self.assertIn('href="#benchmarkStory"', self.page)
        self.assertIn('id="compareYourCosts"', self.page)

    def test_estimates_are_user_entered_not_imputed_from_zip_or_cpi(self):
        self.assertIn('data-ce-kind="current"', self.script)
        self.assertIn('data-ce-kind="scenario"', self.script)
        self.assertIn('alternative+=b===null?a:b', self.script)
        self.assertIn('fmt(delta*12)', self.script)
        self.assertIn("compared?", self.script)
        self.assertIn("not quoted local prices or guaranteed savings", self.script)
        self.assertIn("No dollar figure is inferred from your ZIP code", self.script)

    def test_nonmonetary_category_and_no_double_count_reminder(self):
        self.assertIn("Political influence is not a household invoice", self.script)
        self.assertIn("representation:{", self.script)
        self.assertIn("parts:[]", self.script)
        self.assertIn("avoid double-counting", self.script)

    def test_source_links_and_no_collection_of_personal_expenses(self):
        self.assertIn('target="_blank" rel="noopener noreferrer"', self.script)
        self.assertIn("Related official source", self.script)
        for forbidden in ("localStorage", "sessionStorage", "sendBeacon", "navigator.geolocation",
                          "fetch(", "XMLHttpRequest"):
            self.assertNotIn(forbidden, self.script)
        self.assertIn("amounts stay in this browser tab only", self.script)

    def test_input_safety_and_accessibility(self):
        self.assertIn('aria-label="', self.script)
        self.assertIn('min="0" max="1000000"', self.script)
        self.assertIn("Number.isFinite(n)", self.script)
        self.assertIn('aria-live="polite"', self.page)
        self.assertIn("esc(p.name)", self.script)


if __name__ == "__main__":
    unittest.main()
