"""Validate sourced business outcomes and guards against donation-to-contract inference."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/business-influence/evidence-v1.json"
PAGE = ROOT / "platform/unified/business-influence.html"
HOME = ROOT / "platform/unified/index.html"

class BusinessInfluenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_source_integrity(self):
        d = self.data
        self.assertEqual(d["schema"], "power-atlas.business-political-outcomes.v1")
        self.assertEqual(d["coverage"]["companyDonationToAwardReconciled"], "not_yet_verified")
        self.assertGreaterEqual(len(d["research"]), 3)
        self.assertGreaterEqual(len(d["cases"]), 2)
        for s in d["research"]:
            self.assertTrue(s["source"].startswith("https://"))
            self.assertTrue(s["scope"] and s["qualifier"])
        for case in d["cases"]:
            self.assertTrue(case["disclosedPolitical"]["source"].startswith("https://"))
            self.assertEqual(len(case["evidenceStages"]), 5)
            self.assertEqual(len({s["name"] for s in case["evidenceStages"]}), 5)
            self.assertTrue(any(s["status"] in {"missing", "disputed"} for s in case["evidenceStages"]))

    def test_geo_pac_and_corporate_funds_not_blended(self):
        geo = next(x for x in self.data["cases"] if x["id"] == "geo")
        giving = geo["disclosedPolitical"]
        self.assertEqual(giving["corporateUsd"], 3556200)
        self.assertEqual(giving["pacUsd"], 467000)
        self.assertEqual(giving["totalUsd"], giving["corporateUsd"] + giving["pacUsd"])
        self.assertIn("employee-funded", giving["label"])
        series = geo["governmentBusiness"]["observations"]
        self.assertLess(
            next(x["amountUsd"] for x in series if x["year"] == 2025),
            next(x["amountUsd"] for x in series if x["year"] == 2024)
        )
        self.assertNotIn("return on investment", geo["finding"].lower())
        self.assertIn("does not demonstrate a rise", geo["finding"])

    def test_no_fake_award_proceeds_for_pacmar(self):
        x = next(x for x in self.data["cases"] if x["id"] == "pacmar")
        self.assertEqual(x["governmentBusiness"]["observations"], [])
        self.assertIn("contested", x["finding"])
        self.assertEqual(x["evidenceStages"][3]["status"], "missing")

    def test_dashboard_integrated_and_survives_case_navigation(self):
        p = PAGE.read_text(encoding="utf-8")
        h = HOME.read_text(encoding="utf-8")
        self.assertIn("business-influence.html", h)
        self.assertIn("business-influence/evidence-v1.json", p)
        self.assertIn("renderCase", p)
        self.assertIn("showStep", p)
        self.assertIn('aria-pressed', p)
        self.assertIn("View political-spending evidence", p)
        self.assertIn("No financial values are being inferred", p)
        self.assertIn("federal-contractor restrictions", p)
        self.assertIn("not yet a verified company-to-contract award join", p)

    def test_evidence_sources_do_not_include_personal_contact_data(self):
        text = DATA.read_text(encoding="utf-8").lower()
        self.assertNotIn("street_address", text)
        self.assertNotIn("home_address", text)
        self.assertNotIn("phone_number", text)
        self.assertNotIn("email_address", text)
        self.assertTrue(any("matched non-donors" in x for x in self.data["analyticRules"]))

if __name__ == "__main__":
    unittest.main()
