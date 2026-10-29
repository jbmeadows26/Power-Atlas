"""Synthetic estimator architecture checks: NOT empirical election findings."""
import copy
import unittest

from scripts.estimate_electoral_twfe import (
    generate_synthetic, fit_twfe, build_real_panel,
)

class TWFEArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.synthetic=generate_synthetic()
        cls.fit=fit_twfe(cls.synthetic,source_kind="synthetic_architecture_test")

    def test_correct_panel_layout(self):
        self.assertEqual(self.fit["sourceObservations"],650)
        self.assertEqual(self.fit["states"],50)
        self.assertEqual(self.fit["fiscalYears"],13)
        self.assertEqual(len({(r["state"],r["year"]) for r in self.synthetic}),650)

    def test_recovers_known_injected_synthetic_effects(self):
        # True synthetic data-generating coefficients are -1.50 and -0.70 pp.
        effects=self.fit["effects"]
        self.assertAlmostEqual(effects["electionFiscalYear"]["estimatePercentagePoints"],-1.50,delta=0.12)
        self.assertAlmostEqual(effects["preElectionFiscalYear"]["estimatePercentagePoints"],-0.70,delta=0.12)
        self.assertEqual(self.fit["causalIdentification"],"NOT_ESTABLISHED")
        self.assertIn("SIMULATION",self.fit["disclosure"])

    def test_refuse_to_disguise_synthetic_as_verified_empirical_data(self):
        with self.assertRaisesRegex(ValueError,"unlabeled"):
            fit_twfe(self.synthetic,source_kind="claimed_causal_proof")

    def test_missing_real_election_and_controls_file_refuses_to_estimate(self):
        with self.assertRaisesRegex(ValueError,"NO_ELECTION_CONTROLS"):
            build_real_panel("/tmp/this-file-does-not-exist-atlas-covariates.json")

    def test_duplicate_rows_are_rejected(self):
        rows=copy.deepcopy(self.synthetic)
        rows[0]=copy.deepcopy(rows[1])
        with self.assertRaisesRegex(ValueError,"Duplicate panel"):
            fit_twfe(rows,source_kind="synthetic_architecture_test")

    def test_noneconomic_noise_must_not_be_treated_as_zero(self):
        rows=copy.deepcopy(self.synthetic)
        rows[0]["gdpGrowthPriorYear"]=None
        with self.assertRaisesRegex(ValueError,"missing covariates"):
            fit_twfe(rows,source_kind="synthetic_architecture_test")

    def test_exposure_cannot_be_automatically_assumed_for_every_year(self):
        rows=copy.deepcopy(self.synthetic)
        for r in rows:
            r["electionFiscalYear"]=1
            r["preElectionFiscalYear"]=0
        with self.assertRaisesRegex(ValueError,"comparison group"):
            fit_twfe(rows,source_kind="synthetic_architecture_test")

    def test_no_simulated_results_are_published_to_real_feed(self):
        self.assertTrue(self.fit["noSimulatedDataInResearchFeed"])
        self.assertEqual(self.fit["dataProvenance"],"synthetic_architecture_test")


if __name__=="__main__":
    unittest.main()
