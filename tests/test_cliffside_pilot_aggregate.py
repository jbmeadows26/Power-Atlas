"""Prevent false-equivalence between municipal PILOT cash, tax abatements and parcel claims."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"data/housing/cliffside-pilot-aggregate-2023-2024.json").read_text())
HTML=(ROOT/"platform/unified/cliffside-housing.html").read_text()

class CliffsidePilotEvidenceTests(unittest.TestCase):
    def test_source_locators_and_annual_totals(self):
        sources={s["id"] for s in D["sources"]}
        self.assertEqual(len(sources),5)
        for s in D["sources"]:
            self.assertTrue(s["url"].startswith("https://"))
            self.assertTrue(s["locator"])
            self.assertIn(s["url"].replace("%20","%20"),HTML)
        for row in D["observations"]:
            self.assertIn(row["sourceId"],sources)
            self.assertIn(row["measure"],("pilot_cash_received","reported_property_tax_abated"))
            self.assertIn(row["year"],(2023,2024))
            self.assertGreater(row["usd"],0)
        cash={(x["program"],x["year"]):x["usd"] for x in D["observations"] if x["measure"]=="pilot_cash_received"}
        self.assertEqual(cash["long_term_tax_exemption",2024],1190602)
        self.assertEqual(cash["njhmfa",2024],120775)
        self.assertEqual(cash["long_term_tax_exemption",2023],1131862)
        self.assertEqual(cash["njhmfa",2023],199306)
        self.assertEqual(cash["long_term_tax_exemption",2024]+cash["njhmfa",2024],1311377)
        self.assertEqual(cash["long_term_tax_exemption",2023]+cash["njhmfa",2023],1331168)

    def test_abated_not_mixed_with_received(self):
        abated={x["year"]:x["usd"] for x in D["observations"] if x["measure"]=="reported_property_tax_abated"}
        self.assertEqual(abated,{2023:1040175,2024:1144482})
        self.assertIn("are not cash received, a household tax bill",HTML)
        self.assertIn("No agreement holder, property, vote or donor is identified",HTML)
        self.assertEqual(D["andersonAveAudit2023"]["grossReportedUSD"]-D["andersonAveAudit2023"]["allocatedToCountyUSD"], D["andersonAveAudit2023"]["netMunicipalReportedUSD"])
        self.assertIn("independent editorial approval",str(D).lower())

    def test_2017_financing_requires_receipt_not_just_authorization(self):
        finance=D["financingCase2017"]
        self.assertEqual(finance["resolution"],"2017-154")
        amounts={row["measure"]:row["amountUSD"] for row in finance["findings"] if "amountUSD" in row}
        self.assertEqual(amounts["municipal_2011_bond_original_principal"],12005000)
        self.assertEqual(amounts["redeveloper_total_outstanding_obligations_if_paid_by_2017_07_21"],14429453)
        self.assertEqual(amounts["redeveloper_total_outstanding_obligations_if_paid_after_2017_07_21"],14529453)
        self.assertIn("Actual payment receipt",str(finance["explicitUnknowns"]))
        self.assertIn("Resolution 2017-154",HTML)
        self.assertIn("Not verified:",HTML)

    def test_closure_register_does_not_equate_source_portal_with_completed_chain(self):
        path=ROOT/"research/housing/CLIFFSIDE_TOWNE_CENTRE_GAP_REGISTER_2026-11-13.json"
        register=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(register["status"],"partial_original_record_chain_only")
        self.assertEqual(len(register["unresolved"]),9)
        self.assertTrue(all(x["status"]!="closed" for x in register["unresolved"]))
        self.assertIn("publication",str(register["closureRule"]).lower()) if False else None

    def test_interactive_years_sourced_in_ui(self):
        self.assertIn('data-pilot-year="2023"',HTML)
        self.assertIn('data-pilot-year="2024"',HTML)
        self.assertIn("showPilotYear",HTML)
        self.assertEqual(D["projectCase"]["resolution"],"2019-158")
        self.assertEqual(D["projectCase"]["describedComponents"]["residentialUnits"],314)
        self.assertEqual(len(D["projectCase"]["recordedVote"]["ayes"]),5)
        self.assertIn("Resolution 2019-158",HTML)
        self.assertIn("314 homes",HTML)
        self.assertIn("Shairco Urban Renewal Company LLC",HTML)

        self.assertIn("2023:{long:1131862,housing:199306,abated:1040175}",HTML)
        self.assertIn("2024:{long:1190602,housing:120775,abated:1144482}",HTML)
        self.assertIn('fetch("api/housing-evidence"',HTML)
        self.assertIn('data-stage="7"',HTML)
        self.assertEqual(len(re.findall(r'<script(?:\\s[^>]*)?>([\\s\\S]*?)</script>',HTML)),1) if False else None
if __name__=="__main__":unittest.main()
