"""Offline source completeness and endogeneity tests for BEA/BLS/Census controls."""
import unittest
from unittest.mock import patch
from scripts import collect_state_economic_controls as econ

class EconomicControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_gdp={(state,f"{y}-01-01"):1000.0*(1.02**(y-2000))
                       for state in econ.STATES for y in range(2008,2024)}
        cls.fake_unemp={(state,f"{y}-{m:02d}-01"):4.0
                         for state in econ.STATES for y in range(2009,2024)
                         for m in range(1,13)}
        cls.rev={(state,y,code):(100000 if code=="SF0002" else 25000)
                 for state in econ.STATES for y in range(2012,2025)
                 for code in econ.REVENUE_CODES}

    def run_synthetic_source_mocks(self, rev=None,gdp=None):
        with patch.object(econ,"load_fred",return_value=(
             {"realGDP":gdp or self.fake_gdp,"unemployment":self.fake_unemp},[])),\
             patch.object(econ,"load_census_transfers",return_value=(rev or self.rev,econ.CENSUS_SHA)):
            return econ.build()

    def test_complete_650_rows_and_fips(self):
        d=self.run_synthetic_source_mocks()
        self.assertEqual(d["coverage"]["stateYears"],650)
        self.assertEqual(len({(r["fipsState"],r["fiscalYear"]) for r in d["records"]}),650)
        self.assertEqual(len(econ.STATES),50)
        self.assertNotIn("11",econ.STATES)
        self.assertIn("09",econ.STATES)
        self.assertIn("56",econ.STATES)

    def test_lagged_macro_inputs_and_contemporaneous_transfer(self):
        d=self.run_synthetic_source_mocks()
        row=next(r for r in d["records"] if r["fipsState"]=="01" and r["fiscalYear"]==2012)
        self.assertEqual(row["gdpCalendarYear"],2010)
        self.assertEqual(row["unemploymentCalendarYear"],2010)
        self.assertEqual(row["transferSourceFiscalYear"],2012)
        self.assertAlmostEqual(row["gdpGrowthPriorAvailableCalendarYearPct"],2.,places=4)
        self.assertEqual(row["federalTransfersShareOfCurrentGeneralRevenue"],0.25)

    def test_no_unsupported_causal_claims(self):
        d=self.run_synthetic_source_mocks()
        self.assertFalse(d["researchReadiness"]["causalModelReady"])
        self.assertTrue(d["researchReadiness"]["federalTransferEndogeneityUnresolved"])
        self.assertIsNone(d["causalEffect"])
        self.assertFalse(all(x["preTreatmentStatus"]["causalControlsVerified"] for x in d["records"]))

    def test_missing_prior_gdp_blocks_publication(self):
        gdp=dict(self.fake_gdp)
        del gdp[("01","2010-01-01")]
        with self.assertRaisesRegex(ValueError,"Missing BEA GDP"):
            self.run_synthetic_source_mocks(gdp=gdp)

    def test_federal_transfer_above_revenue_blocks_publication(self):
        rev=dict(self.rev)
        rev[("01",2012,"SF0004")]=110000
        with self.assertRaisesRegex(ValueError,"Invalid Census revenue composition"):
            self.run_synthetic_source_mocks(rev=rev)

    def test_source_codes_are_exact_and_distinct(self):
        self.assertEqual(econ.REVENUE_CODES["SF0002"],"Revenue - Total General Revenue")
        self.assertIn("From Federal Government",econ.REVENUE_CODES["SF0004"])

if __name__=="__main__":
    unittest.main()
