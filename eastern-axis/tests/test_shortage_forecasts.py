#!/usr/bin/env python3
"""Fail-closed offline regressions for conditional product shortage analyst."""
from datetime import datetime,timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import forecast_product_shortages as mod

NOW=datetime(2026,11,21,20,0,tzinfo=timezone.utc)

def metric(key="worldbank-brent", latest=155):
    values=[100]*13+[110,120,latest]
    history=[{"period":f"{year}-{month:02d}","value":v}
             for (year,month),v in zip([(2025,m) for m in range(7,13)]
                                         + [(2026,m) for m in range(1,11)],values)]
    return {"id":key,"label":"Commodity test","source":"World Bank Pink Sheet",
            "sourceUrl":"https://www.worldbank.org/en/research/commodity-markets",
            "period":"2026-10","value":latest,"history":history,"unit":"$/mt","changePct":20}

def features(latest_date="2026-11-20",drop=True):
    # Fourteen continuous source-dated daily snapshots, on a single mapped corridor.
    from datetime import timedelta,date
    latest=date.fromisoformat(latest_date)
    return [{"attributes":{"date":(latest-timedelta(days=i)).isoformat(),
             "portname":"Strait of Hormuz","n_total":30 if drop and i<7 else 100}}
            for i in range(14)]

def data(metrics):
    return {"schemaVersion":1,"checkedAt":"2026-11-21T19:00:00Z","metrics":metrics}

class ShortageSafetyTests(unittest.TestCase):
    def test_price_is_not_shortage_or_command_escalation(self):
        result=mod.forecast(data([metric()]),now=NOW)
        fuel=next(r for r in result["forecasts"] if r["id"]=="fuel")
        self.assertEqual(fuel["status"],"input-cost-watch")
        self.assertFalse(fuel["confirmedShortage"])
        self.assertFalse(fuel["commandEligible"])
        self.assertEqual(result["summary"]["commandEligible"],0)
        self.assertEqual(fuel["confidence"],"limited")
    def test_two_independent_aggregate_proxies_remain_unverified(self):
        result=mod.forecast(data([metric()]),{"status":"observed","features":features()},now=NOW)
        fuel=next(r for r in result["forecasts"] if r["id"]=="fuel")
        self.assertEqual(fuel["status"],"cross-source-watch")
        self.assertGreater(fuel["screenScore"],30)
        self.assertEqual(len({e["publisher"] for e in fuel["evidence"]}),2)
        self.assertFalse(fuel["confirmedShortage"])
        self.assertFalse(fuel["modelReviewed"])
        self.assertEqual(result["summary"]["commandEligible"],0)
    def test_stale_shipping_does_not_corroborate(self):
        result=mod.forecast(data([metric()]),{"status":"observed","features":features("2026-10-01")},now=NOW)
        fuel=next(r for r in result["forecasts"] if r["id"]=="fuel")
        self.assertEqual(fuel["status"],"input-cost-watch")
        self.assertEqual(fuel["routeSeriesAvailable"],0)
    def test_no_inventory_or_price_is_a_gap(self):
        result=mod.forecast(data([]),now=NOW)
        self.assertEqual(result["summary"]["dataGaps"],14)
        self.assertTrue(all(not r["confirmedShortage"] for r in result["forecasts"]))
    def test_stale_price_is_not_current(self):
        m=metric()
        m["period"]="2026-01"
        result=mod.forecast(data([m]),now=NOW)
        self.assertEqual(next(x for x in result["forecasts"] if x["id"]=="fuel")["status"],"data-gap")
    def test_unknown_source_and_mismatched_history_fail_closed(self):
        for changed in ({"sourceUrl":"http://invalid.gov/"},{"value":999}):
            m={**metric(),**changed}
            result=mod.forecast(data([m]),now=NOW)
            self.assertEqual(next(x for x in result["forecasts"] if x["id"]=="fuel")["status"],"data-gap")
    def test_invalid_root_rejected(self):
        with self.assertRaises(ValueError):
            mod.forecast({"schemaVersion":1,"metrics":"bad"},now=NOW)
    def test_network_error_never_creates_an_alert(self):
        with patch.object(mod,"urlopen",side_effect=OSError("offline")):
            status=mod.fetch_portwatch()
        self.assertEqual(status["status"],"unavailable")
        self.assertEqual(status["features"],[])

if __name__=="__main__":
    unittest.main()
