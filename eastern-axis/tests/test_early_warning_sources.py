#!/usr/bin/env python3
"""Fixture-only validation for FAO nominal indices and GNSS accuracy series."""
import importlib.util
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import unittest

SRC=Path(__file__).resolve().parents[1] / "scripts" / "early_warning_sources.py"
spec=importlib.util.spec_from_file_location("early_warning_sources",SRC)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)


class SourceTests(unittest.TestCase):
    def test_fao_index_uses_two_actual_months_not_publication_date(self):
        raw=(
          "World Food Situation / nominal indices\n"
          "Date,Food Price Index,Meat,Dairy,Cereals,Oils,Sugar\n"
          "2026-08,133.3,120,120,115,180,110\n"
          "2026-09,135.5,123,119,122,194,112\n"
          "2026-10,133.9,125,117.8,116.8,199.2,121.3\n"
        ).encode()
        results=mod.read_fao_csv(raw)
        self.assertEqual(len(results),6)
        food=next(x for x in results if x["id"]=="fao-food")
        self.assertEqual(food["period"],"2026-10")
        self.assertEqual(food["previousPeriod"],"2026-09")
        self.assertEqual(food["value"],133.9)
        self.assertEqual(food["group"],"global")
        self.assertTrue(food["changePct"]<0)
        self.assertIn("2014",food["unit"])

    def test_fao_header_and_insufficient_data_fail(self):
        with self.assertRaises(ValueError):
            mod.read_fao_csv(b"Month,Food\n2026-10,133.9\n")
        with self.assertRaises(ValueError):
            mod.read_fao_csv(b"Date,Food Price Index,Meat,Dairy,Cereals,Oils,Sugar\n2026-10,133.9,125,118,117,199,121\n")

    def test_gnss_series_uses_coverage_denominator_and_percentage_points(self):
        newest=date.today()
        prev=newest-timedelta(days=1)
        raw=json.dumps({"slug":"world","version":4,"days":[
            {"date":prev.isoformat(),"hexes":1000,"red":30,"yellow":20,"green":950,"aircraft":35000,"bad":120,"pct":5},
            {"date":newest.isoformat(),"hexes":1020,"red":42,"yellow":30,"green":948,"aircraft":35100,"bad":140,"pct":7.1},
        ]}).encode()
        result=mod.read_gps_series(raw,"world","global","Worldwide")
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["value"],7.1)
        self.assertEqual(result[0]["changePp"],2.1)
        self.assertEqual(result[0]["compareMode"],"percentage-points")
        self.assertEqual(result[0]["sampleSize"],1020)
        self.assertIn("not confirmed jamming",result[0]["source"])

    def test_gnss_fails_for_stale_or_unverifiable_samples(self):
        past=date.today()-timedelta(days=15)
        prior=past-timedelta(days=1)
        series={"slug":"world","version":4,"days":[
          {"date":past.isoformat(),"hexes":100,"red":5,"yellow":5,"green":90,"aircraft":4000,"bad":50,"pct":10},
          {"date":prior.isoformat(),"hexes":100,"red":2,"yellow":3,"green":95,"aircraft":4000,"bad":50,"pct":5},
        ]}
        with self.assertRaises(ValueError):
            mod.read_gps_series(json.dumps(series).encode(),"world","global","Worldwide")
        series["days"][0]["date"]=date.today().isoformat()
        with self.assertRaises(ValueError):
            mod.read_gps_series(json.dumps(series).encode(),"iran","IR","Iran")


if __name__=="__main__":
    unittest.main()
