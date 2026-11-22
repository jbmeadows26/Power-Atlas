"""Global military asset change analyst: source, baseline and promotion guards."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("asset_analyst",ROOT/"scripts"/"analyze_military_asset_changes.py")
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
CHECKED=datetime(2026,11,22,tzinfo=timezone.utc)

def time_series(latest=2025,current=900_000_000,base=200_000_000,name="Fixture Country"):
    return {year:{"value":float(current if year==latest else base+(year%3)*5_000_000),"country":name}
            for year in range(latest-8,latest+1)}

def fixtures():
    return {
      "MS.MIL.MPRT.KD":{"US":time_series()},
      "MS.MIL.XPRT.KD":{"CN":time_series(current=80_000_000,base=700_000_000)},
      "MS.MIL.TOTL.P1":{"RU":time_series(latest=2020,current=450_000,base=300_000)}}

def empty_holdings():
    return {"schemaVersion":1,"observations":[]}

def empty_inventory():
    return {"schemaVersion":1,"assets":[{"code":"US","category":"Naval","name":"Source-estimate"}]}

class MilitaryAssetAnalystTest(unittest.TestCase):
    def test_full_history_detects_extraordinary_transfer_flow_not_inventory(self):
        report=a.report_from_series(fixtures(),empty_holdings(),empty_inventory(),as_of=CHECKED)
        imp=next(x for x in report["assessments"] if x["code"]=="US")
        exp=next(x for x in report["assessments"] if x["code"]=="CN")
        self.assertEqual(imp["baseline"]["status"],"assessable")
        self.assertEqual(imp["status"],"review")
        self.assertEqual(imp["baseline"]["direction"],"expanding")
        self.assertEqual(exp["baseline"]["direction"],"contracting")
        self.assertTrue(imp["notInventoryChange"])
        self.assertEqual(report["summary"]["confirmedInventoryChanges"],0)
        self.assertIn("transfers-not-inventory",imp["evidenceClass"])
        self.assertEqual(report["category"],"Defense, Security & Cyber")

    def test_no_missing_values_as_zero_and_no_two_point_baselines(self):
        series=time_series()
        del series[2020]
        data={"MS.MIL.MPRT.KD":{"US":series},"MS.MIL.XPRT.KD":{},"MS.MIL.TOTL.P1":{}}
        report=a.report_from_series(data,empty_holdings(),empty_inventory(),as_of=CHECKED)
        row=report["assessments"][0]
        self.assertEqual(row["baseline"]["status"],"insufficient-history")
        self.assertEqual(row["status"],"data-gap")
        self.assertIsNone(row["baseline"]["robustZ"])
        self.assertFalse(row["anomalous"])

    def test_old_personnel_estimate_cannot_be_current_escalation(self):
        report=a.report_from_series(fixtures(),empty_holdings(),empty_inventory(),as_of=CHECKED)
        personnel=next(x for x in report["assessments"] if x["kind"]=="personnel-estimate")
        self.assertEqual(personnel["observationYear"],2020)
        self.assertEqual(personnel["status"],"historical")
        self.assertFalse(personnel["anomalous"])
        self.assertIn("Historical annual",personnel["reason"])

    def test_tiny_arms_import_baseline_cannot_trigger_false_spike(self):
        levels=[0.0]*8
        s=a.robust_change(levels,100_000_000,"MS.MIL.MPRT.KD")
        self.assertEqual(s["direction"],"unassessed")
        s=a.robust_change([1_000_000]*8,75_000_000,"MS.MIL.MPRT.KD")
        self.assertNotEqual(s["direction"],"expanding")

    def test_world_bank_pages_must_be_complete(self):
        with self.assertRaisesRegex(ValueError,"truncated"):
            a.checked_page([{"pages":2,"total":200},[{"date":"2025"}]],"world")
        with self.assertRaises(ValueError):
            a.crosswalk([{"pages":1,"total":0},[]])

    def test_crosswalk_drops_aggregates_and_invalid_iso_codes(self):
        response=[{"pages":1,"total":3},[
            {"id":"USA","iso2Code":"US","region":{"id":"NAC"}},
            {"id":"WLD","iso2Code":"1W","region":{"id":"NA"}},
            {"id":"CHN","iso2Code":"CN","region":{"id":"EAS"}}]]
        countries={row["id"]:row["iso2Code"] for row in response[1]
                   if row["region"]["id"]!="NA"}
        result=a.parse_indicator([{"pages":1,"total":3},[
            {"countryiso3code":"USA","date":"2025","value":100,"country":{"value":"United States"}},
            {"countryiso3code":"WLD","date":"2025","value":900,"country":{"value":"World"}},
            {"countryiso3code":"CHN","date":"2024","value":200,"country":{"value":"China"}}]],
            countries,"MS.MIL.MPRT.KD",CHECKED)
        self.assertEqual(set(result),{"US","CN"})

    def test_official_holding_requires_original_sources_and_review(self):
        template={"code":"FR","year":2015,"category":"Naval",
                  "equipmentType":"Surface combatants","count":12,
                  "basis":"All commissioned surface combatants",
                  "sourceUrl":"https://www.unroca.org/","publisher":"UNROCA",
                  "sourceReviewed":True}
        invalid={**template,"sourceReviewed":False}
        with self.assertRaises(ValueError):a.validate_holdings({"schemaVersion":1,"observations":[invalid]})
        with self.assertRaises(ValueError):a.validate_holdings({"schemaVersion":1,"observations":[{**template,"count":-1}]})
        self.assertEqual(len(a.validate_holdings({"schemaVersion":1,"observations":[template]})),1)

    def test_comparable_source_dated_equipment_holdings_can_enter_review_queue(self):
        observations=[]
        for year in range(2017,2026):
            observations.append({
                "code":"FR","countryName":"France","year":year,"category":"Naval",
                "equipmentType":"Surface combatants","count":20 if year==2025 else 10,
                "basis":"Commissioned surface combatants; same source definition",
                "sourceUrl":f"https://www.unroca.org/{year}","publisher":"UNROCA",
                "sourceReviewed":True})
        rows=a.assess_holdings(a.validate_holdings({"schemaVersion":1,"observations":observations}),CHECKED)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["kind"],"equipment-holdings")
        self.assertEqual(rows[0]["status"],"review")
        self.assertTrue(rows[0]["anomalous"])
        self.assertEqual(rows[0]["previousValue"],10)

    def test_missing_annual_holding_reports_not_zero(self):
        observations=[{"code":"FR","year":2024,"category":"Air",
                "equipmentType":"Combat aircraft","count":70,
                "basis":"Active aircraft","sourceUrl":"https://www.unroca.org/2024",
                "publisher":"UNROCA","sourceReviewed":True},
            {"code":"FR","year":2025,"category":"Air","equipmentType":"Combat aircraft",
                "count":100,"basis":"Active aircraft","sourceUrl":"https://www.unroca.org/2025",
                "publisher":"UNROCA","sourceReviewed":True}]
        rows=a.assess_holdings(a.validate_holdings({"schemaVersion":1,"observations":observations}),CHECKED)
        self.assertEqual(rows[0]["status"],"data-gap")
        self.assertIsNone(rows[0]["baseline"]["robustZ"])

    def test_model_never_converts_transfer_flow_into_confirmed_inventory(self):
        report=a.report_from_series(fixtures(),empty_holdings(),empty_inventory(),as_of=CHECKED)
        answer={"id":report["assessments"][0]["id"],"decision":"investigate",
                "rationale":"The annual observed transfer volume is outside its historical baseline."}
        class Resp:
            def __enter__(self):return self
            def __exit__(self,*args):return False
        with mock.patch.object(a.urllib.request,"urlopen",return_value=Resp()),\
             mock.patch.object(a.json,"load",return_value={"response":json.dumps(answer)}):
            a.review_with_model(report,"http://127.0.0.1:11434")
        self.assertEqual(report["summary"]["confirmedInventoryChanges"],0)
        self.assertTrue(all(x["notInventoryChange"] for x in report["assessments"]))

    def test_no_hidden_fabricated_history_in_initial_holdings_file(self):
        doc=json.loads((ROOT/"public/analysis/military-holdings-history.json").read_text())
        self.assertEqual(a.validate_holdings(doc),[])
        self.assertTrue(doc["status"].startswith("awaiting-"))

if __name__=="__main__":
    unittest.main()
