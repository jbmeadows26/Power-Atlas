"""Regression checks for UK parliamentary case and US service evidence, stdlib only."""
import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/institutional-decay/uk-us-accountability-service-2026-10-31.json"

class UKUSAccountabilityServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PATH.read_text(encoding="utf-8"))
        cls.obs = {x["id"]: x for x in cls.doc["observations"]}
        cls.events = {x["id"]: x for x in cls.doc["events"]}

    def test_schema_counts_and_isolation(self):
        d = self.doc
        self.assertEqual(d["schema"], "power-atlas.institutional-decay.accountability-service-cases.v1")
        self.assertEqual(d["causalStatus"], "descriptive_noncausal")
        self.assertIn("not_app_feed", d["publicationStatus"])
        self.assertEqual(len(d["observations"]), 19)
        self.assertEqual(len(d["events"]), 10)
        self.assertEqual(len(d["sourceCatalog"]), 5)
        self.assertEqual({x["geography"] for x in d["observations"]}, {"United Kingdom", "United States"})
        self.assertIn("Do not merge", d["methodology"]["productionGuardrail"])

    def test_sources_licenses_and_non_invented_fields(self):
        d = self.doc
        urls = {s["url"] for s in d["sourceCatalog"]}
        self.assertEqual(len(urls), 5)
        self.assertEqual(len(self.obs), len(d["observations"]))
        self.assertEqual(len(self.events), len(d["events"]))
        for s in d["sourceCatalog"]:
            self.assertEqual(urlparse(s["url"]).scheme, "https")
            self.assertEqual(urlparse(s["licenseEvidence"]).scheme, "https")
            self.assertTrue(s["license"] and s["attribution"] and s["published"])
            self.assertLessEqual(date.fromisoformat(s["published"]), date(2026, 10, 31))
        for row in d["observations"] + d["events"]:
            self.assertIn(row["source"], urls)
            self.assertTrue(row["id"] and row["geography"])
        for row in d["observations"]:
            self.assertTrue(row["population"] and row["denominator"] and row["note"])
            self.assertEqual(row["claimType"], "descriptive_observation")
            self.assertIsInstance(row["value"], (int, float))
            self.assertGreaterEqual(row["value"], 0)
            if row["unit"] == "percent":
                self.assertLessEqual(row["value"], 100)
            if "approximate" in row["unit"]:
                self.assertEqual(row["precision"], "approximate")

    def test_case_timelines_and_distinct_outcomes(self):
        d = self.doc
        ds = [date.fromisoformat(e["eventDate"]) for e in d["events"]]
        self.assertEqual(ds, sorted(ds))
        self.assertTrue(all(x <= date(2026, 10, 31) for x in ds))
        self.assertTrue(all(e["causalLinkToTrust"] == "not_established" for e in d["events"]))
        self.assertEqual(self.events["uk-paterson-house-amended-motion-2021"]["legalStatus"], "sanction_not_approved")
        self.assertEqual(self.events["uk-paterson-resignation-announced-2021"]["legalStatus"], "resigned_before_final_sanction_approval")
        self.assertEqual(self.events["uk-bridgen-suspension-agreed-2023"]["legalStatus"], "parliamentary_sanction_approved")
        self.assertEqual(self.events["uk-ferrier-suspension-agreed-2023"]["legalStatus"], "parliamentary_sanction_approved")
        self.assertEqual(self.obs["uk-paterson-recommended-suspension-2021"]["value"], 30)
        self.assertEqual(self.obs["uk-bridgen-house-approved-suspension-2023"]["value"], 5)
        self.assertEqual(self.obs["uk-ferrier-house-approved-suspension-2023"]["value"], 30)
        self.assertNotEqual(self.obs["uk-paterson-recommended-suspension-2021"]["evidenceStatus"],
                            self.obs["uk-ferrier-house-approved-suspension-2023"]["evidenceStatus"])

    def test_us_agency_periods_and_denominators(self):
        o = self.obs
        expected = {
            "us-ssa-initial-disability-processing-fy2022": 184,
            "us-ssa-initial-disability-processing-fy2024": 231,
            "us-ssa-pending-initial-claims-fy2022": 941000,
            "us-ssa-pending-initial-claims-fy2024": 1200000,
            "us-ssa-pending-appeals-fy2022": 347000,
            "us-ssa-pending-appeals-fy2024": 262000,
            "us-va-backlog-dec2024": 244000,
            "us-va-pact-avg-processing-aug2023": 155,
            "us-va-pact-avg-processing-nov2024": 168,
            "us-va-pact-timely-sep2023": 47,
            "us-va-pact-timely-nov2024": 37,
            "us-va-nonpact-avg-processing-nov2024": 129,
            "us-va-nonpact-timely-nov2024": 59,
            "us-va-all-initial-avg-processing-nov2024": 139,
            "us-va-hearing-appeals-avg-jun2024": 1089,
            "us-va-hearing-appeals-goal-jun2024": 730,
        }
        for key, val in expected.items():
            self.assertEqual(o[key]["value"], val)
        self.assertEqual(o["us-va-hearing-appeals-goal-jun2024"]["evidenceStatus"], "official_policy_target")
        self.assertNotEqual(o["us-va-pact-timely-sep2023"]["period"], o["us-va-pact-avg-processing-aug2023"]["period"])
        self.assertIn("distinct", o["us-ssa-pending-appeals-fy2024"]["denominator"])
        self.assertEqual(o["us-va-backlog-dec2024"]["precision"], "approximate")

if __name__ == "__main__":
    unittest.main()
