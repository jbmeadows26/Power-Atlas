"""Eight-company donor-to-government-business candidate directory guardrails."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/business-influence/additional-candidates-v1.json"
PAGE=ROOT/"platform/unified/business-candidates.html"
HOME=ROOT/"platform/unified/index.html"
PARENT=ROOT/"platform/unified/business-influence.html"


class BusinessCandidatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(DATA.read_text(encoding="utf-8"))
        cls.entries=cls.data["entries"]

    def test_source_backed_identifiers_and_report_cutoffs(self):
        self.assertEqual(self.data["schema"],"power-atlas.business-influence.additional-candidates.v1")
        self.assertEqual(len(self.entries),8)
        self.assertEqual(len({x["id"] for x in self.entries}),8)
        self.assertEqual(len({x["pac"]["fecCommitteeId"] for x in self.entries}),8)
        for company in self.entries:
            p, l=company["pac"],company["legalRecipient"]
            self.assertRegex(p["fecCommitteeId"],r"^C[0-9]{8}$")
            self.assertRegex(l["uei"],r"^[A-Z0-9]{12}$")
            self.assertTrue(p["notCompanyCorporateGiving"])
            self.assertGreater(p["amountUsd"],0)
            self.assertEqual(p["reportingPeriodStart"],"2025-01-01")
            self.assertGreaterEqual(p["reportingPeriodEnd"],"2026-06-30")
            self.assertLessEqual(p["reportingPeriodEnd"],"2026-11-06")
            self.assertTrue(p["source"].startswith("https://www.fec.gov/"))
            self.assertTrue(l["source"].startswith("https://www.usaspending.gov/"))
            self.assertIn("not",company["limits"].lower())
        self.assertTrue(any(x["pac"]["classification"].startswith("secondary") for x in self.entries))
        self.assertTrue(any(x["pac"]["classification"].startswith("official") for x in self.entries))

    def test_corporate_giving_and_pac_are_distinct(self):
        core=next(x for x in self.entries if x["id"]=="corecivic")
        p=core["political"]
        self.assertAlmostEqual(p["combinedUsd"],p["corporateUsd"]+p["pacUsd"],places=2)
        self.assertNotEqual(p["combinedUsd"],core["pac"]["amountUsd"])
        self.assertGreater(p["lobbyingUsdApprox"],p["combinedUsd"])
        self.assertNotEqual(core["financials"]["years"][0]["revenueUsdApprox"],
                            core["financials"]["years"][1]["revenueUsdApprox"])
        self.assertIn("sec.gov",core["financials"]["source"])

    def test_identity_and_type_mismatch_explicitly_visible(self):
        byid={x["id"]:x for x in self.entries}
        self.assertNotEqual(byid["rtx"]["legalRecipient"]["uei"],
                            byid["rtx"]["legalRecipient"]["parentUei"])
        self.assertNotEqual(byid["boeing"]["exampleAward"]["recipientUei"],
                            byid["boeing"]["legalRecipient"]["uei"])
        self.assertIn("distinct",byid["amazon-aws"]["limits"].lower())
        self.assertTrue(byid["amazon-aws"]["pac"]["classification"].startswith("secondary"))
        self.assertLess(byid["exxon"]["exampleAssistance"]["amountUsd"],0)
        self.assertIn("deobligation",byid["exxon"]["exampleAssistance"]["type"])
        self.assertTrue(byid["microsoft"]["corporatePolicy"]["notEquivalentToPAC"])

    def test_new_page_and_navigation_and_noncausal_language(self):
        page=PAGE.read_text(encoding="utf-8")
        self.assertIn("additional-candidates-v1.json",page)
        self.assertIn('d.entries?.length!==8',page)
        self.assertIn("secondary",page)
        self.assertIn("Financial assistance is NOT procurement",page)
        self.assertIn("No firms match",page)
        self.assertIn('data-filter="cloud"',page)
        self.assertIn('data-filter="energy"',page)
        self.assertIn("not established",self.data["plainLanguage"].lower()) if "not established" in self.data["plainLanguage"].lower() else self.assertIn("No improper influence",self.data["plainLanguage"])
        self.assertEqual(len(re.findall(r"<script\s*>",page)),1)
        self.assertIn("business-candidates.html",HOME.read_text(encoding="utf-8"))
        self.assertIn("business-candidates.html",PARENT.read_text(encoding="utf-8"))
        self.assertNotIn("Personal Address",DATA.read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
