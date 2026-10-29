"""Guardrails for published OECD integrity criteria and country selection."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstitutionalDecayIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(
            (ROOT / "data/institutional-decay/integrity-implementation-2025.json").read_text(
                encoding="utf-8"
            )
        )

    def test_schema_and_selection_warning(self):
        self.assertEqual(
            self.doc["schema"], "power-atlas.institutional-decay.integrity-implementation.v1"
        )
        self.assertEqual(self.doc["causalStatus"], "descriptive_noncausal")
        self.assertIn("not_full_country_panel", self.doc["publicationStatus"])
        self.assertIn("Do not merge", self.doc["useRestriction"])

    def test_gap_is_difference_in_criteria_not_corruption_rate(self):
        self.assertIn("not proof", self.doc["interpretation"])
        for row in self.doc["countryCases"] + self.doc["oecdAverages"]:
            with self.subTest(area=row["area"]):
                self.assertTrue(row["source"].startswith("https://"))
                if "regulationPercent" in row:
                    self.assertEqual(
                        row["implementationGapPercentagePoints"],
                        row["regulationPercent"] - row["practicePercent"],
                    )
                    self.assertTrue(0 <= row["regulationPercent"] <= 100)
                    self.assertTrue(0 <= row["practicePercent"] <= 100)

    def test_no_inferred_country_panel(self):
        self.assertEqual(
            {x["code"] for x in self.doc["countryCases"]}, {"POL", "SVK"}
        )
        self.assertEqual(
            {x["id"] for x in self.doc["oecdAverages"]},
            {"oecd-all-areas", "oecd-coi", "oecd-civil-discipline"},
        )


if __name__ == "__main__":
    unittest.main()
