"""Housing bedroom-level HUD rental reference regression suite.

All state data must have source attribution, verify five bedroom sizes and
avoid treating HUD voucher-program reference gross rents as asking rents.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "platform" / "unified" / "my-life.html"
UI = ROOT / "platform" / "unified" / "cost-benchmark-story.js"
HOUSES = ROOT / "data" / "housing" / "bedroom-rents"
STATES = set(("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN "
              "MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA "
              "WA WV WI WY").split())


class HousingBedroomRentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = UI.read_text(encoding="utf-8")
        cls.page = PAGE.read_text(encoding="utf-8")

    def test_rent_card_source_government_year_and_independent_attribution(self):
        data = json.loads((HOUSES / "NJ.json").read_text(encoding="utf-8"))
        self.assertEqual(data["state"], "NJ")
        self.assertEqual(data["fy"], 2027)
        self.assertEqual(data["effective"], "2026-10-01")
        self.assertIn("HUD", data["officialSource"].upper())
        self.assertEqual(data["license"], "CC BY 4.0")
        self.assertIn("Multifamily Today", data["attribution"])
        self.assertEqual(len(data["zips"]["07010"][0][1]), 5)

    def test_all_state_and_dc_files_exist_with_five_prices(self):
        states = {p.stem for p in HOUSES.glob("??.json")}
        self.assertEqual(states, STATES)
        for state in STATES:
            with self.subTest(state=state):
                data = json.loads((HOUSES / (state + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(data["state"], state)
                self.assertEqual(data["fy"], 2027)
                self.assertGreaterEqual(len(data["zips"]), 5)
                for zipcode, areas in data["zips"].items():
                    self.assertRegex(zipcode, r"^[0-9]{5}$")
                    for item in areas:
                        self.assertIn(item[0], data["areas"])
                        self.assertEqual(len(item[1]), 5)
                        self.assertTrue(all(isinstance(n, (int, float)) and n > 0 for n in item[1]))
                        if len(item) == 3:
                            self.assertEqual(len(item[2]), 5)

    def test_loads_by_selected_state_without_sending_zip_to_rent_provider(self):
        self.assertIn("RENT_FILES+st+\".json\"", self.ui)
        self.assertIn("RENT_PROVIDER+st+\".json\"", self.ui)
        self.assertIn("if(!zip||!/^[0-9]{5}$/.test(zip))", self.ui)
        self.assertIn('id="housingBedroomPanel"', self.ui)
        self.assertIn("renderHousingRents();", self.ui)

    def test_clear_separation_from_market_asking_rent(self):
        self.assertIn("not today’s advertised apartment prices", self.ui.lower())
        self.assertIn("tenant-paid utilities", self.ui)
        self.assertIn("gross rent", self.ui.lower())
        self.assertIn("HUD area", self.ui)
        self.assertIn("FY 2026 amount marked", self.ui)
        self.assertIn("spendBlock='<details", self.ui)

    def test_accessible_mobile_layout_and_multiple_hud_areas(self):
        self.assertIn(".bs-rent-grid", self.page)
        self.assertIn('grid-template-columns:repeat(2,minmax(0,1fr))', self.page)
        self.assertIn('id="bsRentRegion"', self.ui)
        self.assertIn('aria-label="Choose HUD rent area', self.ui)
        self.assertIn("showHousingRent(hud,zip,Number(this.value))", self.ui)

    def test_zip_state_fallback(self):
        self.assertIn('first["state abbreviation"]', self.page)
        self.assertIn("selectedStateCode=", self.page)
        self.assertIn("data/housing/bedroom-rents/", self.ui)


if __name__ == "__main__":
    unittest.main()
