"""Validation guards for the institutional decay source extract.

Run via: python -m unittest discover -s tests -p 'test_*.py' -v
No external dependencies or network access are required.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "institutional-decay" / "evidence-v1.json"


class InstitutionalDecayEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.rows = cls.doc["observations"]
        cls.events = cls.doc["events"]

    def test_baseline_has_explicit_not_causal_scope(self):
        self.assertEqual(self.doc["schema"], "power-atlas.institutional-decay.evidence.v1")
        self.assertIn("not_harmonized_panel", self.doc["publicationStatus"])
        self.assertIn("None of these", self.doc["causality"])

    def test_observations_have_unique_ids_and_source_provenance(self):
        ids = [row["id"] for row in self.rows]
        self.assertGreater(len(ids), 0)
        self.assertEqual(len(ids), len(set(ids)))
        for row in self.rows:
            with self.subTest(id=row["id"]):
                for key in ("id", "dimension", "geography", "period", "unit", "measure", "population", "source", "note", "claimType"):
                    self.assertTrue(row.get(key), key)
                self.assertTrue(row["source"].startswith("https://"))
                self.assertTrue(isinstance(row["value"], (int, float)))
                self.assertNotIsInstance(row["value"], bool)
                self.assertEqual(row["claimType"], "descriptive_observation")
                if row["unit"] in ("percent", "approximate_percent"):
                    self.assertTrue(0 <= row["value"] <= 100)

    def test_events_dont_infer_causality(self):
        ids = [event["id"] for event in self.events]
        self.assertEqual(len(ids), len(set(ids)))
        for event in self.events:
            with self.subTest(id=event["id"]):
                self.assertTrue(event["source"].startswith("https://"))
                self.assertTrue(re.match(r"^\d{4}-\d{2}(?:-\d{2})?$", event["eventDate"]))
                inferred = [v for k, v in event.items() if k.lower().startswith("causallink")]
                self.assertTrue(inferred)
                self.assertTrue(all(v == "not_established" for v in inferred))

    def test_rounded_irs_correspondence_is_internally_consistent(self):
        by_id = {row["id"]: row for row in self.rows}
        inventory = by_id["gao-irs-correspondence-fy2025"]["value"]
        overage = by_id["gao-irs-overage-correspondence-fy2025"]["value"]
        reported_pct = by_id["gao-irs-overage-share-fy2025"]["value"]
        self.assertLess(abs(100 * overage / inventory - reported_pct), 1)

    def test_citation_and_dataset_catalog(self):
        self.assertGreaterEqual(len(self.doc["sourceCatalog"]), 6)
        self.assertEqual(len({row["id"] for row in self.doc["sourceCatalog"]}), len(self.doc["sourceCatalog"]))
        urls = {c["url"] for c in self.doc["sourceCatalog"]}
        for row in self.rows:
            self.assertIn(row["source"], urls)
        for event in self.events:
            self.assertIn(event["source"], urls)

    def test_all_hypotheses_marked_untested(self):
        self.assertTrue(self.doc["researchQuestions"])
        for question in self.doc["researchQuestions"]:
            self.assertEqual(question["status"], "not_tested")


if __name__ == "__main__":
    unittest.main()
