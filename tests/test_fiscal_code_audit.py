"""Census source-code coverage audit invariants: never manufacture investment ratios."""
import unittest

from scripts.audit_state_fiscal_codes import compile_audit


class CensusCodeAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=compile_audit()

    def test_16_year_actual_vintage_collection(self):
        self.assertEqual(self.audit["sourceYears"],list(range(2000,2016)))
        self.assertEqual(self.audit["distinctStateYearKeys"],800)
        self.assertEqual(len(self.audit["annualCoverage"]),16)
        self.assertTrue(all(y["stateGovernmentsWithRows"]==50 for y in self.audit["annualCoverage"]))

    def test_counts_reconcile_to_original_source_evidence(self):
        self.assertEqual(self.audit["totalRawCapitalFamilyRecords"],
                         sum(y["originalCodeRows"] for y in self.audit["annualCoverage"]))
        self.assertEqual(self.audit["totalPublishedMissingValueMarkers"],
                         sum(sum(y["missingValuesByMarker"].values()) for y in self.audit["annualCoverage"]))

    def test_g_and_k_overlap_is_not_falsely_summed(self):
        self.assertTrue(self.audit["nonadditiveCharacterCodes"]["forbidNaiveFPlusGPlusK"])
        self.assertIn("include K equipment",self.audit["nonadditiveCharacterCodes"]["G"])
        self.assertNotIn("capitalOutlayTotal",self.audit)
        self.assertIsNone(self.audit["spendingShares"])
        self.assertIsNone(self.audit["electionProximityCoefficients"])
        self.assertIsNone(self.audit["causalFindings"])

    def test_alert_to_2012_2013_scope_discontinuity(self):
        t=next(t for t in self.audit["adjacentYearCodeUncertainty"]
               if t["fromYear"]==2012 and t["toYear"]==2013)
        self.assertGreater(t["recordCountDelta"],0)
        self.assertTrue(t["largeChangeInRowCount"])
        self.assertEqual(t["interpretation"],
                         "coding_universe_or_data_scope_change_requires_review_not_expenditure_change")

    def test_2022_break_requires_harmonization(self):
        breaks={b["year"]:b for b in self.audit["knownBreaks"]}
        self.assertEqual(breaks[2022]["status"],"verified_documented_break")
        self.assertEqual(breaks[2013]["status"],"requires_review")
        self.assertIn("not_imported",self.audit["excludedCoverage"]["2016_to_2025"])
        self.assertEqual(self.audit["publicationStatus"],"source_code_coverage_audited_not_spending_model_ready")

    def test_source_year_codes_have_valid_format(self):
        for y in self.audit["annualCoverage"]:
            self.assertIn(y["sourceRecordWidthChars"],(35,38))
            self.assertEqual(len(y["sourceSHA256"]),64)
            self.assertTrue(y["sourceURL"].startswith("https://www2.census.gov/govs/state/"))
            self.assertEqual(sum(y["capitalFamilyRows"].values()),y["originalCodeRows"])
            self.assertGreater(y["minimumRowsPerState"],0)


if __name__=="__main__":
    unittest.main()
