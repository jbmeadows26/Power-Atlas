"""Military coverage regression tests: provenance, date, and no false zero."""
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("mil_inventory",ROOT/"scripts"/"collect_military_inventory.py")
collector=importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

class InventoryTest(unittest.TestCase):
 def test_baseline(self):
  obj=json.loads((ROOT/"public"/"analysis"/"military-inventory.json").read_text())
  self.assertEqual(obj["schemaVersion"],1)
  ids=[a["id"] for a in obj["assets"]]
  self.assertEqual(len(ids),len(set(ids)))
  nuke={a["code"]:a["value"] for a in obj["assets"] if a["status"]=="military-stockpile"}
  self.assertEqual(len(nuke),9)
  self.assertEqual(nuke["RU"],4400)
  self.assertEqual(nuke["CN"],620)
  for a in obj["assets"]:
   self.assertEqual(len(a["code"]),2)
   self.assertTrue(a["published"])
   self.assertTrue(a["url"].startswith("https://"))
   self.assertGreaterEqual(a["value"],0)
  self.assertGreaterEqual(len(obj["sources"]),10)

 def test_wdi_not_presented_as_current(self):
  rows=[{},[
    {"countryiso3code":"USA","date":"2018","value":100},
    {"countryiso3code":"USA","date":"2020","value":120},
    {"countryiso3code":"USA","date":"2021","value":None},
    {"countryiso3code":"CHN","date":"2020","value":200},
    {"countryiso3code":"WLD","date":"2020","value":900}
  ]]
  values=collector.latest_observations(rows,{"USA":"US","CHN":"CN"},"MS.MIL.TOTL.P1")
  self.assertEqual(values["US"]["value"],120)
  self.assertEqual(len(values),2)
  item=collector.make_entries("MS.MIL.TOTL.P1",values)[0]
  self.assertEqual(item["status"],"historical-active-personnel")
  self.assertIn("NOT a current 2026",item["detail"])
  self.assertEqual(item["published"],"2020")

 def test_counts_never_join_stockpile_and_deployed(self):
  obj=json.loads((ROOT/"public"/"analysis"/"military-inventory.json").read_text())
  for item in obj["assets"]:
   self.assertNotEqual(item.get("status"),"confirmed-operational")

 def test_reject_incomplete_world_bank_page(self):
  with self.assertRaisesRegex(ValueError,"Incomplete/paginated"):
   collector.require_complete_page([{"pages":2,"total":51},[{"value":1}]],"indicator")

 def test_failed_refresh_keeps_previous_observations(self):
  baseline=json.loads((ROOT/"public"/"analysis"/"military-inventory.json").read_text())
  old={"id":"wdi-MS-MIL-TOTL-P1-US","code":"US","category":"Personnel",
       "name":"Armed forces personnel (historical)","quantity":"100","value":100,
       "unit":"people","published":"2020","publisher":"IISS via World Bank WDI",
       "url":"https://data.worldbank.org/indicator/MS.MIL.TOTL.P1?locations=US",
       "basis":"Historic WDI/IISS estimate","detail":"Historical 2020",
       "status":"historical-active-personnel","estimate":True,"observationYear":2020}
  baseline["assets"].append(old)
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/"military-inventory.json"
   target.write_text(json.dumps(baseline))
   def fake_fetch(url):
    if "/country?" in url:
     return [{"pages":1,"total":1},[{"id":"USA","iso2Code":"US","region":{"id":"NAC"}}]]
    raise TimeoutError("test upstream outage")
   with mock.patch.object(collector,"OUT",target),mock.patch.object(collector,"fetch_json",side_effect=fake_fetch):
    collector.main()
   result=json.loads(target.read_text())
   preserved=[item for item in result["assets"] if item["id"]==old["id"]]
   self.assertEqual(preserved,[old])
   self.assertEqual(result["collectionHealth"]["worldBank"]["MS.MIL.TOTL.P1"]["state"],"stale")
   self.assertEqual(result["collectionHealth"]["worldBank"]["MS.MIL.XPND.CD"]["state"],"unavailable")
   self.assertEqual(len({item["id"] for item in result["assets"]}),len(result["assets"]))

if __name__=="__main__": unittest.main()
