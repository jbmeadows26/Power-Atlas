"""Regression checks for public fare rates and non-causal transit accountability stories."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"place-impact"
APP=ROOT/"platform"/"unified"
FARES=DATA/"transport-fares-v1.json"
AUDIT=DATA/"transport-accountability-v1.json"
SCRIPT=APP/"transport-cost-story.js"
BENCHMARK=APP/"cost-benchmark-story.js"
PAGE=APP/"my-life.html"
PERSONAL=APP/"personal-cost-explorer.js"

class TransportCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fares=json.loads(FARES.read_text("utf-8"))
        cls.audit=json.loads(AUDIT.read_text("utf-8"))
        cls.script=SCRIPT.read_text("utf-8")
        cls.benchmark=BENCHMARK.read_text("utf-8")
        cls.page=PAGE.read_text("utf-8")
        cls.personal=PERSONAL.read_text("utf-8")

    def test_geography_and_sources_do_not_impute_route(self):
        self.assertEqual(self.fares["schema"],"power-atlas.transport-fares.v1")
        self.assertEqual(self.fares["asOf"],"2026-11-07")
        self.assertEqual({x["id"] for x in self.fares["regions"]},{"NYNJ","CHI","OTHER"})
        self.assertIn("not a detected route",self.script)
        self.assertIn("A ZIP cannot",self.script)
        self.assertIn("No fees are added without",self.fares["rule"])
        for row in self.fares["fares"]+self.fares["tolls"]:
            self.assertTrue(row["source"].startswith("https://"),row["id"])
            self.assertIn("verifiedAsOf",row)

    def test_real_fares_caps_and_separate_systems(self):
        d={x["id"]:x for x in self.fares["fares"]}
        self.assertEqual(d["mta-local"]["price"],3)
        self.assertEqual(d["mta-local"]["capWeekly"],35)
        self.assertEqual(d["mta-express"]["price"],7.25)
        self.assertEqual(d["mta-express"]["capWeekly"],67)
        self.assertEqual(d["path"]["price"],3.25)
        self.assertEqual(d["path"]["monthlyPass"],131.50)
        self.assertEqual(d["cta-rail"]["price"],2.50)
        self.assertEqual(d["cta-bus"]["price"],2.25)
        self.assertIsNone(d["njtransit-custom"]["price"])
        self.assertIsNone(d["metra-custom"]["price"])
        self.assertIn("separate",d["path"]["note"].lower())

    def test_tolls_direction_and_congestion_are_separate(self):
        d={x["id"]:x for x in self.fares["tolls"]}
        self.assertEqual(d["pa-peak"]["price"],16.79)
        self.assertEqual(d["pa-offpeak"]["price"],14.79)
        self.assertEqual(d["pa-mail"]["price"],23.30)
        self.assertEqual(d["nyc-congestion"]["price"],9)
        self.assertEqual(d["nyc-congestion-overnight"]["price"],2.25)
        self.assertIn("westbound into NJ is not tolled",d["pa-peak"]["note"])
        self.assertIn("only",d["nyc-congestion"]["note"])
        self.assertIn("congestion",self.script.lower())
        self.assertIn("exclusiveToll",self.script)
        self.assertIn("congestionCredit",self.script)

    def test_monthly_math_has_no_invented_pass_or_trip(self):
        # 5 roundtrip full-fare NYC subway commute days (10 paid trips).
        self.assertAlmostEqual(5*2*3*52/12,130)
        # 5 days with one NY-bound peak toll and the return direction untolled.
        self.assertAlmostEqual(5*16.79*52/12,363.7833333333)
        self.assertIn("52/12",self.script)
        self.assertIn("Math.min(weekly,item.capWeekly)",self.script)
        self.assertIn("No fees are added without",self.fares["rule"])
        self.assertIn("Month is modeled as 52 weeks",self.script)
        self.assertIn("not automatically applied",self.script)

    def test_evidence_for_integrity_has_noncausal_limitations(self):
        self.assertEqual(self.audit["schema"],"power-atlas.transport-accountability.v1")
        self.assertEqual(self.audit["asOf"],"2026-11-07")
        self.assertEqual(len(self.audit["pathways"]),4)
        cases={e["id"]:e for e in self.audit["examples"]}
        self.assertEqual(len(cases),4)
        self.assertEqual(cases["amtrak-kickbacks"]["status"],"civil_resolution_and_guilty_pleas")
        self.assertEqual(cases["mbta-warehousing"]["status"],"auditor_finding")
        self.assertEqual(cases["mbta-overtime-charges"]["status"],"charged_allegations")
        self.assertEqual(cases["amtrak-kickbacks"]["publicDollars"],2_000_000)
        for case in cases.values():
            self.assertTrue(case["source"].startswith("https://"))
            self.assertTrue(case["unproven"])
            self.assertTrue(any(term in case["unproven"].lower() for term in ("fare","ticket","toll","price")),case["id"])
        self.assertIn("No personal surcharge estimates",self.audit["findingRule"])
        self.assertIn("not proof of corruption",self.script)

    def test_page_sources_and_mobile_controls(self):
        self.assertIn('id="transportCostStory"',self.benchmark)
        self.assertIn('window.PowerAtlasTransport?.render()',self.benchmark)
        self.assertIn('transport-cost-story.js?v=',self.page)
        self.assertIn('PowerAtlasTransport.setContext(context)',self.page)
        self.assertIn('.ts-picker-grid',self.page)
        self.assertIn('.ts-audit-flow',self.page)
        self.assertIn('@media(max-width:750px)',self.page)
        self.assertIn("Optional · National average transport spending",self.benchmark)
        self.assertIn('(topic==="transport"?\'<section class="bs-inner ts-story"',self.benchmark)
        self.assertIn("')+spendBlock+",self.benchmark)

    def test_personal_expense_types_are_separate(self):
        for needle in ("Bridge, tunnel and road tolls","Congestion pricing or zone charges",
                       "Parking, meters and garages","Subway or metro fares",
                       "Local and express bus fares","Commuter rail and regional trains",
                       "Taxi, rideshare and micromobility"):
            self.assertIn(needle,self.personal)
        self.assertIn("Do not count travel costs again",self.personal)

    def test_user_inputs_are_private_and_untracked(self):
        for prohibited in ("localStorage","sessionStorage","navigator.geolocation",
                          "sendBeacon","XMLHttpRequest"):
            self.assertNotIn(prohibited,self.script)
        self.assertIn("All options begin unselected.",self.script)
        self.assertIn("user-selected scenario",self.script)
        self.assertIn("not a quoted route",self.script.lower())
        self.assertIn("No example shown assigns a dollar",self.script)

    def test_javascript_syntax_when_node_available(self):
        if not shutil.which("node"):self.skipTest("node unavailable")
        for path in (SCRIPT,BENCHMARK,PERSONAL):
            with self.subTest(file=path.name):
                r=subprocess.run(["node","--check",str(path)],text=True,capture_output=True)
                self.assertEqual(r.returncode,0,r.stderr)

if __name__=="__main__":unittest.main()
