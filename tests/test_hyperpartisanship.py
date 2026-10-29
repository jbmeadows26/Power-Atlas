"""Offline validation of Congress-level descriptive results."""
import importlib.util
import json
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("analyze_hyperpartisanship",R/"scripts/analyze_hyperpartisanship.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class TestHyperpartisanship(unittest.TestCase):
    def test_aggregate_and_provenance(self):
        d=mod.calculate()
        self.assertEqual([x["congress"] for x in d["series"]],list(range(100,120)))
        self.assertTrue(all(x["complete_congress"] for x in d["series"][:-1]))
        self.assertFalse(d["series"][-1]["complete_congress"])
        self.assertEqual((d["series"][2]["substantive_laws_pre_election"],d["series"][18]["substantive_laws_pre_election"]),(387,84))
        self.assertEqual((d["series"][2]["cloture_motions_filed"],d["series"][17]["cloture_motions_filed"]),(60,336))
        self.assertEqual(d["cohorts"]["change_mean_substantive_percent"],-44.66)
        self.assertEqual(d["cohorts"]["change_mean_cloture_percent"],222.64)
        self.assertTrue(d["cohorts"]["notCausal"])
        self.assertIn("DIFFERENT cutoff periods",d["comparability"])
        self.assertEqual(json.loads((R/"data/hyperpartisanship/baseline-v1.json").read_text()),d)
