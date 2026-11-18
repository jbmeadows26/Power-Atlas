#!/usr/bin/env python3
"""Fixture-based early warning parser safety tests; zero external network calls."""
import importlib.util
import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from openpyxl import Workbook

SOURCE=Path(__file__).resolve().parents[1]/"scripts"/"collect_early_warning.py"
sys.path.insert(0, str(SOURCE.parent))
spec=importlib.util.spec_from_file_location("early_warning",SOURCE)
mod=importlib.util.module_from_spec(spec)
sys.modules["early_warning"]=mod
spec.loader.exec_module(mod)

class CollectorTest(unittest.TestCase):
    def test_sofr_two_dated_observations(self):
        data={"refRates":[
            {"effectiveDate":"2026-11-16","type":"SOFR","percentRate":3.93,"volumeInBillions":3170},
            {"effectiveDate":"2026-11-17","type":"SOFR","percentRate":3.92,"volumeInBillions":3173}
        ]}
        result=mod.read_sofr(json.dumps(data).encode())
        self.assertEqual(len(result),2)
        self.assertEqual(result[0]["period"],"2026-11-17")
        self.assertEqual(result[0]["changeBps"],-1.0)
        self.assertEqual(result[1]["unit"],"US$ billions")
        self.assertEqual(result[1]["group"],"US")

    def test_sofr_missing_prior_rejected(self):
        payload={"refRates":[{"effectiveDate":"2026-11-17","type":"SOFR","percentRate":3.92,"volumeInBillions":3000}]}
        with self.assertRaises(ValueError):
            mod.read_sofr(json.dumps(payload).encode())

    def test_pink_sheet_headers_and_uneven_columns(self):
        wb=Workbook()
        ws=wb.active
        ws.title="Monthly Prices"
        ws.append(["World Bank historical prices"])
        ws.append(["Date","Crude oil, Brent","Natural gas (U.S.)","Urea","Copper"])
        ws.append(["units","$/bbl","$/mmbtu","$/mt","$/mt"])
        ws.append(["2026M09",70,3,300,10000])
        ws.append(["2026M10",77,3.5,330,11000])
        output=BytesIO()
        wb.save(output)
        values=mod.read_pink_sheet(output.getvalue())
        byid={m["id"]:m for m in values}
        self.assertEqual(byid["worldbank-urea"]["changePct"],10.0)
        self.assertEqual(byid["worldbank-copper"]["period"],"2026-10")
        self.assertEqual(byid["worldbank-brent"]["source"],"World Bank Pink Sheet")

    def test_scorecard_cannot_label_maintainer_malicious(self):
        payload={"date":"2026-11-17T10:00:00Z","score":7.9,
            "checks":[{"name":"Code-Review","score":7},{"name":"Signed-Releases","score":5}]}
        result=mod.parse_scorecard(json.dumps(payload).encode(),"curl/curl")
        self.assertEqual(result["codeReview"],7)
        self.assertIsNone(result["previousScore"])
        self.assertNotIn("malicious",json.dumps(result).replace("does not imply compromise or malicious maintainers",""))
        self.assertIn("does not imply",result["method"])

    def test_no_fake_zero_baselines(self):
        with self.assertRaises(ValueError): mod.change(20,0)
        with self.assertRaises(ValueError): mod.read_sofr(b'{"refRates": []}')

if __name__=="__main__":
    unittest.main()
