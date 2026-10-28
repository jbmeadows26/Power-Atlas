"""Offline regression checks for source field mapping and collector startup."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectorChecks(unittest.TestCase):
    def test_fec_totals_module_imports_without_credentials(self):
        # Regression: MAX_COMMITTEES used KEY before KEY was initialized.
        mod = load_module("fec_totals_test", "collect_fec_totals.py")
        self.assertIn(mod.KEY, ("DEMO_KEY", mod.KEY))
        self.assertIn(mod.MAX_COMMITTEES, (2, 7))
        self.assertEqual(mod.MAX_COMMITTEES, 2 if mod.KEY == "DEMO_KEY" else 7)

    def test_fec_totals_normalization_requires_exact_cycle(self):
        mod = load_module("fec_totals_norm", "collect_fec_totals.py")
        row = {"committee_id": "C00630707", "cycle": 2024, "receipts": 123.45}
        self.assertIsNone(mod.normalize(row, "C00630707", 2026))
        result = mod.normalize(row, "C00630707", 2024)
        self.assertEqual(result["receipts"], 123.45)
        self.assertEqual(result["committeeId"], "C00630707")

    def test_senate_lobbying_activity_uses_official_field(self):
        mod = load_module("lda_test", "collect_lda.py")
        self.assertEqual(
            mod.matching_issue({"lobbying_activities": [
                {"specific_lobbying_issues": "Federal redistricting policy and voting rights."}
            ]}),
            "Federal redistricting policy and voting rights."
        )
        self.assertEqual(
            mod.matching_issue({"lobbying_activities": [
                {"specific_issues": "Congressional district legislation"}
            ]}),
            "Congressional district legislation"
        )
        self.assertEqual(
            mod.matching_issue({"lobbying_activities": [
                {"specific_lobbying_issues": "Unrelated infrastructure policy"}
            ]}),
            ""
        )


if __name__ == "__main__":
    unittest.main()
