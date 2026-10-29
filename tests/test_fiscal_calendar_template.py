"""Offline quality tests for provisional state fiscal-year boundary alignment."""
import datetime as dt
import unittest
from scripts.build_fiscal_calendar_template import make

class FiscalYearClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=make()
        cls.rows={(r["fipsState"],r["fiscalYearLabel"]):r for r in cls.d["records"]}

    def test_no_fabricated_election_dates(self):
        self.assertEqual(len(self.rows),650)
        self.assertIsNone(self.d["electionDateData"])
        self.assertTrue(all(r["electionDate"] is None and r["electionExposureFraction"] is None for r in self.rows.values()))
        self.assertTrue(all(r["electoralTreatmentAssignmentStatus"]=="not_approved" for r in self.rows.values()))

    def test_fiscal_ends_for_four_exception_states(self):
        self.assertEqual(self.rows[("36",2024)]["fiscalStartDate"],"2023-04-01")
        self.assertEqual(self.rows[("36",2024)]["fiscalEndDate"],"2024-03-31")
        self.assertEqual(self.rows[("48",2024)]["fiscalStartDate"],"2023-09-01")
        self.assertEqual(self.rows[("48",2024)]["fiscalEndDate"],"2024-08-31")
        self.assertEqual(self.rows[("01",2024)]["fiscalStartDate"],"2023-10-01")
        self.assertEqual(self.rows[("26",2024)]["fiscalEndDate"],"2024-09-30")

    def test_standard_state_fiscal_year(self):
        r=self.rows[("06",2024)] # California
        self.assertEqual(r["fiscalStartDate"],"2023-07-01")
        self.assertEqual(r["fiscalEndDate"],"2024-06-30")

    def test_every_clock_is_one_full_fiscal_year(self):
        for r in self.rows.values():
            a=dt.date.fromisoformat(r["fiscalStartDate"])
            b=dt.date.fromisoformat(r["fiscalEndDate"])
            self.assertIn((b-a).days,(364,365))

    def test_warning_marks_all_backcasts_provisional(self):
        self.assertTrue(self.d["publicationStatus"].startswith("provisional"))
        self.assertIn("historical",self.d["modelReadiness"])
        self.assertTrue(all(r["historicalVerification"].startswith("provisional") for r in self.d["records"]))
        self.assertEqual(self.d["sourceCoverage"]["statesPerYear"],50)

if __name__=="__main__":
    unittest.main()
