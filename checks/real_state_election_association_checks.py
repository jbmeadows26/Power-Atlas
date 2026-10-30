"""Live, already source-linked observational models: regression output must stay noncausal."""
import json
import unittest
from scripts.analyze_state_election_association import analyze,source_join

class RealWorldObservationalDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=analyze()
        cls.rows,*_=source_join()

    def test_complete_650_real_state_years_and_sources(self):
        self.assertEqual(len(self.rows),650)
        self.assertEqual(self.data["sourceRecordCount"],650)
        self.assertEqual(len({(r["state"],r["year"]) for r in self.rows}),650)
        self.assertEqual(len({r["state"] for r in self.rows}),50)

    def test_election_and_pre_election_timing_do_not_overlap(self):
        self.assertTrue(all(not (r["electionFiscalYear"] and r["preElectionFiscalYear"])
                            for r in self.rows))
        self.assertTrue(any(r["electionFiscalYear"] for r in self.rows))
        self.assertTrue(any(r["preElectionFiscalYear"] for r in self.rows))

    def test_numerical_results_are_not_called_causal(self):
        self.assertIsNone(self.data["causalEffect"])
        self.assertIsNone(self.data["politicalIntentInference"])
        self.assertEqual(self.data["status"],"observational_diagnostics_not_verified_causal_effect")
        for m in self.data["models"]:
            self.assertIn("OBSERVATIONAL_ASSOCIATION_ONLY",m["interpretation"])
            for v in m["coefficients"].values():
                self.assertIsNone(v["causalEffect"])

    def test_six_predeclared_sensitivity_specifications(self):
        names={m["name"] for m in self.data["models"]}
        self.assertEqual(names,{
            "all_fy_unadjusted","all_fy_lagged_macro",
            "all_fy_macro_plus_contemporaneous_transfers_sensitivity",
            "pre_2022_unadjusted","pre_2022_lagged_macro",
            "exclude_pandemic_fy2020_2021_macro",
        })
        self.assertEqual(next(m for m in self.data["models"]
                         if m["name"]=="pre_2022_lagged_macro")["nObservedStateYears"],500)
        self.assertEqual(next(m for m in self.data["models"]
                         if m["name"]=="exclude_pandemic_fy2020_2021_macro")["nObservedStateYears"],550)

    def test_contemporaneous_grants_sensitivity_not_presented_as_controlled_cause(self):
        transfers=[m for m in self.data["models"] if m["hasPotentiallyPostTreatmentFederalTransferShare"]]
        self.assertEqual(len(transfers),1)
        self.assertIn("contemporaneous",transfers[0]["name"])

if __name__=="__main__":
    unittest.main()
