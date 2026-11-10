"""Evidence standards for Trump-linked financial flow reporting (no third party dependencies)."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIG=ROOT/"data/public-integrity/official-financial-flows-v1.json"
MIRROR=ROOT/"platform/unified/official-financial-flows-v1.json"
PAGE=ROOT/"platform/unified/financial-flows.html"

class FinancialFlowIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(ORIG.read_text(encoding="utf-8"))
        cls.html=PAGE.read_text(encoding="utf-8")

    def test_identical_static_and_canonical_datasets(self):
        self.assertEqual(self.data,json.loads(MIRROR.read_text(encoding="utf-8")))
        self.assertEqual(self.data["schema"],"power-atlas.official-financial-flows.v1")

    def test_all_20_entries_have_source_recipient_time_and_status(self):
        cases=self.data["cases"]
        self.assertEqual(len(cases),20)
        self.assertEqual(len({v["id"] for v in cases}),20)
        categories={v["id"] for v in self.data["categories"]}
        for v in cases:
            self.assertIn(v["category"],categories)
            self.assertTrue(v["from"] and v["to"] and v["period"] and v["caveat"])
            self.assertTrue(v["status"] and v["description"])
            self.assertEqual(v["legalFinding"],"no_legal_finding_established_by_this_record")
            self.assertGreaterEqual(len(v["sources"]),1)
            for source in v["sources"]:
                self.assertTrue(source["url"].startswith("https://"),(v["id"],source))
            self.assertTrue(v["amountUsd"] is None or v["amountUsd"]>0)
            self.assertNotEqual(v["measurement"],"personal_profit")

    def test_source_level_wallet_ambiguity_not_counted_twice(self):
        d=self.data
        self.assertEqual(d["crypto"]["minimumReview"],1143196249)
        self.assertEqual(d["crypto"]["potentialDuplicateWallets"],292388944)
        self.assertEqual(d["crypto"]["inclusiveReview"],1435585193)
        self.assertEqual(d["crypto"]["minimumReview"]+d["crypto"]["potentialDuplicateWallets"],d["crypto"]["inclusiveReview"])
        v={r["id"]:r for r in d["cases"]}
        self.assertEqual(v["wlf_token"]["overlap"],v["wlf_wallets"]["overlap"])
        self.assertEqual(v["foreign_revenue"]["overlap"],v["gulf_license"]["overlap"])
        self.assertEqual(v["wlf_wallets"]["status"],"reconciliation_required")

    def test_transaction_principal_is_not_personal_income(self):
        c={r["id"]:r for r in self.data["cases"]}
        self.assertEqual(c["mgx_usd1"]["amountUsd"],2000000000)
        self.assertEqual(c["mgx_usd1"]["measurement"],"investment_principal")
        self.assertIn("not a $2 billion payment",c["mgx_usd1"]["caveat"].lower())
        self.assertIsNone(c["qatar_747"]["amountUsd"])
        self.assertEqual(c["qatar_747"]["measurement"],"government_non_cash_gift")
        self.assertIn("U.S. Defense Department",c["qatar_747"]["to"])
        self.assertEqual(c["family_film"]["measurement"],"spouse_entity_proceeds")
        self.assertEqual(c["x_library"]["status"],"destination_unverified")

    def test_oge_claims_have_pdf_page_locations(self):
        c={r["id"]:r for r in self.data["cases"]}
        for case,p in [("meme_royalties",848),("stablecoin_equity",854),("wlf_token",855),("wlf_equity",855),("family_film",6),("filing_fees",1)]:
            self.assertEqual(c[case]["primaryLocation"]["pdfPage"],p)
            self.assertTrue(any("#page="+str(p) in x["url"] for x in c[case]["sources"]))

    def test_standalone_page_works_without_external_js_dependencies(self):
        for token in ["id=\"incomeChart\"","id=\"cards\"","id=\"filters\"",
                      "data-example=\"mgx_usd1\"","data-example=\"qatar_747\"",
                      "chooseFlow","renderCards","data-category=\"all\"",
                      "fetch('official-financial-flows-v1.json'","bug-report.js"]:
            self.assertIn(token,self.html)
        self.assertIn("setAttribute('aria-pressed'",self.html)
        self.assertIn("details",self.html)
        self.assertNotIn("proved corruption",self.html.lower())

    def test_integrated_links_are_real(self):
        for path in ["platform/unified/index.html","platform/unified/my-life.html",
                     "platform/unified/donor-intelligence.html","platform/unified/public-trading.html",
                     "platform/unified/business-influence.html","platform/unified/corporate-ownership.html"]:
            self.assertIn('href="financial-flows.html"',(ROOT/path).read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
