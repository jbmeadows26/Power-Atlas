"""Source and UI regression checks for benchmark-first Daily Life narrative."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "platform" / "unified" / "my-life.html"
STORY = ROOT / "platform" / "unified" / "cost-benchmark-story.js"
DATA = ROOT / "data" / "place-impact" / "cost-benchmark-drivers-v1.json"
EXPECTED = {
    "housing", "groceries", "energy", "health", "work",
    "schools", "transport", "public-services", "representation",
}

class BenchmarkStoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.script = STORY.read_text(encoding="utf-8")
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_nine_categories_and_primary_source(self):
        self.assertEqual(self.data["schema"], "power-atlas.cost-benchmark-drivers.v1")
        self.assertEqual(set(self.data["topics"]), EXPECTED)
        self.assertEqual(self.data["primarySource"], "https://www.bls.gov/news.release/cesan.htm")
        self.assertEqual(self.data["asOf"], "2026-11-06")
        self.assertIn("mean annual spending", self.data["measurement"])
        self.assertIn("weight", self.data["integrity"])

    def test_bls_2025_headlines(self):
        targets = {
            "housing": 27790, "groceries": 6491, "energy": 4931,
            "health": 6470, "work": 110847,
            "schools": 1583, "transport": 13492,
        }
        for topic, annual in targets.items():
            with self.subTest(topic=topic):
                self.assertEqual(self.data["topics"][topic]["headline"]["annual"], annual)
                self.assertEqual(self.data["topics"][topic]["headline"]["period"], "2025")
        self.assertIsNone(self.data["topics"]["public-services"]["headline"])
        self.assertIsNone(self.data["topics"]["representation"]["headline"])
        self.assertEqual(self.data["topics"]["work"]["headline"]["kind"], "income")

    def test_component_sums_match_source_rounding(self):
        for name, topic in self.data["topics"].items():
            slices = topic["slices"]
            if not slices:
                continue
            self.assertLessEqual(abs(sum(amount for _, amount in slices) - topic["headline"]["annual"]), 2, name)
            self.assertGreaterEqual(len(slices), 4)
        self.assertEqual(
            self.data["topics"]["energy"]["secondary"]["unit"], "¢/kWh"
        )

    def test_driver_evidence_in_every_topic(self):
        for name, topic in self.data["topics"].items():
            self.assertGreaterEqual(len(topic["drivers"]), 3, name)
            self.assertIn("localNote", topic)
            self.assertIn("disclaimer", topic)
            for d in topic["drivers"]:
                self.assertTrue(d["source"].startswith("https://"), name)
                for k in ("label", "why", "who", "choice"):
                    self.assertTrue(d[k].strip(), (name, k))

    def test_benchmark_before_optional_calculator_and_step_three(self):
        start = self.page.index('id="benchmarkStory"')
        personal = self.page.index('id="personalCostExplorer"')
        step_three = self.page.index('id="why"')
        self.assertLess(start, personal)
        self.assertLess(personal, step_three)
        self.assertIn('<details class="ce-optional"', self.page)
        self.assertIn('id="compareYourCosts"', self.page)
        self.assertRegex(self.page, r'src="cost-benchmark-story\.js\?v=[^"]+" defer')
        self.assertIn('href="#benchmarkStory"', self.page)
        self.assertIn("queueMicrotask(syncCostBenchmark)", self.page)

    def test_local_noncausal_guardrails(self):
        self.assertIn("record&&localMeasures?.provider?.release", self.page)
        self.assertIn("record.data?.data?.[geoid]", self.page)
        self.assertIn("getBenchmarkContext", self.page)
        self.assertIn("originalTable", self.page)
        self.assertIn("not a causal ranking for your ZIP", self.script)
        self.assertIn("not the percent of a price increase", self.script)
        self.assertIn("no local price has been inferred", self.script.lower())
        self.assertNotIn("localStorage", self.script)
        self.assertNotIn("sessionStorage", self.script)
        self.assertNotIn("XMLHttpRequest", self.script)
        self.assertNotIn("sendBeacon", self.script)
        self.assertNotIn("navigator.geolocation", self.script)

    def test_javascript_is_syntactically_valid_when_node_available(self):
        if not shutil.which("node"):
            self.skipTest("node unavailable")
        run = subprocess.run(["node", "--check", str(STORY)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

if __name__ == "__main__":
    unittest.main()
