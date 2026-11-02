"""Institutional-decay source, status, date and denominator regression checks (2026-11-02)."""
import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PATH = Path(__file__).resolve().parents[1] / "data/institutional-decay/municipal-benefits-horizon-evidence-2026-11-02.json"

class MunicipalBenefitsHorizonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))
        cls.obs = {r["id"]: r for r in cls.data["observations"]}
        cls.events = {r["id"]: r for r in cls.data["events"]}

    def test_schema_unique_ids_and_isolation(self):
        d = self.data
        self.assertEqual(d["schema"], "power-atlas.institutional-decay.accountability-service-cases.v1")
        self.assertEqual(d["asOf"], "2026-11-02")
        self.assertEqual(d["causalStatus"], "descriptive_noncausal")
        self.assertIn("not_app_feed", d["publicationStatus"])
        self.assertEqual((len(d["sourceCatalog"]), len(d["observations"]), len(d["events"])), (12, 28, 10))
        self.assertEqual(len(self.obs), 28)
        self.assertEqual(len(self.events), 10)
        self.assertEqual({r["geography"] for r in d["observations"]},
                         {"South Africa", "Netherlands", "United Kingdom"})
        self.assertIn("No changes", d["methodology"]["productionGuardrail"])

    def test_sources_dates_precision_and_status(self):
        d = self.data
        urls = {s["url"] for s in d["sourceCatalog"]}
        self.assertEqual(len(urls), 12)
        for s in d["sourceCatalog"]:
            self.assertEqual(urlparse(s["url"]).scheme, "https")
            self.assertLessEqual(date.fromisoformat(s["published"]), date(2026, 11, 2))
            self.assertTrue(s["license"] and s["licenseEvidence"] and s["attribution"])
            if s["licenseEvidence"] != "not_verified":
                self.assertEqual(urlparse(s["licenseEvidence"]).scheme, "https")
        for row in d["observations"]:
            self.assertIn(row["source"], urls)
            self.assertTrue(row["denominator"] and row["population"] and row["note"])
            self.assertEqual(row["claimType"], "descriptive_observation")
            self.assertTrue(row["evidenceStatus"])
            self.assertIsInstance(row["value"], (int, float))
            self.assertGreaterEqual(row["value"], 0)
            if row["unit"] == "percent":
                self.assertLessEqual(row["value"], 100)
            if row["unit"].endswith("_lower_bound_exclusive"):
                self.assertEqual(row["precision"], "lower_bound_exclusive")
        dates = [date.fromisoformat(e["eventDate"]) for e in d["events"]]
        self.assertEqual(dates, sorted(dates))
        for event in d["events"]:
            self.assertIn(event["source"], urls)
            self.assertEqual(event["causalLinkToTrust"], "not_established")
            self.assertTrue(event["disposition"] and event["legalStatus"])

    def test_audit_accounting_and_denominator_separation(self):
        o = self.obs
        counts = ["sa-municipal-clean-audits-2023-24",
                  "sa-municipal-unqualified-findings-2023-24",
                  "sa-municipal-qualified-2023-24",
                  "sa-municipal-adverse-2023-24",
                  "sa-municipal-disclaimed-2023-24",
                  "sa-municipal-outstanding-2023-24"]
        self.assertEqual(sum(o[k]["value"] for k in counts), 257)
        self.assertEqual(o["sa-municipal-audits-completed-2023-24"]["value"], 247)
        self.assertEqual(o["sa-municipal-outstanding-2023-24"]["value"], 10)
        self.assertEqual(o["sa-municipal-compliance-findings-2023-24"]["value"], 206)
        self.assertIn("247", o["sa-municipal-compliance-findings-2023-24"]["denominator"])
        self.assertEqual(o["sa-municipal-performance-report-findings-2023-24"]["value"], 119)
        self.assertIn("247", o["sa-municipal-performance-report-findings-2023-24"]["denominator"])
        self.assertEqual(o["sa-municipal-improved-since-2020-21"]["value"], 59)
        self.assertEqual(o["sa-municipal-regressed-since-2020-21"]["value"], 40)

    def test_dutch_redress_precision_and_distinct_dispositions(self):
        o = self.obs
        self.assertEqual(o["nl-potential-benefits-claimants-2025-07"]["value"], 69400)
        self.assertEqual(o["nl-confirmed-affected-parents-2025-07"]["value"], 42000)
        self.assertEqual(o["nl-integrated-assessments-completed-2025-07"]["value"], 64000)
        self.assertEqual(o["nl-integrated-assessments-completed-2025-07"]["precision"], "lower_bound_exclusive")
        self.assertEqual(o["nl-integrated-assessment-completion-share-2025-07"]["value"], 92.5)
        self.assertIn("not independently reconciled", o["nl-integrated-assessment-completion-share-2025-07"]["denominator"])
        self.assertEqual(o["nl-children-identified-care-placement-2023"]["value"], 1819)
        self.assertEqual(o["nl-parents-identified-care-placement-2023"]["value"], 1168)
        self.assertIn("not_acquittal", self.events["nl-childcare-prosecution-declined-2021"]["legalStatus"])
        self.assertIn("not_criminal_conviction", self.events["nl-childcare-cabinet-resignation-2021"]["legalStatus"])

    def test_horizon_subset_and_inquiry_recommendations(self):
        o = self.obs
        self.assertEqual(o["uk-horizon-redress-paid-2025-06"]["value"], 1039)
        self.assertEqual(o["uk-horizon-convictions-redress-subset-2025-06"]["value"], 245)
        self.assertIn("INCLUDED", o["uk-horizon-convictions-redress-subset-2025-06"]["denominator"])
        self.assertEqual(o["uk-horizon-redress-recipients-2025-06"]["precision"], "lower_bound_exclusive")
        self.assertEqual(o["uk-horizon-inquiry-recommendations-2025"]["value"], 19)
        self.assertIn("not a criminal conviction", self.events["uk-horizon-inquiry-volume1-2025"]["disposition"])

if __name__ == "__main__":
    unittest.main()
