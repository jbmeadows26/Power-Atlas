"""Science gate tests: four factorial arms and three genuine OECD aggregate waves."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VIGNETTES=ROOT/"research/institutional-decay/field-instrument-v1.json"
THREE=ROOT/"data/institutional-decay/oecd-trust-three-wave-cohort.json"


class InstitutionalDecayResearchGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=json.loads(VIGNETTES.read_text(encoding="utf-8"))
        cls.o=json.loads(THREE.read_text(encoding="utf-8"))

    def test_four_independent_conditions_and_balanced_target(self):
        v=self.v
        self.assertEqual(v["plannedN"],3000)
        self.assertEqual(v["targetPerArm"],750)
        arms=v["arms"]
        self.assertEqual({a["cell"] for a in arms},{"00","01","10","11"})
        self.assertEqual(sum(v["allocation"]["targetAllocation"].values()),3000)
        for arm in arms:
            a,b=int(arm["cell"][0]),int(arm["cell"][1])
            self.assertEqual((arm["impunity"],arm["high_burden"]),(a,b))
            self.assertTrue(arm["script"].startswith(v["vignetteCommon"]))
            self.assertIn(v["factorClauses"]["accountability"][str(a)],arm["script"])
            self.assertIn(v["factorClauses"]["administrativeBurden"][str(b)],arm["script"])
            self.assertNotIn(v["factorClauses"]["accountability"][str(1-a)],arm["script"])
            self.assertNotIn(v["factorClauses"]["administrativeBurden"][str(1-b)],arm["script"])

    def test_ethics_and_sampling_not_spoofed(self):
        v=self.v
        self.assertEqual(v["status"],"ready_for_ethics_and_pilot_review_not_fielded")
        self.assertFalse(v["ethicsGate"]["completed"])
        self.assertFalse(v["ethicsGate"]["consentFinalized"])
        self.assertEqual(v["ethicsGate"]["recruitedN"],0)
        self.assertIn("quota",v["allocation"]["recruitment"])
        self.assertTrue(v["analysis"]["preregistrationRequiredBeforeFieldwork"])
        self.assertEqual(v["primaryOutcome"]["range"],[1,7])

    def test_three_wave_aggregate_cannot_masquerade_as_panel(self):
        o=self.o
        self.assertEqual(o["nCountries"],18)
        self.assertEqual([(r["year"],r["value"]) for r in o["data"]],
                         [(2021,43.2),(2023,40.8),(2025,42.7)])
        self.assertFalse(o["validation"]["arellanoBondEstimable"])
        self.assertEqual(o["validation"]["nCountrySeriesAvailableInThisFile"],0)
        self.assertEqual(o["causalStatus"],"descriptive_only_not_dynamic_evidence")


if __name__=="__main__":
    unittest.main()
