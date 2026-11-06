"""Validate every Daily Life category has measured national, state and ZCTA evidence layers."""
import json
import math
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "data/place-impact"
TOPICS = {
    "housing", "groceries", "energy", "health", "work", "schools",
    "transport", "public-services", "representation"
}

class ConnectedDailyLifeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measured=json.loads((ROOT/"connected-metrics-v1.json").read_text(encoding="utf-8"))
        cls.local=json.loads((ROOT/"local-measures-v1.json").read_text(encoding="utf-8"))
        cls.health=json.loads((ROOT/"local-source-health-v1.json").read_text(encoding="utf-8"))
        cls.issues=json.loads((ROOT/"life-issues-v1.json").read_text(encoding="utf-8"))
        cls.ui=(BASE/"platform/unified/my-life.html").read_text(encoding="utf-8")

    def test_all_nine_have_verified_statistic_and_practical_resources(self):
        self.assertEqual(self.measured["schema"],"power-atlas.place-impact-connected-metrics.v1")
        self.assertEqual(set(self.measured["national"]),TOPICS)
        self.assertEqual(set(self.measured["topicSemantics"]),TOPICS)
        self.assertEqual(set(self.local["issues"]),TOPICS)
        self.assertEqual({x["id"] for x in self.issues["issues"]},TOPICS)
        for name,datum in self.measured["national"].items():
            with self.subTest(topic=name):
                self.assertTrue(isinstance(datum["value"],(int,float)))
                self.assertTrue(math.isfinite(datum["value"]))
                self.assertTrue(datum["source"].startswith("https://"))
                self.assertTrue(datum["period"])
                self.assertTrue(datum["method"] and datum["scope"])
                self.assertTrue(self.measured["topicSemantics"][name]["localUnknown"])
                self.assertEqual(len(self.local["issues"][name]["measures"]),2)
                self.assertTrue(all(x["columns"] and x["table"] for x in self.local["issues"][name]["measures"]))
        self.assertEqual(len(self.measured["sourceDatasets"]),5)

    def test_51_eia_and_bls_values_are_state_not_zip(self):
        e=self.measured["state"]["electricity_2024_all_sector_cents_per_kwh"]
        b=self.measured["state"]["unemployment_2026_09_seasonally_adjusted_pct"]
        self.assertEqual(len(e["values"]),51)
        self.assertEqual(len(b["values"]),51)
        self.assertEqual(set(e["values"]),set(b["values"]))
        self.assertEqual(e["values"]["IL"],12.21)
        self.assertEqual(e["values"]["NJ"],16.29)
        self.assertEqual(b["values"]["IL"],4.6)
        self.assertEqual(b["values"]["NJ"],4.2)
        self.assertIn("all",e["note"].lower())
        self.assertIn("seasonally",b["note"].lower())
        self.assertTrue(all(1<x<45 for x in e["values"].values()))
        self.assertTrue(all(0<=x<=25 for x in b["values"].values()))
        school=self.measured["state"]["school_2024_current_spending_per_pupil"]
        self.assertEqual(len(school["values"]),10)
        self.assertEqual(school["values"]["NJ"],27234)
        self.assertNotIn("IL",school["values"])
        self.assertIn("10",school["geographicLevel"])

    def test_cpi_year_over_year_and_macro_series_units(self):
        m=self.measured["national"]
        for k in ("housing","groceries","health","transport"):
            with self.subTest(topic=k):
                datum=m[k]
                self.assertTrue(datum["id"] and datum["id"]!="UNRATE")
                self.assertRegex(datum["period"],r"^20[0-9]{2}-[0-9]{2}$")
                self.assertGreaterEqual(datum["period"],"2026-09")
                expected=round(100*(datum["value"]/datum["previousYearSameMonth"]-1),2)
                self.assertAlmostEqual(datum["yoyPct"],expected,places=2)
                self.assertIn("index",datum["unit"])
                self.assertIn("not household",datum["method"].lower())
        self.assertEqual(m["work"]["unit"],"percent")
        self.assertEqual(m["schools"]["value"],17619)
        self.assertEqual(m["public-services"]["unit"],"billions_usd_annualized")
        self.assertEqual(m["representation"]["value"],51)
        self.assertIn("not",m["representation"]["method"])

    def test_nine_live_zcta_source_health_checks_and_18_observations(self):
        h=self.health
        self.assertEqual(h["schema"],"power-atlas.place-impact.local-source-health.v1")
        self.assertTrue(h["sampleIsNotUserLocation"])
        self.assertEqual(h["sampleZCTA"],"10001")
        self.assertEqual(set(h["observations"]),TOPICS)
        self.assertEqual(sum(len(x["measures"]) for x in h["observations"].values()),18)
        self.assertTrue(all(any(m["value"] is not None for m in x["measures"])
                            for x in h["observations"].values()))
        self.assertEqual(h["release"],"acs2024_5yr")
        self.assertIn("ZIP vs ZCTA",h["warning"])

    def test_navigation_reacts_to_topic_and_user_selected_state_without_inferred_results(self):
        for fragment in (
            "SOURCE_MEASURED","SOURCE_ELECTION_OFFICES","SOURCE_VOTER_RULES",
            "SOURCE_TREASURY_AWARDS","SOURCE_BUSINESS_PACS","SOURCE_CIVIC_REFORMS",
            "renderMeasuredSnapshot()","renderVerifiedLinks()","renderCivicRecordLinks()",
            'id="issueMetrics"','id="verifiedConnections"','id="reformEvidence"',
            "selectedStateCode","selectedStateName",
            "not your", "localMetrics",
        ):
            self.assertIn(fragment,self.ui)
        self.assertIn("Census Reporter",self.ui)
        self.assertIn("Zippopotam.us",self.ui)
        self.assertNotIn("localStorage",self.ui)
        self.assertNotIn("navigator.geolocation",self.ui)
        self.assertNotIn("No URL",self.ui)

if __name__=="__main__":
    unittest.main()
