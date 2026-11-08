"""Reconcile observed ACS district totals without imputing party for vacancies.

Run: python -m unittest discover -s tests -p 'test_political_authenticity_acs_reconciliation.py'
No network access or optional dependencies required.
"""
import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data/research/political-authenticity/acs-2025-age-representation-comparison.json"


class TestACS2025Reconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(DATA.read_text(encoding="utf-8"))

    def test_geographic_and_member_denominators(self):
        d = self.d
        self.assertEqual(d["districts"], 435)
        self.assertEqual(d["occupiedDistricts"] + len(d["vacantDistricts"]), 435)
        self.assertEqual(d["votingHouseMembers"], d["occupiedDistricts"])
        self.assertEqual(sum(v["members"] for v in d["partyStrataDescriptive"].values()), d["votingHouseMembers"])

    def test_vacancy_population_reconciles_without_party_imputation(self):
        d = self.d
        vacant = d["unoccupiedDistrictPopulationDescriptive"]
        occupied = d["occupiedDistrictPopulationDescriptive"]
        for suffix, total in (
            ("Age25plus", d["populationAge25plusEstimate"]),
            ("Age25to34", d["populationAge25to34Estimate"]),
        ):
            key = "residents" + suffix + "Estimate"
            self.assertEqual(occupied[key] + vacant[key], total)
            self.assertEqual(sum(s["districtResidents" + suffix] for s in d["partyStrataDescriptive"].values()), occupied[key])
        self.assertIsNone(vacant["partyAssignment"])
        self.assertEqual(set(vacant["districts"]), set(d["vacantDistricts"]))

    def test_population_and_member_shares_recalculate(self):
        d = self.d
        self.assertAlmostEqual(d["populationAge25to34Estimate"] / d["populationAge25plusEstimate"], d["populationAge25to34ShareOf25plus"], places=7)
        self.assertAlmostEqual(d["votingHouseMembersAge25to34"] / d["votingHouseMembers"], d["votingHouseMembersAge25to34Share"], places=8)
        self.assertAlmostEqual(100 * (d["votingHouseMembersAge25to34Share"] - d["populationAge25to34ShareOf25plus"]), d["memberMinusResidentPercentagePoints"], delta=0.0001)

    def test_occupied_comparison_recalculates(self):
        d = self.d
        o = d["occupiedDistrictPopulationDescriptive"]
        share = o["residentsAge25to34Estimate"] / o["residentsAge25plusEstimate"]
        self.assertAlmostEqual(share, o["age25to34ShareOf25plus"], places=8)
        self.assertAlmostEqual(100 * (d["votingHouseMembersAge25to34Share"] - share), o["memberMinusOccupiedDistrictResidentPercentagePoints"], delta=0.0001)

    def test_no_unearned_causal_or_statistical_claim(self):
        d = self.d
        self.assertEqual(d["publicationStatus"], "OBSERVED_DESCRIPTIVE_TWO_DATE_NONCAUSAL")
        self.assertIsNone(d["uncertainty"]["statisticalSignificanceClaim"])
        self.assertTrue(d["sourceUrls"]["acsB01001"].startswith("https://"))
        self.assertTrue(d["sourceUrls"]["districtGeography"].startswith("https://"))
        self.assertIn("noncitizens", d["populationUniverse"])
        self.assertIn("not independently primary-source-verified", d["uncertainty"]["memberAgeSourceStatus"])


if __name__ == "__main__":
    unittest.main()
