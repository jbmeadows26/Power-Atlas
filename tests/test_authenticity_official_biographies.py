"""Offline regression checks: official biography audit, provenance, and non-inference."""
import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from validate_authenticity_official_biographies import AUDIT, MEMBERS, COMPARISON, load, validate

class OfficialHouseBiographyAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit, cls.members, cls.comparison = load(AUDIT), load(MEMBERS), load(COMPARISON)

    def test_source_verified_cohort_and_missingness(self):
        s = validate(self.audit, self.members, self.comparison)
        self.assertEqual(s["youngVotingHouseMembersOfficiallyCrosschecked"], 5)
        self.assertEqual(s["officialHouseBiographiesCrosschecked"], 11)
        self.assertEqual(s["otherVotingHouseMembersStillUnverified"], 422)
        self.assertEqual(s["membersWithDisclosedWealthIntervals"], 0)
        self.assertFalse(s["generalizableToAllMembers"])

    def test_birthdate_mismatch_fails_closed(self):
        a = copy.deepcopy(self.audit)
        a["records"][0]["officialBirthDate"] = "1992-04-08"
        with self.assertRaisesRegex(ValueError, "birthdate"):
            validate(a, self.members, self.comparison)

    def test_missing_young_member_fails_closed(self):
        a = copy.deepcopy(self.audit)
        a["records"] = [x for x in a["records"] if x["bioguideId"] != "F000476"]
        with self.assertRaisesRegex(ValueError, "young members"):
            validate(a, self.members, self.comparison)

    def test_wrong_district_fails_closed(self):
        a = copy.deepcopy(self.audit)
        a["records"][0]["houseDistrict"] = 2
        with self.assertRaisesRegex(ValueError, "join mismatch"):
            validate(a, self.members, self.comparison)

    def test_duplicate_member_fails_closed(self):
        a = copy.deepcopy(self.audit)
        a["records"].append(copy.deepcopy(a["records"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate(a, self.members, self.comparison)

    def test_nonofficial_url_fails_closed(self):
        a = copy.deepcopy(self.audit)
        a["records"][0]["officialBiographyUrl"] = "https://example.com/unverified"
        with self.assertRaisesRegex(ValueError, "official House"):
            validate(a, self.members, self.comparison)

    def test_no_inferred_wealth_or_class(self):
        a = copy.deepcopy(self.audit)
        a["records"][0]["workingClassClassification"] = "elite"
        with self.assertRaisesRegex(ValueError, "wealth, class"):
            validate(a, self.members, self.comparison)

    def test_source_hash_must_remain_unknown(self):
        a = copy.deepcopy(self.audit)
        a["records"][0]["sourceContentSha256"] = "fabricated"
        with self.assertRaisesRegex(ValueError, "date/hash"):
            validate(a, self.members, self.comparison)

    def test_undocumented_education_is_not_no_degree(self):
        frost = next(x for x in self.audit["records"] if x["bioguideId"] == "F000476")
        self.assertIsNone(frost["highestDegreeMentionedInBiography"])
        self.assertTrue(frost["degreeAttainmentUnmentioned"])
        a = copy.deepcopy(self.audit)
        next(x for x in a["records"] if x["bioguideId"] == "F000476")["degreeAttainmentUnmentioned"] = False
        with self.assertRaisesRegex(ValueError, "Missing degree"):
            validate(a, self.members, self.comparison)

if __name__ == "__main__":
    unittest.main()
