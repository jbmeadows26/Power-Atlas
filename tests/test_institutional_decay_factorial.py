"""Pre-registered factorial model integrity tests: no fictional respondents."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT / "scripts/institutional_decay_factorial.py"


def load():
    spec=importlib.util.spec_from_file_location("id_factorial",PATH)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FactorialAnalysisTests(unittest.TestCase):
    def test_saturated_ols_and_hc3(self):
        # Deliberately synthetic fixture: 20 respondents per cell, not observed data.
        rows=[]
        means={(0,0):4.0,(1,0):3.0,(0,1):3.0,(1,1):1.5}
        for (a,b),mu in means.items():
            for i in range(20):
                val=mu+(0.5 if i%2 else -0.5)
                rows.append({"impunity":str(a),"high_burden":str(b),"trust_score":str(val)})
        d=load().analyze(rows)
        coeff=d["olsCoefficients"]
        self.assertEqual(d["completeTotal"],80)
        self.assertAlmostEqual(coeff["intercept"],4)
        self.assertAlmostEqual(coeff["impunityMainEffect"],-1)
        self.assertAlmostEqual(coeff["burdenMainEffect"],-1)
        self.assertAlmostEqual(coeff["compoundingInteraction"],-0.5)
        # HC3 exact saturated-model variance = sum over four cells
        # of sum((y - cellmean)^2)/(n-1)^2.
        self.assertAlmostEqual(d["hc3InteractionSE"],(20/19**2)**0.5)
        self.assertLess(d["interaction95PctNormalCI"][1],0)
        self.assertEqual(d["plannedSample"],3000)

    def test_incomplete_outcomes_are_retained_as_assignment_counts(self):
        rows=[{"impunity":str(a),"high_burden":str(b),"trust_score":"4"}
              for a in (0,1) for b in (0,1) for _ in range(12)]
        rows.append({"impunity":"1","high_burden":"1","trust_score":""})
        out=load().analyze(rows)
        self.assertEqual(out["assignedTotal"],49)
        self.assertEqual(out["completeTotal"],48)
        self.assertEqual(out["cells"]["11"]["missing"],1)
        self.assertIsNone(out["interactionTwoSidedNormalP"])

    def test_rejects_bad_values_and_unpopulated_experiment(self):
        f=load()
        with self.assertRaises(ValueError):
            f.analyze([])
        with self.assertRaises(ValueError):
            f.analyze([{"impunity":"5","high_burden":"1","trust_score":"4"}])
        with self.assertRaises(ValueError):
            f.analyze([{"impunity":"1","high_burden":"0","trust_score":"8"}])

if __name__=="__main__":
    unittest.main()
