"""Independent stdlib checks for Nov 1 official oversight and passport service extracts."""
import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PATH = Path(__file__).resolve().parents[1] / "data/institutional-decay/ombudsman-passport-evidence-2026-11-01.json"

class OmbudsmanPassportEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))
        cls.obs = {r["id"]: r for r in cls.data["observations"]}
        cls.events = {r["id"]: r for r in cls.data["events"]}

    def test_schema_counts_uniqueness_and_isolation(self):
        d = self.data
        self.assertEqual(d["schema"], "power-atlas.institutional-decay.accountability-service-cases.v1")
        self.assertEqual(d["asOf"], "2026-11-01")
        self.assertEqual(d["causalStatus"], "descriptive_noncausal")
        self.assertIn("not_app_feed", d["publicationStatus"])
        self.assertEqual((len(d["sourceCatalog"]), len(d["observations"]), len(d["events"])), (8, 19, 8))
        self.assertEqual(len(self.obs), 19)
        self.assertEqual(len(self.events), 8)
        self.assertEqual({r["geography"] for r in d["observations"]}, {"Ireland", "New Zealand", "United States"})
        self.assertIn("No modifications", d["methodology"]["productionGuardrail"])

    def test_provenance_license_date_and_denominator(self):
        d = self.data
        urls = {s["url"] for s in d["sourceCatalog"]}
        self.assertEqual(len(urls), 8)
        for s in d["sourceCatalog"]:
            self.assertEqual(urlparse(s["url"]).scheme, "https")
            self.assertTrue(s["license"] and s["licenseEvidence"] and s["attribution"])
            self.assertLessEqual(date.fromisoformat(s["published"]), date(2026, 11, 1))
            if s["id"].startswith("nz"):
                self.assertEqual(s["licenseEvidence"], "not_verified")
            else:
                self.assertEqual(urlparse(s["licenseEvidence"]).scheme, "https")
        for row in d["observations"]:
            self.assertIn(row["source"], urls)
            self.assertTrue(row["denominator"] and row["population"] and row["note"])
            self.assertEqual(row["claimType"], "descriptive_observation")
            self.assertIsInstance(row["value"], (int, float))
            self.assertGreaterEqual(row["value"], 0)
            self.assertTrue(row["evidenceStatus"])
            if row["unit"] == "percent":
                self.assertLessEqual(row["value"], 100)
        dates = [date.fromisoformat(e["eventDate"]) for e in d["events"]]
        self.assertEqual(dates, sorted(dates))
        for e in d["events"]:
            self.assertIn(e["source"], urls)
            self.assertEqual(e["causalLinkToTrust"], "not_established")

    def test_exact_claims_and_non_equivalent_denominators(self):
        o = self.obs
        expected = {
            "ie-ombudsman-complaints-received-2024": 4778,
            "ie-ombudsman-complaints-received-2025": 5297,
            "ie-ombudsman-complaints-investigated-2025": 4996,
            "ie-ombudsman-local-authority-complaints-2025": 1793,
            "ie-ombudsman-complaints-3months-2024": 3722,
            "ie-ombudsman-complaints-6months-2024": 4329,
            "ie-ombudsman-upheld-share-2024": 27,
            "ie-case-pup-recovery-cancelled-2024": 26000,
            "ie-case-carer-arrears-awarded-2024": 6078,
            "nz-ombudsman-complaints-completed-2025": 8163,
            "nz-ombudsman-ombudsmen-act-received-2025": 5269,
            "nz-ombudsman-official-info-received-2025": 2554,
            "nz-ombudsman-clearance-rate-2025": 104,
            "nz-ombudsman-protected-disclosures-completed-2025": 278,
            "us-passport-call-wait-june-2023": 45,
            "us-passport-call-wait-june-2024": 1,
            "us-passport-agent-staff-fy2020": 500,
            "us-passport-agent-staff-fy2024": 1600,
            "us-passport-calls-answered-fy2024": 4600000,
        }
        for key, value in expected.items():
            self.assertEqual(o[key]["value"], value, key)
        self.assertEqual(o["us-passport-call-wait-june-2024"]["precision"], "upper_bound_exclusive")
        self.assertEqual(o["us-passport-call-wait-june-2024"]["unit"], "minutes_upper_bound_exclusive")
        self.assertEqual(o["ie-ombudsman-upheld-share-2024"]["unit"], "percent")
        self.assertNotEqual(o["ie-ombudsman-upheld-share-2024"]["denominator"],
                            o["ie-ombudsman-complaints-received-2024"]["denominator"])
        self.assertNotEqual(o["nz-ombudsman-clearance-rate-2025"]["unit"], "percent")
        self.assertEqual(self.events["nz-education-oia-investigation-notified"]["legalStatus"],
                         "formal_investigation_not_adjudicated")
        self.assertIn("not criminal", self.events["ie-pup-ombudsman-case-published-2024"]["legalStatus"])

if __name__ == "__main__":
    unittest.main()
