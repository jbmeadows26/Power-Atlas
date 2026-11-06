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
        self.assertIn("8.6% higher", geo["finding"])
        self.assertIn("do not establish", geo["finding"])
        fin = geo["companyFinancials"]
        self.assertEqual(fin["changeUsd"], 207847000)
        self.assertEqual(fin["observations"][1]["revenueUsd"] - fin["observations"][0]["revenueUsd"], fin["changeUsd"])
        self.assertEqual(fin["newBusiness2025"]["amountUsdUpperBoundApprox"], 520000000)
        self.assertIn("not cash collected", fin["newBusiness2025"]["basis"])
        self.assertIn("sec.gov", fin["source"])

    def test_actual_disclosed_contributions_and_operating_income(self):
        geo = next(x for x in self.data["cases"] if x["id"] == "geo")
        rows = geo["politicalByCalendarYear"]
        self.assertEqual([y["year"] for y in rows], [2024, 2025])
        self.assertEqual(rows[0]["combinedUsd"], 4023200)
        self.assertEqual(rows[1]["combinedUsd"], 4425400)
        for item in rows:
            self.assertEqual(item["corporateUsd"] + item["pacUsd"], item["combinedUsd"])
            self.assertTrue(item["source"].startswith("https://"))
        lobby = geo["lobbyingDisclosures"]
        self.assertEqual(lobby["federalUsd"] + lobby["stateLocalUsd"], lobby["combinedUsd"])
        self.assertEqual(lobby["combinedUsd"], 5371336)
        self.assertNotEqual(lobby["combinedUsd"], rows[-1]["combinedUsd"])
        operating = geo["companyFinancials"]["operatingIncomeUsd"]
        self.assertEqual(operating[0]["amountUsd"], 309975000)
        self.assertEqual(operating[1]["amountUsd"], 257490000)
        self.assertEqual(
            operating[-1]["amountUsd"] - operating[0]["amountUsd"],
            geo["companyFinancials"]["operatingProfitChangeUsd"]
        )
        self.assertLess(geo["companyFinancials"]["operatingProfitChangePct"], 0)
        self.assertIn("None of these facts establish", geo["finding"])
        self.assertIn("not", geo["lobbyingDisclosures"]["meaning"])

    def test_unmerged_treasury_and_fec_evidence(self):
        geo = next(x for x in self.data["cases"] if x["id"] == "geo")
        self.assertEqual(geo["entityIdentifiers"]["exactPrimeRecipientUEI"], "JMLKZZ1NL2Z6")
        self.assertEqual(geo["entityIdentifiers"]["companyPACFecCommitteeId"], "C00382150")
        pacmar = next(x for x in self.data["cases"] if x["id"] == "pacmar")
        self.assertEqual(pacmar["entityIdentifiers"]["exactPrimeRecipientUEI"], "L1WZRB6JKWJ4")
        self.assertEqual(self.data["primaryDataLink"]["collectionStatus"], "published_original_treasury_transaction_snapshot")
        self.assertIn("no", self.data["purpose"].lower())
        self.assertNotEqual(geo["disclosedPolitical"]["totalUsd"],
                            geo["politicalByCalendarYear"][1]["combinedUsd"])

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
        self.assertIn("financials(c)", p)
        self.assertIn("politicalSeries(c)", p)
        self.assertIn("Operating income · SEC filed", p)
        self.assertIn("federal-contract-transactions-v1.json", p)
        self.assertIn("geo-pac-candidate-disbursements-v1.json", p)
        self.assertIn("SEC Form 10-K", p)
        self.assertIn("showStep", p)
        self.assertIn('aria-pressed', p)
        self.assertIn("View political-spending evidence", p)
        self.assertIn("No financial values are being inferred", p)
        self.assertIn("No zeros or business gains have been invented", p)
        self.assertIn("federal-contractor restrictions", p)
        self.assertIn("not yet a verified company-to-contract award join", p)

    def test_published_official_treasury_transactions(self):
        source = ROOT / "data/business-influence/federal-contract-transactions-v1.json"
        self.assertTrue(source.is_file(), "The official transaction file was previously published; preserve it")
        d = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(d["schema"], "power-atlas.business-federal-contract-transactions.v1")
        self.assertEqual(
            {e["id"]: e["uei"] for e in d["entities"]},
            {"geo": "JMLKZZ1NL2Z6", "pacmar": "L1WZRB6JKWJ4"}
        )
        for entity in d["entities"]:
            self.assertGreaterEqual(len(entity["years"]), 9)
            self.assertIn("not paid cash", entity["coverageNote"])
            self.assertEqual(entity["scope"], "exact_UEI_prime_contract_actions_only_excludes_sibling_subsidiary_UEIs")
            self.assertTrue(all(y["sourcePagesRead"] > 0 for y in entity["years"]))
            self.assertTrue(all(y["transactionCount"] >= 0 for y in entity["years"]))
            for y in entity["years"]:
                self.assertAlmostEqual(y["grossPositiveObligationsUsd"] + y["deobligationsUsd"], y["netObligationsUsd"], places=2)
            self.assertTrue(all(x["source"].startswith("https://www.usaspending.gov/award/") for y in entity["years"] for x in y["topAwardsByAbsoluteNetChange"]))
        geo = next(e for e in d["entities"] if e["id"] == "geo")
        years = {y["fiscalYear"]: y for y in geo["years"]}
        self.assertEqual(years[2024]["netObligationsUsd"], 641589367.03)
        self.assertEqual(years[2025]["netObligationsUsd"], 791460351.57)
        self.assertEqual(years[2026]["netObligationsUsd"], 1006358861.91)
        self.assertTrue(years[2027]["partialFiscalYear"])
        self.assertEqual(d["causalStatus"], "no_validated_donation_to_award_decision_path_or_matched_counterfactual")

    def test_evidence_sources_do_not_include_personal_contact_data(self):
        text = DATA.read_text(encoding="utf-8").lower()
        self.assertNotIn("street_address", text)
        self.assertNotIn("home_address", text)
        self.assertNotIn("phone_number", text)
        self.assertNotIn("email_address", text)
        self.assertTrue(any("matched non-donors" in x for x in self.data["analyticRules"]))

if __name__ == "__main__":
    unittest.main()
