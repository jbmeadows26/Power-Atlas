#!/usr/bin/env python3
"""Source schema and review-gate tests independent of network/model availability."""
from datetime import date, datetime, timezone
from pathlib import Path
import io
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import collect_shortage_inventory as inv
import forecast_product_shortages as fc
import review_shortage_outlook as ai

NOW=datetime(2026,11,21,20,0,tzinfo=timezone.utc)
EIA='STUB_1,STUB_2,11/13/26,11/6/26,Difference,11/14/25,Percent Change\nMotor Gasoline,Total Motor Gasoline,190,200,-10,220,-13.64\nMotor Gasoline,East Coast (PADD 1),50,55,-5,55,-9.1\n'
FRED="observation_date,ISRATIO\n"+'\n'.join(f"2025-{(i%12)+1:02d}-01,1.{i%6+10}" for i in range(12))+ "\n2026-10-01,1.30\n"
def stock():
    return inv.parse_eia(EIA, NOW.date())

def inventory():
    return {"schemaVersion":1,"checkedAt":NOW.isoformat(),"metrics":[stock()]}

def report_with_stock():
    data={"schemaVersion":1,"metrics":[],"checkedAt":NOW.isoformat()}
    return fc.forecast(data,now=NOW,inventory=inventory())

class CollectorTests(unittest.TestCase):
    def test_eia_direct_wholesale_inventory_not_local_stockout(self):
        row=stock()
        self.assertEqual(row["value"],190)
        self.assertLess(row["changeWeekPct"],-3)
        self.assertLess(row["changeYearPct"],-8)
        self.assertIn("retail",row["limitation"])
    def test_eia_region_row_cannot_replace_national(self):
        with self.assertRaises(ValueError):
            inv.parse_eia(EIA.replace("Total Motor Gasoline","East Coast (PADD 1)"),NOW.date())
    def test_eia_stale_fails(self):
        with self.assertRaises(ValueError):
            inv.parse_eia(EIA.replace("11/13/26","09/13/26"),NOW.date())
    def test_fred_broad_ratio_is_not_product_stock(self):
        row=inv.parse_fred(FRED,"ISRATIO",NOW.date())
        self.assertEqual(row["kind"],"sector-inventory-ratio")
        self.assertGreater(row["value"],0)
    def test_fred_missing_series_rejected(self):
        with self.assertRaises(ValueError):
            inv.parse_fred(FRED,"MNFCTRIRSA",NOW.date())
    def test_collection_failure_explicit_not_zero(self):
        def offline(*_):raise OSError("no network")
        report=inv.collect(now=NOW,downloader=offline)
        self.assertEqual(report["status"],"unavailable")
        self.assertEqual(report["metrics"],[])
        self.assertTrue(all(s["status"]=="unavailable" for s in report["sources"]))
    def test_measured_stocks_are_evidence_not_confirmed_shortage(self):
        result=report_with_stock()
        fuel=next(x for x in result["forecasts"] if x["id"]=="fuel")
        self.assertTrue(fuel["inventoryStockScreen"])
        self.assertEqual(fuel["status"],"inventory-watch")
        self.assertGreater(fuel["screenScore"],0)
        self.assertFalse(fuel["confirmedShortage"])
        self.assertFalse(fuel["commandEligible"])
    def test_sector_context_never_promotes_product(self):
        x={"schemaVersion":1,"checkedAt":NOW.isoformat(),"metrics":[{
          "id":"fred-ISRATIO","kind":"sector-inventory-ratio","label":"Total business ratio",
          "source":"Census via FRED","sourceUrl":"https://fred.stlouisfed.org/series/ISRATIO",
          "period":"2026-10-01","value":0.2}]}
        result=fc.forecast({"schemaVersion":1,"metrics":[]},now=NOW,inventory=x)
        self.assertEqual(result["summary"]["inventoryWatch"],0)
        self.assertTrue(all(r["status"]=="data-gap" for r in result["forecasts"]))

class ModelReviewTests(unittest.TestCase):
    def test_model_offline_retains_full_rules_assessment(self):
        r=ai.review(report_with_stock())
        self.assertEqual(r["analyst"]["screened"],14)
        self.assertEqual(r["analyst"]["status"],"unavailable")
        self.assertEqual(r["summary"]["modelReviewed"],0)
        self.assertTrue(all(not x["commandEligible"] for x in r["forecasts"]))
    def test_local_model_can_only_triage_not_claim_shortage(self):
        r=report_with_stock()
        answer={"message":{"content":json.dumps({"decision":"investigate","rationale":
            "Measured wholesale fuel inventories are declining and should be cross-checked against actual retail availability."})}}
        with patch.object(ai,"urlopen",return_value=io.BytesIO(json.dumps(answer).encode())):
            output=ai.review(r,"http://127.0.0.1:11434")
        fuel=next(x for x in output["forecasts"] if x["id"]=="fuel")
        self.assertTrue(fuel["modelReviewed"])
        self.assertEqual(fuel["modelAssessment"]["decision"],"investigate")
        self.assertFalse(fuel["confirmedShortage"])
        self.assertEqual(output["summary"]["commandEligible"],0)
    def test_model_fake_probability_rejected(self):
        candidate=next(x for x in report_with_stock()["forecasts"] if x["id"]=="fuel")
        answer={"message":{"content":json.dumps({"decision":"investigate",
          "rationale":"There is a 95% probability of a confirmed shortage, buy supplies immediately."})}}
        with patch.object(ai,"urlopen",return_value=io.BytesIO(json.dumps(answer).encode())):
            with self.assertRaises(ValueError):ai.ask_local(candidate,"http://127.0.0.1:11434")
    def test_remote_model_endpoints_rejected(self):
        with self.assertRaises(ValueError):
            ai.ask_local({"product":"Fuel","evidence":[]},"https://example.com")
    def test_invalid_model_response_fails_closed(self):
        r=report_with_stock()
        with patch.object(ai,"urlopen",side_effect=OSError("model down")):
            result=ai.review(r,"http://localhost:11434")
        self.assertEqual(result["analyst"]["status"],"unavailable")
        self.assertEqual(result["summary"]["commandEligible"],0)

if __name__=="__main__":
    unittest.main()
