"""OECD integrity source values: fractions, explicit missingness and decimal values."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/collect_institutional_decay_pii.py"

def load():
    spec=importlib.util.spec_from_file_location("oecd_pii",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PIIRawValueTests(unittest.TestCase):
    def setUp(self):
        self.normalize=load().normalize
        self.series={"REF_AREA":"GBR","MEASURE":"PII_3119","FREQ":"A","UNIT_MEASURE":"PO"}

    def test_fraction_not_missing_or_decimally_imputed(self):
        d=self.normalize({"TIME_PERIOD":"2025","OBS_VALUE":"3/7","CRITERIA":"_T"},self.series)
        self.assertEqual(d["valueKind"],"reported_fraction")
        self.assertEqual((d["reportedNumerator"],d["reportedDenominator"]),(3,7))
        self.assertIsNone(d["value"])
        self.assertEqual(d["rawObservedValue"],"3/7")

    def test_zero_fraction_is_observed(self):
        d=self.normalize({"TIME_PERIOD":"2025","OBS_VALUE":"0/12"},self.series)
        self.assertEqual(d["valueKind"],"reported_fraction")
        self.assertEqual(d["reportedNumerator"],0)
        self.assertEqual(d["reportedDenominator"],12)
        self.assertIsNone(d["value"])

    def test_pending_is_missing_and_not_zero(self):
        d=self.normalize({"TIME_PERIOD":"2025","OBS_VALUE":"Data pending"},self.series)
        self.assertEqual(d["valueKind"],"source_missing")
        self.assertIsNone(d["value"])
        self.assertIsNone(d["reportedNumerator"])

    def test_decimal_percentage_kept_without_assumed_unit_conversion(self):
        d=self.normalize({"TIME_PERIOD":"2023","OBS_VALUE":"66.7"},self.series)
        self.assertEqual(d["valueKind"],"numeric")
        self.assertAlmostEqual(d["value"],66.7)
        self.assertIsNone(d["reportedDenominator"])

    def test_invalid_fraction_rejected(self):
        with self.assertRaises(ValueError):
            self.normalize({"TIME_PERIOD":"2025","OBS_VALUE":"5/0"},self.series)
        with self.assertRaises(ValueError):
            self.normalize({"TIME_PERIOD":"2025","OBS_VALUE":"8/7"},self.series)

if __name__=="__main__":
    unittest.main()
