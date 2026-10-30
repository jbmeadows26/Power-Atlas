"""Actual six-domain state-level evidence QA: observed vs merely source-indexed."""
import unittest
from scripts.build_six_gap_coverage import build,DOMAINS

class SixGaps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=build()
        cls.rows={(r["state"],r["domain"]):r for r in cls.doc["records"]}
        cls.c=cls.doc["coverage"]

    def test_50_state_six_domain_grid(self):
        self.assertEqual(self.doc["jurisdictions"],50)
        self.assertEqual(len(self.doc["records"]),300)
        self.assertEqual(len(self.rows),300)
        self.assertEqual(set(self.c),set(DOMAINS))
        self.assertTrue(all(x["jurisdictionsIndexed"]==50 for x in self.c.values()))

    def test_current_official_geometry_has_all_fifty_states_and_not_false_legal_history(self):
        v=self.c["state_legislative_district_polygons_and_legal_boundary_history"]
        self.assertEqual(v["sourceVerifiedJurisdictions"],50)
        self.assertEqual(v["officialSourceRecordsIngested"],6785)
        self.assertEqual(v["jurisdictionsCompleted"],0)
        for state in self.doc["records"]:
            if state["domain"]=="state_legislative_district_polygons_and_legal_boundary_history":
                self.assertGreater(state["recordsIngested"],0)
                self.assertTrue(state["officialRecordsSourceLinked"])
                self.assertEqual(len(state["sourceDiscovery"]["current2024CensusZIPs"]),
                                 1 if state["state"]=="NE" else 2)
                self.assertIn("history",state["coverageStatus"])

    def test_authentic_north_carolina_original_precinct_and_judicial_source_counts(self):
        a=self.c["statewide_local_returns_and_official_vote_reconciliation"]
        j=self.c["state_judicial_selection_and_election_outcomes"]
        self.assertEqual(a["sourceVerifiedJurisdictions"],1)
        self.assertEqual(a["officialSourceRecordsIngested"],233510)
        self.assertEqual(j["sourceVerifiedJurisdictions"],1)
        self.assertEqual(j["officialSourceRecordsIngested"],227)
        r=self.rows[("NC","statewide_local_returns_and_official_vote_reconciliation")]
        self.assertEqual(r["sourceDiscovery"]["countyCount"],100)
        self.assertEqual(r["sourceDiscovery"]["exceptionCount"],4)
        self.assertEqual(r["reconciliationStatus"],"four_certified_spotchecks_unresolved")

    def test_missing_four_domains_are_not_fabricated(self):
        for name in ("lower_court_litigation_dockets_and_state_cases",):
            self.assertEqual(self.c[name]["sourceVerifiedJurisdictions"],0)
            self.assertEqual(self.c[name]["officialSourceRecordsIngested"],0)
            self.assertEqual(self.c[name]["jurisdictionsCompleted"],0)

    def test_wa_member_rollcall_sample_is_source_verified_but_not_complete(self):
        x=self.c["state_roll_calls"]
        self.assertEqual(x["sourceVerifiedJurisdictions"],1)
        self.assertEqual(x["officialSourceRecordsIngested"],4017)
        self.assertEqual(x["jurisdictionsCompleted"],0)
        sample=self.rows[("WA","state_roll_calls")]
        self.assertEqual(sample["sourceDiscovery"]["rollCalls"],56)
        self.assertIn("not_full_biennium",sample["coverageStatus"])

    def test_wa_coarse_finance_categories_with_licensing_gate(self):
        x=self.c["state_campaign_finance"]
        self.assertEqual(x["sourceVerifiedJurisdictions"],1)
        self.assertEqual(x["officialSourceRecordsIngested"],9)
        self.assertEqual(x["jurisdictionsCompleted"],0)
        row=self.rows[("WA","state_campaign_finance")]
        self.assertEqual(row["sourceDiscovery"]["electionYears"],[2020,2022,2024])
        self.assertIn("noncommercial",row["sourceDiscovery"]["licensingWarning"])
        self.assertIn("aggregates",row["coverageStatus"])

    def test_no_domains_falsely_complete(self):
        self.assertTrue(all(v["jurisdictionsCompleted"]==0 for v in self.c.values()))
        self.assertTrue(all(not r["domainFullyComplete"] for r in self.doc["records"]))
        self.assertIn("partial",self.doc["publicationStatus"])

    def test_dc_and_pr_not_in_fifty_state_denominator(self):
        self.assertTrue(self.doc["additionalDistrictOfColumbiaElectionAuthorityKnown"])
        self.assertFalse(any(r["state"] in ("DC","PR") for r in self.doc["records"]))

if __name__=="__main__":
    unittest.main()
