"""Political Power Atlas coverage dashboard must expose actual six-domain evidence."""
import unittest
from pathlib import Path
from scripts.build_six_gap_coverage import build

ROOT=Path(__file__).resolve().parents[1]
class SixDomainDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=build()
        cls.html=(ROOT/"site/index.html").read_text(encoding="utf8")

    def test_six_domains_loaded_on_frontend(self):
        self.assertIn("loadSixGapEvidence()",self.html)
        self.assertIn("data/coverage-six-domains.json",self.html)
        self.assertIn("Verified coverage by research area",self.html)
        self.assertIn("50 states with record-level sources",self.html.replace("'+verified+'/50 states with record-level sources", "50 states with record-level sources"))
        self.assertIn("sourceVerifiedJurisdictions",self.html)
        self.assertIn("jurisdictionsCompleted",self.html)

    def test_50_state_geometry_2024_but_history_stays_open(self):
        x=self.data["coverage"]["state_legislative_district_polygons_and_legal_boundary_history"]
        self.assertEqual(x["sourceVerifiedJurisdictions"],50)
        self.assertEqual(x["officialSourceRecordsIngested"],6785)
        self.assertEqual(x["jurisdictionsCompleted"],0)

    def test_nc_source_based_2024_elections_not_nationwide(self):
        x=self.data["coverage"]["statewide_local_returns_and_official_vote_reconciliation"]
        j=self.data["coverage"]["state_judicial_selection_and_election_outcomes"]
        self.assertEqual(x["sourceVerifiedJurisdictions"],1)
        self.assertEqual(j["sourceVerifiedJurisdictions"],1)
        self.assertEqual(x["jurisdictionsCompleted"],0)
        self.assertEqual(j["jurisdictionsCompleted"],0)

    def test_uncollected_state_facts_are_not_fabricated(self):
        for name in ("state_campaign_finance",
                     "lower_court_litigation_dockets_and_state_cases"):
            self.assertEqual(self.data["coverage"][name]["sourceVerifiedJurisdictions"],0)

    def test_wa_official_votes_are_counted_but_not_claimed_full(self):
        c=self.data["coverage"]["state_roll_calls"]
        self.assertEqual(c["sourceVerifiedJurisdictions"],1)
        self.assertEqual(c["officialSourceRecordsIngested"],4017)
        self.assertEqual(c["jurisdictionsCompleted"],0)

    def test_ui_explicitly_warns_about_legal_lineage_and_vote_reconciliation(self):
        self.assertIn("legal effective dates remain incomplete",self.html)
        self.assertIn("four certified canvass differences remain unresolved",self.html)
        self.assertIn("Not source-verified",self.html)
        self.assertIn("Gaps are not hidden",self.html)

if __name__=="__main__":
    unittest.main()
