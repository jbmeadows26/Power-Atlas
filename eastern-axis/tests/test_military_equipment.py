"""Fixture-based tests for global military equipment imports and provenance."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("mil_equipment",ROOT/"scripts"/"collect_military_equipment.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class MilitaryEquipmentTests(unittest.TestCase):
    def test_source_is_immutable_and_wide(self):
        self.assertIn("2026-q4-r20261121",MOD.DOWNLOAD_URL)
        self.assertEqual(len(MOD.EXPECTED_SHA256),64)
        self.assertIn("creativecommons.org",MOD.LICENCE)
        self.assertGreaterEqual(len(MOD.CATEGORIES),25)
        self.assertNotIn("nuclear_warheads",MOD.CATEGORIES)
        self.assertNotIn("military_satellites_score",MOD.CATEGORIES)

    @staticmethod
    def make_data():
        # Fixture exercises 175 countries x all 27 countable metrics.
        rows=[]
        category={name:cat.lower() for name,cat in MOD.CATEGORIES.items()}
        category={k:("missile" if v=="missiles" else v) for k,v in category.items()}
        for index in range(175):
            code=chr(65+index//26)+chr(65+index%26)
            for metric,cat in category.items():
                rows.append(dict(iso2=code,iso3="XXX",country="Fixture "+code,
                    metric_code=metric,metric=metric.replace("_"," ").title(),
                    category=cat,unit="count",year="2026",value="4",
                    confidence="medium",source="Fixture open-source estimate",source_url=""))
        rows[0]["value"]="0"  # A claimed zero must not be treated as confirmed absence.
        rows[1]["confidence"]="estimate"
        return rows

    def test_dated_equipment_estimates_and_zero_handling(self):
        rows=self.make_data()
        records,health=MOD.make_equipment_entries(rows)
        self.assertEqual(len(records),175*len(MOD.CATEGORIES)-1)
        self.assertEqual(health["countries"],175)
        self.assertTrue(all(r["readiness"]=="not-verified" for r in records))
        self.assertTrue(all(r["value"]>0 for r in records))
        self.assertTrue(all(r["observationYear"]==2026 for r in records))
        self.assertTrue(all(r["licence"]==MOD.LICENCE for r in records))
        self.assertTrue(any(r["status"]=="editorial-estimate" for r in records))
        self.assertTrue(any(r["category"]=="Land" for r in records))
        self.assertTrue(any(r["category"]=="Naval" for r in records))
        self.assertTrue(any(r["category"]=="Air" for r in records))
        self.assertTrue(any(r["category"]=="Space" for r in records))
        self.assertFalse(any(r["metricCode"]=="nuclear_warheads" for r in records))

    def test_duplicate_and_unit_errors_fail(self):
        rows=self.make_data()
        rows.append(dict(rows[7]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):MOD.make_equipment_entries(rows)
        rows=self.make_data()
        rows[10]["unit"]="usd"
        with self.assertRaisesRegex(ValueError,"count unit"):MOD.make_equipment_entries(rows)

    def test_collector_never_writes_unchecked_values(self):
        path=ROOT/"public"/"analysis"/"military-inventory.json"
        catalog=json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(any(a["status"]=="military-stockpile" for a in catalog["assets"]))
        added=[a for a in catalog["assets"] if a["id"].startswith("dml-")]
        if added:
            self.assertGreaterEqual(len(added),1600)
            self.assertTrue(all(a["confidence"] in MOD.CONFIDENCE for a in added))
            self.assertTrue(all(a["value"]>0 and a["readiness"]=="not-verified" for a in added))
            self.assertTrue(all(a["sourceDatasetUrl"]==MOD.DOWNLOAD_URL for a in added))
            self.assertEqual(catalog["collectionHealth"]["equipment"]["sha256"],MOD.EXPECTED_SHA256)

if __name__=="__main__": unittest.main()
