"""Verify macro/global signal scope and corporate influence separation in Power Atlas."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/place-impact/economic-forces-v1.json"
PAGE = ROOT / "platform/unified/my-life.html"
SCRIPT = ROOT / "platform/unified/cost-benchmark-story.js"
OWNERS = ROOT / "data/corporate-ownership/verified-relationships-v1.json"
CASES = ROOT / "data/corporate-ownership/transparency-price-power-v1.json"
FINANCE = ROOT / "data/business-influence/evidence-v1.json"
TOPICS = {"housing", "groceries", "energy", "health", "work", "schools",
          "transport", "public-services", "representation"}


class EconomicForcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")

    def test_scope_and_indicators(self):
        self.assertEqual(self.data["schema"], "power-atlas.economic-forces.v1")
        self.assertEqual(self.data["asOf"], "2026-11-06")
        self.assertEqual(set(self.data["topics"]), TOPICS)
        signal_ids = [x["id"] for x in self.data["signals"]]
        self.assertEqual(len(signal_ids), len(set(signal_ids)))
        self.assertGreaterEqual(len(signal_ids), 10)
        allowed = {"measured", "forecast", "policy_decision", "research_estimate"}
        for signal in self.data["signals"]:
            self.assertIn(signal["kind"], allowed)
            self.assertTrue(signal["source"].startswith("https://"))
            for field in ("value", "period", "scope", "explain", "limits"):
                self.assertTrue(signal[field], (signal["id"], field))

    def test_all_topic_refs_are_source_backed(self):
        ids = {x["id"] for x in self.data["signals"]}
        for topic, config in self.data["topics"].items():
            with self.subTest(topic=topic):
                self.assertTrue(set(config["domestic"]) <= ids)
                self.assertTrue(set(config["global"]) <= ids)
                self.assertGreaterEqual(len(config["domestic"]), 2)
                self.assertGreaterEqual(len(config["global"]), 2)
                self.assertEqual(len(config["mechanisms"]), 2)
                self.assertTrue(config["firm"].strip())

    def test_bls_and_global_series_not_equated(self):
        d = {x["id"]: x for x in self.data["signals"]}
        self.assertEqual(d["allcpi"]["value"], "+3.7%")
        self.assertEqual(d["foodhome"]["value"], "+1.8%")
        self.assertEqual(d["energy"]["value"], "+20.4%")
        self.assertEqual(d["fed"]["value"], "3.75–4.00%")
        self.assertEqual(d["imf_growth"]["kind"], "forecast")
        self.assertEqual(d["global_energy"]["kind"], "forecast")
        self.assertIn("NOT the change in household bills", d["global_energy"]["limits"])
        self.assertEqual(d["tariff_pass"]["kind"], "research_estimate")
        self.assertIn("NOT a 26% rise", d["tariff_pass"]["limits"])
        self.assertEqual(d["imports"]["value"], "+8.1%")

    def test_company_sources_exist_and_are_not_causal(self):
        graph = json.loads(OWNERS.read_text(encoding="utf-8"))
        case = json.loads(CASES.read_text(encoding="utf-8"))
        finance = json.loads(FINANCE.read_text(encoding="utf-8"))
        owners = {r["id"] for r in graph["relations"]}
        self.assertTrue({"pg-kindercare", "bezos-amazon-2026",
                         "orlando-thoma-bravo", "cvs-caremark"} <= owners)
        self.assertTrue(any(c["id"] == "transparency-rent" for c in case["cases"]))
        self.assertTrue(any(c["id"] == "transparency-pbm" for c in case["cases"]))
        self.assertTrue(any(c["id"] == "geo" for c in finance["cases"]))
        self.assertIn("doesNotEstablishPoliticalCausation", case["cases"][0])
        self.assertIsNone(case["cases"][0]["measuredIndividualCostUsd"])

    def test_source_to_interface_wiring(self):
        for marker in ["SOURCE_BUSINESS_INFLUENCE", "corporateExamples", "ownershipExamples",
                       "moneyExample", "syncCostBenchmark", "getBenchmarkContext"]:
            self.assertIn(marker, self.page)
        for marker in ["FORCES_URL", "renderEconomicForces()+", "bs-force-trail",
                       "ownershipLinks+moneyStory", "bs-status-kind", "Observed association"]:
            self.assertIn(marker, self.script)
        self.assertIn('id="benchmarkStory"', self.page)
        self.assertLess(self.page.index('id="benchmarkStory"'),
                        self.page.index('id="personalCostExplorer"'))

    def test_ethical_limitations(self):
        s = self.script
        self.assertIn("No company or wealthy individual is assigned an individual cost premium", self.data["rules"][2])
        self.assertIn("do not", s.lower())
        self.assertIn("local", self.data["rules"][3].lower())
        for prohibited in ("localStorage", "sessionStorage", "sendBeacon", "navigator.geolocation"):
            self.assertNotIn(prohibited, s)
        self.assertIn("A named billionaire", s)
        self.assertIn("No local household price effect", s)

if __name__ == "__main__":
    unittest.main()
