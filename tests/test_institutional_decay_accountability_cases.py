"""Guardrails for additive, source-attributed institutional-decay cases (no third-party dependencies)."""
import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "institutional-decay" / "accountability-service-cases-2026-10-30.json"

class AccountabilityServiceCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PATH.read_text(encoding="utf-8"))
        cls.obs = {o["id"]: o for o in cls.doc["observations"]}

    def test_schema_and_isolation(self):
        d = self.doc
        self.assertEqual(d["schema"], "power-atlas.institutional-decay.accountability-service-cases.v1")
        self.assertEqual(d["causalStatus"], "descriptive_noncausal")
        self.assertIn("not_app_feed", d["publicationStatus"])
        self.assertIn("Do not merge", d["methodology"]["productionGuardrail"])
        self.assertEqual({o["geography"] for o in d["observations"]}, {"Australia", "Canada"})
        self.assertEqual(len(d["observations"]), 14)
        self.assertEqual(len(d["events"]), 7)

    def test_provenance_and_licensing(self):
        d = self.doc
        source_urls = {s["url"] for s in d["sourceCatalog"]}
        self.assertEqual(len(source_urls), 4)
        self.assertEqual(len({o["id"] for o in d["observations"]}), len(d["observations"]))
        self.assertEqual(len({e["id"] for e in d["events"]}), len(d["events"]))
        for s in d["sourceCatalog"]:
            self.assertEqual(urlparse(s["url"]).scheme, "https")
            self.assertEqual(urlparse(s["licenseEvidence"]).scheme, "https")
            self.assertTrue(s["license"] and s["attribution"])
        for row in d["observations"] + d["events"]:
            self.assertIn(row["source"], source_urls)
            self.assertTrue(row["id"] and row["geography"])
        for o in d["observations"]:
            self.assertTrue(o["denominator"] and o["population"] and o["note"])
            self.assertEqual(o["claimType"], "descriptive_observation")
            self.assertIsInstance(o["value"], (int, float))
            self.assertGreaterEqual(o["value"], 0)

    def test_dated_case_timeline_and_legal_status(self):
        d = self.doc
        dates = [date.fromisoformat(e["eventDate"]) for e in d["events"]]
        self.assertEqual(dates, sorted(dates))
        self.assertTrue(all(x <= date(2026, 10, 30) for x in dates))
        self.assertTrue(all(e["causalLinkToTrust"] == "not_established" for e in d["events"]))
        self.assertTrue(all(e["legalStatus"] for e in d["events"]))
        self.assertEqual(self.obs["aus-robodebt-referrals-2024"]["value"], 16)
        self.assertEqual(self.obs["aus-robodebt-final-breach-persons-2024"]["value"], 12)
        self.assertEqual(self.obs["aus-robodebt-final-breach-instances-2024"]["value"], 97)
        self.assertEqual(self.obs["aus-robodebt-current-employee-sanctions-2024"]["value"], 4)
        self.assertIn("not automatically", self.doc["events"][4]["disposition"])
        self.assertEqual(self.obs["aus-robodebt-commissioner-allegations-reviewed-2025"]["value"], 10)
        self.assertEqual(self.obs["aus-robodebt-commissioner-allegations-substantiated-2025"]["value"], 0)
        self.assertEqual(self.obs["aus-robodebt-commissioner-allegations-substantiated-2025"]["evidenceStatus"], "official_investigation_not_substantiated")

    def test_canada_audit_denominators_and_perception_selection(self):
        o = self.obs
        self.assertEqual(o["can-cra-timely-calls-fy2024"]["value"], 49)
        self.assertEqual(o["can-cra-timely-calls-fy2025"]["value"], 18)
        self.assertEqual(o["can-cra-timely-calls-target-fy2025"]["value"], 65)
        self.assertEqual(o["can-cra-timely-calls-target-fy2025"]["evidenceStatus"], "official_policy_target")
        self.assertEqual(o["can-cra-average-agent-wait-fy2025"]["value"], 31)
        self.assertEqual(o["can-cra-deflected-calls-fy2025"]["value"], 8630000)
        self.assertEqual(o["can-cra-general-individual-tax-accuracy-2025"]["value"], 17)
        self.assertIn("subgroup n not given", o["can-cra-general-individual-tax-accuracy-2025"]["denominator"])
        self.assertEqual(o["can-cra-reported-satisfaction-fy2025"]["value"], 77)
        self.assertIn("less than 2%", o["can-cra-reported-satisfaction-fy2025"]["denominator"])
        self.assertIn("not unique", o["can-cra-deflected-calls-fy2025"]["denominator"])

if __name__ == "__main__":
    unittest.main()
