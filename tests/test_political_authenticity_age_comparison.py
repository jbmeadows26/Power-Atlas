"""Independent checks of the political authenticity age comparison builder."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from build_political_authenticity_age_comparison import build, ACS

class AgeComparisonTests(unittest.TestCase):
    def setUp(self):
        members = []
        for i in range(433):
            members.append({"chamber": "House", "votingMember": True, "ageYears": 32 if i < 5 else 55})
        for i in range(6):
            members.append({"chamber": "House", "votingMember": False, "ageYears": 26})
        for i in range(100):
            members.append({"chamber": "Senate", "votingMember": True, "ageYears": 65})
        self.snapshot = {
            "asOf": "2026-10-29",
            "source": "https://example.org/cc0-roster",
            "sourceSha256": "test",
            "records": members,
        }

    def test_census_components_total_and_25plus(self):
        self.assertEqual(ACS["allResidents"], 340110990)
        self.assertEqual(sum(v for k,v in ACS.items() if k!="allResidents"), ACS["allResidents"])
        self.assertEqual(sum(ACS[k] for k in ("age25to34","age35to44","age45to54","age55to64","age65plus")), 235910719)

    def test_voting_house_excludes_nonvoting_delegates(self):
        result=build(self.snapshot)
        self.assertEqual(result["houseVotingCount"],433)
        self.assertEqual(result["houseVotingAge25to34Count"],5)
        self.assertAlmostEqual(result["houseVotingAge25to34Share"],5/433,places=6)
        self.assertEqual(result["populationAge25plus"],235910719)
        self.assertAlmostEqual(result["houseMinusPopulation25to34PercentagePoints"],(5/433-46198405/235910719)*100,places=3)

    def test_missing_member_age_is_failure_not_zero(self):
        self.snapshot["records"][0]["ageYears"]=None
        with self.assertRaises(ValueError):
            build(self.snapshot)

    def test_incomplete_senate_is_failure(self):
        self.snapshot["records"].pop()
        with self.assertRaises(ValueError):
            build(self.snapshot)

    def test_25to34_upper_boundary(self):
        self.snapshot["records"][5]["ageYears"]=34
        result=build(self.snapshot)
        self.assertEqual(result["houseVotingAge25to34Count"],6)

if __name__=="__main__": unittest.main()
