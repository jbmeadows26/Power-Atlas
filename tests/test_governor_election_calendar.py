"""Historical gubernatorial cycle provenance and fiscal-year alignment quality checks."""
import datetime as dt
import unittest
from collections import Counter
from scripts.build_governor_election_calendar import make,schedule,CLASS_A,CLASS_B,ALL_STATES

class GovernorElectionClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=make()
        cls.rows={(r["fipsState"],r["fiscalYear"]):r for r in cls.data["records"]}

    def test_all_50_states_2012_2024(self):
        self.assertEqual(len(CLASS_A),36)
        self.assertEqual(len(CLASS_B),9)
        self.assertEqual(len(ALL_STATES),50)
        self.assertEqual(len(self.rows),650)
        self.assertEqual({x["fipsState"] for x in self.data["records"]},set(ALL_STATES))

    def test_historical_election_calendar_counts(self):
        counts=Counter(e["electionCalendarYear"] for e in schedule())
        self.assertEqual(dict(counts),{
            2011:3,2012:11,2013:2,2014:36,2015:3,2016:12,
            2017:2,2018:36,2019:3,2020:11,2021:2,
            2022:36,2023:3,2024:11,
        })

    def test_off_cycle_and_two_year_states(self):
        self.assertEqual(self.rows[("34",2014)]["electionDuringFiscalYear"],1) # 2013 New Jersey
        self.assertEqual(self.rows[("51",2022)]["electionDuringFiscalYear"],1) # 2021 Virginia
        self.assertEqual(self.rows[("21",2024)]["electionDuringFiscalYear"],1) # 2023 Kentucky
        self.assertEqual(self.rows[("33",2019)]["electionDuringFiscalYear"],1) # 2018 New Hampshire
        self.assertEqual(self.rows[("50",2021)]["electionDuringFiscalYear"],1) # 2020 Vermont
        self.assertEqual(self.rows[("18",2021)]["electionDuringFiscalYear"],1) # 2020 Indiana

    def test_2024_election_falls_into_following_FY(self):
        self.assertEqual(self.rows[("10",2024)]["electionDuringFiscalYear"],0) # Delaware
        self.assertEqual(self.rows[("10",2024)]["preElectionFiscalYear"],1)
        self.assertEqual(self.rows[("10",2024)]["scheduledUpcomingElectionId"],"10-2024")

    def test_special_oregon_2016_not_unmarked_regular(self):
        e=next(x for x in self.data["elections"] if x["id"]=="41-2016")
        self.assertIn("special",e["electionDayRole"])
        self.assertEqual(self.rows[("41",2017)]["electionDuringFiscalYear"],1)

    def test_louisiana_primary_and_runoff_not_fabricated_nov_tuesday(self):
        actual={x["electionCalendarYear"]:x["governorElectionDay"]
                for x in self.data["elections"] if x["fipsState"]=="22"}
        self.assertEqual(actual,{2011:"2011-10-22",2015:"2015-11-21",2019:"2019-11-16",2023:"2023-10-14"})

    def test_secondary_election_and_fiscal_backcast_not_causal(self):
        self.assertIsNone(self.data["causalEstimates"])
        self.assertFalse(self.data["controlsLinked"])
        self.assertEqual(self.data["analysisApproval"],"descriptive_association_sensitivity_only_no_causal_identification")
        self.assertTrue(all(not r["causalModelReady"] for r in self.data["records"]))
        self.assertTrue(all(r["fiscalStartEndVerification"].startswith("CURRENT_") for r in self.data["records"]))

    def test_no_state_has_two_mutually_exclusive_treatment_flags(self):
        self.assertTrue(all(not (r["electionDuringFiscalYear"] and r["preElectionFiscalYear"])
                            for r in self.data["records"]))

if __name__=="__main__":
    unittest.main()
