"""OECD country-wave reproducibility tests; no third-party dependencies."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "analyze_institutional_decay.py"


def load_analysis():
    spec = importlib.util.spec_from_file_location("analyze_institutional_decay", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstitutionalDecayCountryPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = load_analysis().build_summary()

    def test_sample_and_availability_are_not_overclaimed(self):
        counts = self.summary["counts"]
        self.assertEqual(counts["countriesRepresented"], 39)
        self.assertEqual(counts["oecdCountryRowsIn2025"], 33)
        self.assertEqual(counts["accessionCountryRowsIn2025"], 5)
        self.assertEqual(counts["pairedGovernmentTrustCountries"], 28)
        self.assertTrue(counts["missing2023ColombiaGovernmentTrust"])
        self.assertTrue(counts["missing2025CzechiaGovernmentTrust"])
        self.assertTrue(counts["usaNotInSurvey"])

    def test_paired_statistics_reproducible(self):
        stat = self.summary["nationalGovernmentTrustPaired"]
        self.assertEqual(stat["mean2023Percent"], 40.5)
        self.assertEqual(stat["mean2025Percent"], 41.25)
        self.assertEqual(stat["meanChangePercentagePoints"], 0.75)
        self.assertEqual(stat["medianChangePercentagePoints"], 0)
        self.assertEqual(
            stat["increased"] + stat["decreased"] + stat["unchangedAtRoundingPrecision"], 28
        )
        self.assertEqual(
            (stat["increased"], stat["decreased"], stat["unchangedAtRoundingPrecision"]),
            (11, 13, 4),
        )

    def test_institutional_gaps_count_same_country_cohort(self):
        gap = self.summary["institutionalGaps2025"]
        self.assertEqual(
            gap["civil_service_minus_national_government"]["countryCount"], 33
        )
        self.assertEqual(
            (gap["civil_service_minus_national_government"]["above"],
             gap["civil_service_minus_national_government"]["below"],
             gap["civil_service_minus_national_government"]["equalAtRoundedPrecision"]),
            (23, 8, 2),
        )
        self.assertEqual(
            (gap["local_government_minus_national_government"]["above"],
             gap["local_government_minus_national_government"]["below"],
             gap["local_government_minus_national_government"]["equalAtRoundedPrecision"]),
            (25, 5, 3),
        )

    def test_no_causality_claim_or_imputation(self):
        self.assertIn("noncausal", self.summary["status"])
        self.assertTrue(any("no ecological causal" in s for s in self.summary["limitations"]))
        self.assertTrue(any("not equivalent" in s for s in self.summary["limitations"]))


if __name__ == "__main__":
    unittest.main()
