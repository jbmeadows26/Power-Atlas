"""Reviewable evidence checks for the final campaign promises assessment.

Success certifies consistency with persisted source data, NOT causal identification
or independent substantive adjudication of politician conduct.
"""
import copy
import unittest
from unittest.mock import patch

from scripts import build_campaign_assessment as assessment


class FinalCampaignAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=assessment.make()
        cls.pledge=cls.doc["researchQuestions"]["pledgeFulfillment"]
        cls.fiscal=cls.doc["researchQuestions"]["electoralShortTermism"]

    def test_assessment_completion_not_empirical_premature_release(self):
        self.assertIn("assessment_complete",self.doc["completionStatus"])
        self.assertEqual(self.doc["studyReadiness"]["causalClaims"],"prohibited_pending_identification_validation")
        self.assertFalse(self.pledge["frozenPopulationDenominator"])
        self.assertIsNone(self.pledge["overallPledgeFulfillmentRate"])
        self.assertIsNone(self.pledge["confidenceInterval"])
        self.assertIsNone(self.fiscal["electoralTreatmentEffects"])
        self.assertIsNone(self.fiscal["causalConfidenceInterval"])

    def test_singly_reviewed_purposive_pilot_is_not_population(self):
        self.assertEqual(self.pledge["observedProvisionalPilotCases"],8)
        self.assertEqual(self.pledge["unscoredCandidateRows"],24)
        self.assertEqual(self.pledge["independentlyDualAdjudicatedCases"],0)
        self.assertEqual(self.pledge["provisionalOutcomeCounts"],
                         {"attempted_not_enacted":1,"fully_enacted":7})
        self.assertIn("cannot be extrapolated",self.pledge["warning"])

    def test_650_official_state_years_reconcile_with_financial_summaries(self):
        self.assertEqual(self.fiscal["modernStateYears"],650)
        self.assertEqual(self.fiscal["officialFinanceAggregateRows"],3250)
        years=self.fiscal["ratioPercentagesByFiscalYear"]
        self.assertEqual([x["fiscalYear"] for x in years],list(range(2012,2025)))
        self.assertTrue(all(x["observations"]==50 for x in years))
        self.assertEqual(years[0]["meanOf50StateCapitalOutlaySharesPct"],8.67)
        self.assertEqual(years[9]["meanOf50StateCapitalOutlaySharesPct"],6.83)
        self.assertEqual(years[-1]["meanOf50StateCapitalOutlaySharesPct"],9.22)
        self.assertEqual(years[-1]["pooledCapitalOutlaySharePct"],8.26)
        self.assertEqual(self.fiscal["sampleOf50StateMeanTrend2012to2021Pp"],-1.84)
        self.assertEqual(self.fiscal["sampleOf50StateMeanTrend2022to2024Pp"],1.41)

    def test_disallow_cross_2022_trend_and_naive_f_g_k_sum(self):
        self.assertTrue(self.doc["historicalSourceAudit"]["GandKMayOverlap"])
        self.assertEqual(self.doc["historicalSourceAudit"]["rawCapitalCodeRows"],65554)
        self.assertEqual(self.doc["historicalSourceAudit"]["explicitMissingValueMarkers"],66)
        self.assertEqual(self.fiscal["cross2022Comparability"],
                         "blocked_by_documented_census_classification_and_social_insurance_change")
        self.assertFalse(self.fiscal["gubernatorialElectionsMatched"])
        self.assertFalse(self.fiscal["verifiedHistoricalFiscalBoundaries"])
        self.assertEqual(self.fiscal["calendarTemplateRowsProvisional"],650)

    def test_old_promise_feed_finance_data_mismatch_is_explicit(self):
        x=self.doc["sourceRegistryStaleness"]
        self.assertTrue(x["promiseSourceRegistryListsFiscalSourceAsNotIngested"])
        self.assertEqual(x["researchFeedFiscalSeriesCount"],0)
        self.assertEqual(x["correctSeparateModernIngestionObserved"],650)

    def test_provenance_is_explicit_and_local(self):
        paths=self.doc["inputProvenance"]
        self.assertIn("data/fiscal/state-timeseries/aggregate-capital-2012-2024.json",
                      paths.values())
        self.assertTrue(all("https://" not in x for x in paths.values()))


if __name__=="__main__":
    unittest.main()
