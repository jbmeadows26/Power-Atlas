#!/usr/bin/env python3
"""Build a descriptive, same-ACS-vintage House age representation comparison.

Inputs are checked-in, source-hashed 2025 ACS 119th district estimates and
a dated member roster. No survey microdata, imputed ages, or causal modeling.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACS = ROOT / "data/research/political-authenticity/acs-2025-house-district-age.json"
MEMBERS = ROOT / "data/research/political-authenticity/members.json"
OUTPUT = ROOT / "data/research/political-authenticity/acs-2025-age-representation-comparison.json"


def age_on(birth_date: str, as_of: str) -> int:
    from datetime import date
    born, today = date.fromisoformat(birth_date), date.fromisoformat(as_of)
    if born > today:
        raise ValueError("Member birth date after roster snapshot")
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def build(acs: dict, roster: dict) -> dict:
    if acs.get("schema") != "power-atlas.political-authenticity.acs2025-district-age.v1":
        raise ValueError("Expected 2025 official district B01001 dataset")
    if acs.get("surveyYear") != 2025 or acs.get("districtCount") != 435 or acs.get("districtMissingCount") != 0:
        raise ValueError("Incomplete or wrong-vintage 2025 ACS districts")
    if acs.get("memberSnapshotDate") != roster.get("asOf"):
        raise ValueError("ACS join and member roster have different snapshot dates")
    if not acs.get("sourceUrl", "").startswith("https://www2.census.gov/") or len(acs.get("sourceSha256", "")) != 64:
        raise ValueError("Missing official Census source and fingerprint")
    if not roster.get("source", "").startswith("https://") or len(roster.get("sourceSha256", "")) != 64:
        raise ValueError("Missing roster provenance")
    records = acs.get("records", [])
    if len(records) != 435 or len({r["seatKey"] for r in records}) != 435:
        raise ValueError("Expected 435 unique House seats")
    active = [m for m in roster.get("records", []) if m["chamber"] == "House" and m["votingMember"]]
    if len({m["bioguideId"] for m in active}) != len(active):
        raise ValueError("Duplicate voting member identity")
    by_id = {m["bioguideId"]: m for m in active}
    matched = set()
    party = {}
    pop25 = popyoung = 0
    vacant = []
    for row in records:
        adult, young = row["populationAge25plusEstimate"], row["populationAge25to34Estimate"]
        if not isinstance(adult, int) or not isinstance(young, int) or not 0 <= young <= adult:
            raise ValueError("Invalid district age population counts")
        pop25 += adult
        popyoung += young
        bioguide = row["memberBioguideIdAtSnapshot"]
        if bioguide is None:
            vacant.append(row["seatKey"])
            continue
        if bioguide not in by_id or bioguide in matched:
            raise ValueError("Unmatched or duplicated House member")
        member = by_id[bioguide]
        expected_seat = f'{member["state"]}-{member["district"]:02d}'
        if row["seatKey"] != expected_seat:
            raise ValueError("Member district mismatch")
        age = age_on(member["birthDate"], roster["asOf"])
        if member.get("ageYears") != age:
            raise ValueError("Stale or inconsistent member age")
        matched.add(bioguide)
        group = party.setdefault(member["party"], {"members": 0, "membersAge25to34": 0,
                                                   "districtResidentsAge25plus": 0,
                                                   "districtResidentsAge25to34": 0})
        group["members"] += 1
        group["membersAge25to34"] += int(25 <= age <= 34)
        group["districtResidentsAge25plus"] += adult
        group["districtResidentsAge25to34"] += young
    if matched != set(by_id) or not pop25:
        raise ValueError("Incomplete member-to-district join")
    young_members = sum(g["membersAge25to34"] for g in party.values())
    member_share = young_members / len(active)
    resident_share = popyoung / pop25
    return {
        "schema": "power-atlas.political-authenticity.acs2025-age-representation-comparison.v1",
        "publicationStatus": "OBSERVED_DESCRIPTIVE_TWO_DATE_NONCAUSAL",
        "acsSurveyYear": 2025,
        "acsReleaseDate": acs["acsReleaseDate"],
        "memberSnapshotDate": roster["asOf"],
        "sourceUrls": {"acsB01001": acs["sourceUrl"], "roster": roster["source"],
                       "acsRelease": "https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html",
                       "districtGeography": "https://www.census.gov/programs-surveys/decennial-census/about/rdo/congressional-districts.119th_Congress.html"},
        "sourceHashesSha256": {"acsB01001": acs["sourceSha256"], "roster": roster["sourceSha256"]},
        "sourceLicenses": {"acsB01001": acs["sourceLicense"], "roster": roster["license"]},
        "sourceRetrievedAtUTC": {"acsB01001": acs["retrievedAtUTC"], "rosterSnapshot": roster["asOf"]},
        "crosswalkSourceSha256": acs["sourceCrosswalkSha256"],
        "rosterReviewStatus": roster["reviewStatus"],
        "geography": "119th Congress 435 voting House districts, excluding DC and nonvoting territories",
        "populationUniverse": "2025 ACS estimated residents age 25+ in 435 districts, including noncitizens; not legally eligible candidate pool",
        "memberUniverse": "Voting House members in roster snapshot; vacant seats excluded from member denominator",
        "districts": len(records),
        "occupiedDistricts": len(active),
        "vacantDistricts": sorted(vacant),
        "populationAge25plusEstimate": pop25,
        "populationAge25to34Estimate": popyoung,
        "populationAge25to34ShareOf25plus": round(resident_share, 9),
        "votingHouseMembers": len(active),
        "votingHouseMembersAge25to34": young_members,
        "votingHouseMembersAge25to34Share": round(member_share, 9),
        "memberMinusResidentPercentagePoints": round((member_share - resident_share) * 100, 4),
        "memberToResidentAge25to34ShareRatio": round(member_share / resident_share, 6),
        "partyStrataDescriptive": dict(sorted(party.items())),
        "uncertainty": {"ageBandSourceMOE90": "Published district MOEs exist; no valid national aggregate/share MOE or confidence interval calculated",
                        "memberAgeSourceStatus": "Secondary roster birth dates not independently primary-source-verified",
                        "statisticalSignificanceClaim": None},
        "limitations": [
            "2025 ACS resident estimates compared with a 2026-10-30 member snapshot, not a synchronized point-in-time population",
            "Population includes noncitizens and residents ineligible for House candidacy; legal eligibility not modeled",
            "District estimates and member counts are different measurement universes; ratio is descriptive only",
            "District age shares and party strata are not evidence of causal political responsiveness or misconduct",
            "Member biographies and birth dates require independent primary-source confirmation",
            "No survey microdata, occupational histories, disclosed-wealth intervals, or voter preferences used",
            "No statistical tests: ACS design covariance and valid share standard errors not available in this aggregate",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--acs", type=Path, default=ACS)
    p.add_argument("--members", type=Path, default=MEMBERS)
    p.add_argument("--output", type=Path, default=OUTPUT)
    args = p.parse_args()
    result = build(json.loads(args.acs.read_text()), json.loads(args.members.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"districts": result["districts"], "members": result["votingHouseMembers"],
                      "gap_pp": result["memberMinusResidentPercentagePoints"]}))


if __name__ == "__main__":
    main()
