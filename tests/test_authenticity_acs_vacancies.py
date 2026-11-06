"""Ensure 2025 ACS party strata do not silently lose vacant House districts."""
import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data/research/political-authenticity/acs-2025-age-representation-comparison.json"

class VacantDistrictReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(DATA.read_text(encoding="utf-8"))

    def test_vacant_districts_preserved_without_party(self):
        d = self.d
        v = d["unoccupiedDistrictPopulationDescriptive"]
        self.assertEqual(v["districts"], ["FL-20", "TX-23"])
        self.assertEqual(d["districts"], d["occupiedDistricts"] + len(v["districts"]))
        self.assertIsNone(v["partyAssignment"])

    def test_resident_denominators_reconcile(self):
        d = self.d
        v = d["unoccupiedDistrictPopulationDescriptive"]
        o = d["occupiedDistrictPopulationDescriptive"]
        for key, total in [("residentsAge25plusEstimate", d["populationAge25plusEstimate"]),
                           ("residentsAge25to34Estimate", d["populationAge25to34Estimate"])]:
            self.assertEqual(o[key] + v[key], total)
        self.assertEqual(v["residentsAge25plusEstimate"], 1095946)
        self.assertEqual(v["residentsAge25to34Estimate"], 218632)

    def test_party_strata_equal_occupied_only(self):
        d = self.d
        o = d["occupiedDistrictPopulationDescriptive"]
        self.assertEqual(sum(x["districtResidentsAge25plus"] for x in d["partyStrataDescriptive"].values()),
                         o["residentsAge25plusEstimate"])
        self.assertEqual(sum(x["districtResidentsAge25to34"] for x in d["partyStrataDescriptive"].values()),
                         o["residentsAge25to34Estimate"])
        self.assertEqual(sum(x["members"] for x in d["partyStrataDescriptive"].values()), d["votingHouseMembers"])

    def test_alternative_occupied_district_comparison_is_descriptive(self):
        d = self.d
        o = d["occupiedDistrictPopulationDescriptive"]
        observed = o["residentsAge25to34Estimate"] / o["residentsAge25plusEstimate"]
        self.assertAlmostEqual(o["age25to34ShareOf25plus"], observed, places=8)
        self.assertAlmostEqual(o["memberMinusOccupiedDistrictResidentPercentagePoints"],
                               100 * (d["votingHouseMembersAge25to34Share"] - observed), places=3)
        self.assertNotEqual(o["memberMinusOccupiedDistrictResidentPercentagePoints"],
                            d["memberMinusResidentPercentagePoints"])

if __name__ == "__main__":
    unittest.main()
