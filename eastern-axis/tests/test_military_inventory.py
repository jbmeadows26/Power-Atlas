"""Military coverage regression tests: provenance, date, and no false zero."""
import importlib.util
import json
from pathlib import Path
import unittest

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

if __name__=="__main__": unittest.main()
