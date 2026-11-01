"""Offline positive/negative checks for the 2025 ACS age representation comparison."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_authenticity_acs2025_comparison import build, age_on


def fixture():
    members = []
    districts = []
    for i in range(435):
        bioguide = f"T{i:06d}" if i < 434 else None
        districts.append({"seatKey": f"ZZ-{i:02d}", "memberBioguideIdAtSnapshot": bioguide,
                          "populationAge25plusEstimate": 1000, "populationAge25to34Estimate": 200})
        if bioguide:
            members.append({"bioguideId": bioguide, "chamber": "House", "votingMember": True,
                            "state": "ZZ", "district": i, "party": "Republican" if i % 2 else "Democrat",
                            "birthDate": "1992-10-30" if i == 0 else ("1991-10-30" if i == 1 else "1986-10-30"),
                            "ageYears": 34 if i == 0 else (35 if i == 1 else 40)})
    acs = {"schema": "power-atlas.political-authenticity.acs2025-district-age.v1",
           "surveyYear": 2025, "districtCount": 435, "districtMissingCount": 0,
           "memberSnapshotDate": "2026-10-30", "acsReleaseDate": "2026-10-29",
           "sourceUrl": "https://www2.census.gov/fixture", "sourceSha256": "a"*64,
           "sourceLicense": "United States federal government public-domain statistical data",
           "retrievedAtUTC": "2026-10-31T12:00:00+00:00", "sourceCrosswalkSha256": "c"*64,
           "records": districts}
    roster = {"asOf": "2026-10-30", "source": "https://example.org/fixture",
              "sourceSha256": "b"*64, "license": "CC0-1.0",
              "reviewStatus": "unverified_secondary_data_not_policy_influence_findings", "records": members}
    return acs, roster


class Tests(unittest.TestCase):
    def test_age_exact_birthday(self):
        self.assertEqual(age_on("1992-10-30", "2026-10-30"), 34)
        self.assertEqual(age_on("1992-10-31", "2026-10-30"), 33)

    def test_expected_population_and_vacancy(self):
        a, b = fixture()
        r = build(a, b)
        self.assertEqual(r["districts"], 435)
        self.assertEqual(r["occupiedDistricts"], 434)
        self.assertEqual(r["vacantDistricts"], ["ZZ-434"])
        self.assertEqual(r["populationAge25plusEstimate"], 435000)
        self.assertEqual(r["populationAge25to34Estimate"], 87000)
        self.assertEqual(r["votingHouseMembersAge25to34"], 1)
        self.assertAlmostEqual(r["memberMinusResidentPercentagePoints"], -19.7696, places=4)
        self.assertIsNone(r["uncertainty"]["statisticalSignificanceClaim"])
        self.assertEqual(r["sourceLicenses"]["roster"], "CC0-1.0")
        self.assertEqual(r["crosswalkSourceSha256"], "c"*64)

    def test_stale_snapshot_fails(self):
        a, b = fixture()
        b["asOf"] = "2026-10-29"
        with self.assertRaisesRegex(ValueError, "snapshot"):
            build(a, b)

    def test_duplicate_district_fails(self):
        a, b = fixture()
        a["records"][1]["seatKey"] = a["records"][0]["seatKey"]
        with self.assertRaisesRegex(ValueError, "unique"):
            build(a, b)

    def test_duplicate_member_fails(self):
        a, b = fixture()
        b["records"][1]["bioguideId"] = b["records"][0]["bioguideId"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build(a, b)

    def test_mismatched_seat_fails(self):
        a, b = fixture()
        b["records"][0]["district"] = 100
        with self.assertRaisesRegex(ValueError, "district mismatch"):
            build(a, b)

    def test_age_not_stale(self):
        a, b = fixture()
        b["records"][0]["ageYears"] = 35
        with self.assertRaisesRegex(ValueError, "Stale"):
            build(a, b)

    def test_invalid_population_fails(self):
        a, b = fixture()
        a["records"][0]["populationAge25to34Estimate"] = 1001
        with self.assertRaisesRegex(ValueError, "Invalid"):
            build(a, b)

    def test_missing_provenance_fails(self):
        a, b = fixture()
        a["sourceSha256"] = ""
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            build(a, b)

    def test_checked_in_aggregate_reproducible(self):
        paths = [ROOT / "data/research/political-authenticity" / n for n in (
            "acs-2025-house-district-age.json", "members.json", "acs-2025-age-representation-comparison.json")]
        if not all(p.exists() for p in paths):
            self.skipTest("Observed dataset or aggregate not committed")
        a, b, c = [json.loads(p.read_text()) for p in paths]
        self.assertEqual(build(a, b), c)


if __name__ == "__main__":
    unittest.main()
