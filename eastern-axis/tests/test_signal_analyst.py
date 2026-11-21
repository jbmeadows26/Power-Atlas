#!/usr/bin/env python3
"""Offline regression tests for signal evidence gates and official event adapters."""
from datetime import datetime,timezone,timedelta
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("signal_analyst",ROOT/"analyze_early_warning.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
import early_warning_events as ev

TODAY=datetime.now(timezone.utc)
DAY=TODAY.date().isoformat()
STAMP=TODAY.isoformat(timespec="seconds").replace("+00:00","Z")
SOURCE="https://www.newyorkfed.org/markets/reference-rates/sofr"

def snapshot(metrics=None,eventFeeds=None):
    return {"schemaVersion":1,"checkedAt":STAMP,"status":"ok",
            "metrics":metrics or [],"eventFeeds":eventFeeds or [],
            "sources":[{"id":"test","status":"ok"}]}

def example_metric():
    return {"id":"sofr-rate","label":"SOFR","value":4.0,"previous":3.0,
            "period":DAY,"previousPeriod":(TODAY-timedelta(days=1)).date().isoformat(),
            "interval":"daily","compareMode":"basis-points","changeBps":100,
            "changePct":33.333,"sourceUrl":SOURCE,"source":"NY Fed","group":"US",
            "history":[{"period":(TODAY-timedelta(days=15-i)).date().isoformat(),
                        "value":3.0+0.01*(i%4)} for i in range(16)]}

def alert():
    return {"id":"nws-123","title":"Severe Flood Warning — county","observedAt":STAMP,
            "group":"US","severity":"Severe","officialAlert":True,
            "sourceUrl":"https://api.weather.gov/alerts/abc123"}

class AnalystSafetyTest(unittest.TestCase):
    def test_all_source_metrics_screened_no_auto_elevation(self):
        report=mod.evaluate(snapshot(metrics=[example_metric()]))
        self.assertEqual(report["summary"]["observed"],1)
        self.assertEqual(report["summary"]["screened"],1)
        self.assertEqual(report["summary"]["elevated"],0)
        self.assertEqual(report["model"]["status"],"unavailable")
        self.assertEqual(report["reviews"][0]["status"],"monitor")

    def test_model_cannot_promote_single_source_outlier(self):
        m=example_metric()
        with patch.object(mod,"model_assess",return_value=({m["id"]:{"decision":"elevate","confidence":"high","rationale":"Highly unusual but no second independent source available"}},"available")):
            report=mod.evaluate(snapshot(metrics=[m]))
        self.assertEqual(report["summary"]["elevated"],0)
        self.assertIn("withheld",report["reviews"][0]["reason"])

    def test_verifiable_active_direct_official_advisory_can_escalate(self):
        source={"id":"nws-severe","publisher":"NWS","events":[alert()]}
        with patch.object(mod,"model_assess",return_value=({"nws-123":{"decision":"elevate","confidence":"high","rationale":"Current officially issued severe flood warning with named location"}},"available")):
            report=mod.evaluate(snapshot(eventFeeds=[source]))
        self.assertEqual(report["summary"]["elevated"],1)
        self.assertEqual(report["alerts"][0]["sourceUrl"],"https://api.weather.gov/alerts/abc123")

    def test_cross_publisher_statistical_market_break_can_escalate(self):
        def previous_month(n):
            index=TODAY.year*12+TODAY.month-1-n
            return f"{index//12:04d}-{index%12+1:02d}"
        def commodity(metric_id,publisher):
            points=[{"period":previous_month(15-i),"value":100+(i%4)} for i in range(15)]
            last=points[-1]["value"]
            points.append({"period":previous_month(0),"value":160})
            return {"id":metric_id,"label":metric_id,"source":publisher,"sourceUrl":"https://example.gov/source",
                    "group":"global","interval":"monthly","period":previous_month(0),
                    "previousPeriod":previous_month(1),"value":160,"previous":last,
                    "changePct":(160/last-1)*100,"compareMode":"percent","history":points}
        wheat=commodity("worldbank-wheat","World Bank")
        cereals=commodity("fao-cereals","FAO")
        candidate=mod.screen(snapshot(metrics=[wheat,cereals]))
        self.assertEqual(len(candidate),2)
        self.assertTrue(all(r["anomalous"] and r["corroborated"] for r in candidate))
        fake={row["id"]:{"decision":"elevate","confidence":"high",
                "rationale":"Exceptionally large same-direction, source-dated grain price moves from two independent official publishers"}
                for row in candidate}
        with patch.object(mod,"model_assess",return_value=(fake,"available")):
            report=mod.evaluate(snapshot(metrics=[wheat,cereals]))
        self.assertEqual(report["summary"]["elevated"],2)
        self.assertEqual(report["alerts"][0]["kind"],"metric")

    def test_non_official_event_cannot_escalate(self):
        event=alert()
        event["officialAlert"]=False
        report=mod.evaluate(snapshot(eventFeeds=[{"id":"other","publisher":"NWS","events":[event]}]))
        self.assertEqual(report["summary"]["screened"],0)
        self.assertEqual(report["summary"]["elevated"],0)

    def test_stale_source_cannot_escalate(self):
        event=alert()
        event["observedAt"]=(TODAY-timedelta(days=12)).isoformat()
        report=mod.evaluate(snapshot(eventFeeds=[{"id":"nws","publisher":"NWS","events":[event]}]))
        self.assertEqual(report["summary"]["elevated"],0)
        self.assertEqual(report["summary"]["screened"],0)

    def test_missing_history_not_claimed_normal(self):
        m=example_metric()
        m.pop("history")
        report=mod.evaluate(snapshot(metrics=[m]))
        self.assertEqual(report["reviews"][0]["baseline"]["status"],"insufficient")
        self.assertEqual(report["summary"]["historyReady"],0)

    def test_invalid_source_schema_fails_closed(self):
        with self.assertRaises(ValueError):mod.evaluate({"metrics":[]})

    def test_cisa_kevs_are_not_breaches(self):
        raw={"catalogVersion":"2026.11.20","vulnerabilities":[{"cveID":"CVE-2026-11111",
             "dateAdded":DAY,"vendorProject":"Vendor","product":"Widget"}]}
        result=ev.read_kev(json.dumps(raw).encode())
        self.assertFalse(result["events"][0]["officialAlert"])
        self.assertEqual(result["events"][0]["group"],"global")

    def test_usgs_is_not_actor_attribution(self):
        raw={"type":"FeatureCollection","features":[{"type":"Feature","id":"a1","properties":{
            "mag":6.9,"time":int(TODAY.timestamp()*1000),"title":"M6.9 earthquake",
            "url":"https://earthquake.usgs.gov/earthquakes/eventpage/a1"}}]}
        result=ev.read_usgs(json.dumps(raw).encode())
        self.assertEqual(len(result["events"]),1)
        self.assertFalse(result["events"][0]["officialAlert"])

    def test_live_noaa_kp_object_array_schema(self):
        raw=[{"time_tag":"2026-11-19T03:00:00","Kp":4.33,"a_running":25,"station_count":8},
             {"time_tag":"2026-11-20T09:00:00","Kp":2.67,"a_running":12,"station_count":8}]
        report=ev.read_swpc(json.dumps(raw).encode())
        self.assertEqual(report["events"][0]["observedAt"],"2026-11-20T09:00:00")
        self.assertFalse(report["events"][0]["officialAlert"])

    def test_nws_active_severe_advisory_is_source_dated(self):
        raw={"type":"FeatureCollection","features":[{"type":"Feature","properties":{
            "@id":"https://api.weather.gov/alerts/abc123","event":"Flood Warning",
            "areaDesc":"Example County","severity":"Severe","status":"Actual",
            "effective":STAMP,"expires":(TODAY+timedelta(days=1)).isoformat()}}]}
        report=ev.read_nws(json.dumps(raw).encode())
        self.assertEqual(report["events"][0]["group"],"US")
        self.assertTrue(report["events"][0]["officialAlert"])

    def test_reject_external_lookalike_links(self):
        self.assertIsNone(ev.safe_url("https://api.weather.gov.bad.org/alerts/","api.weather.gov"))
        self.assertIsNone(ev.safe_url("http://api.weather.gov/alerts/","api.weather.gov"))

if __name__=="__main__":unittest.main()
