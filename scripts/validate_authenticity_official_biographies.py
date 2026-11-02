#!/usr/bin/env python3
"""Fail-closed validation of manually reviewed official House biographies.

Does not scrape, invent biographies, infer wealth/class, or upgrade unreviewed
members. Source pages were inspected manually; tests verify joins, not truth of
the underlying external text. No live requests or paid services.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/research/political-authenticity/official-house-biography-audit-2026-11-02.json"
MEMBERS = ROOT / "data/research/political-authenticity/members.json"
COMPARISON = ROOT / "data/research/political-authenticity/acs-2025-age-representation-comparison.json"

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def age_at(birth, day):
    b = dt.date.fromisoformat(birth)
    return day.year - b.year - ((day.month, day.day) < (b.month, b.day))

def validate(audit, members, comparison):
    if audit.get("schema") != "power-atlas.political-authenticity.official-house-biography-audit.v1":
        raise ValueError("Unexpected primary-source audit schema")
    if audit.get("reviewStatus") != "manual_primary_source_crosscheck_single_reviewer_not_independently_adjudicated":
        raise ValueError("Do not overstate independent adjudication")
    if audit.get("sourceContentSha256") is not None or audit.get("sourceDocumentVersionDate") is not None:
        raise ValueError("Unretrieved original source bytes and version dates must remain null")
    day = dt.date.fromisoformat(audit["rosterSnapshotDate"])
    if members["asOf"] != day.isoformat() or comparison["memberSnapshotDate"] != day.isoformat():
        raise ValueError("Roster vintage mismatch")
    roster = [m for m in members["records"] if m["chamber"] == "House" and m["votingMember"]]
    by_id = {m["bioguideId"]: m for m in roster}
    if len(by_id) != len(roster) or len(roster) != comparison["votingHouseMembers"]:
        raise ValueError("Invalid House member denominator")
    young = {m["bioguideId"] for m in roster if 25 <= m["ageYears"] <= 34}
    if len(young) != comparison["votingHouseMembersAge25to34"]:
        raise ValueError("Mismatch with published age comparison")
    seen = set()
    verified_young = set()
    counts = {"Democrat": 0, "Republican": 0}
    degree_count = 0
    for row in audit["records"]:
        key = row["bioguideId"]
        if key in seen or key not in by_id:
            raise ValueError("Duplicate or non-voting-House identity")
        seen.add(key)
        member = by_id[key]
        if (row["name"], row["houseState"], row["houseDistrict"], row["partyAtRosterSnapshot"]) != (
                member["name"], member["state"], member["district"], member["party"]):
            raise ValueError("Bioguide ID / state / district / party / name join mismatch")
        if row["officialBirthDate"] != member["birthDate"]:
            raise ValueError("Official birthdate disagrees with secondary snapshot")
        if age_at(row["officialBirthDate"], day) != member["ageYears"]:
            raise ValueError("Age at roster snapshot inconsistent")
        if row["observedAt"] != audit["reviewedAt"] or row["sourceVersionDate"] is not None or row["sourceContentSha256"] is not None:
            raise ValueError("Source provenance date/hash incorrectly filled")
        if not row["officialBiographyUrl"].startswith("https://history.house.gov/People/"):
            raise ValueError("Source is not an official House Historian biography")
        if row["sourceSection"] != "Concise Biography":
            raise ValueError("Missing precise source section")
        tags = row["roleTagsBeforeCongress"]
        if not isinstance(tags, list) or not tags or len(tags) != len(set(tags)) or any(not isinstance(t, str) or not t for t in tags):
            raise ValueError("Unverifiable or duplicated career tags")
        if any(row[k] is not None for k in ("wealthIntervalUsd", "workingClassClassification", "authenticityScore")):
            raise ValueError("Biography cannot establish wealth, class, or authenticity")
        degree = row["highestDegreeMentionedInBiography"]
        if (degree is None) != row["degreeAttainmentUnmentioned"]:
            raise ValueError("Missing degree is not proof of no degree")
        degree_count += degree is not None
        if key in young:
            verified_young.add(key)
        if member["party"] in counts:
            counts[member["party"]] += 1
    if verified_young != young:
        raise ValueError("All five young members must be officially checked, without substitution")
    if len(seen) != 11 or counts != {"Democrat": 6, "Republican": 5} or degree_count != 10:
        raise ValueError("Purposive bipartisan sample changed; revise documented selection first")
    if comparison["votingHouseMembersAge25to34"] != 5:
        raise ValueError("Do not silently change the published comparison")
    return {"officialHouseBiographiesCrosschecked": len(seen),
            "votingHouseMembersInRoster": len(roster),
            "officialBirthDatesMatchingSecondaryRoster": len(seen),
            "youngVotingHouseMembers": len(young),
            "youngVotingHouseMembersOfficiallyCrosschecked": len(verified_young),
            "otherVotingHouseMembersStillUnverified": len(roster)-len(seen),
            "membersWithSourceReportedCareerTags": len(seen),
            "membersWithSourceReportedHighestDegree": degree_count,
            "membersWithDisclosedWealthIntervals": 0,
            "bipartisanPurposiveSample": counts,
            "generalizableToAllMembers": False,
            "causalInferenceSupported": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="Validate existing archived sources without network calls")
    args = p.parse_args()
    result = validate(load(AUDIT), load(MEMBERS), load(COMPARISON))
    print(json.dumps(result, indent=2, sort_keys=True))
if __name__ == "__main__":
    main()
