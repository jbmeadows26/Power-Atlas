"""Audit 2024 House result district keys against official 119th Census geography.

This compares geographic key coverage only. It does not certify vote totals,
establish partisan bias, or infer any wrongdoing from a missing data row.
"""
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "data/geography/districts-119.geojson"
VOTES = ROOT / "data/elections/house-districts.json"
STATES = ROOT / "data/geography/states.json"
DEST = ROOT / "data/health/house-2024-audit.json"
UNOPPOSED = ROOT / "data/elections/house-2024-unopposed.json"

def audit():
    geo = json.loads(MAP.read_text(encoding="utf-8"))
    votes = json.loads(VOTES.read_text(encoding="utf-8"))
    states = json.loads(STATES.read_text(encoding="utf-8"))["states"]
    state_by_fips = {x["fips"]: x["postal"] for x in states if x["postal"] != "PR"}
    if len(state_by_fips) != 51:
        raise RuntimeError("Expected 50 states and DC for House key comparison")
    expected = set()
    for feature in geo["features"]:
        p = feature["properties"]
        state = state_by_fips.get(p["STATEFP"])
        if state is not None:
            expected.add((state, int(p["CD119FP"])))
    observed = set()
    for row in votes["records"]:
        if row.get("year") == 2024 and row.get("state") in set(state_by_fips.values()):
            # Census labels DC's nonvoting delegate CD=98; MEDSL uses 0.
            # Normalize only this known identifier convention, not vote totals.
            district = int(row["district"])
            if row["state"] == "DC" and district == 0:
                district = 98
            observed.add((row["state"], district))
    if not 430 <= len(expected) <= 440 or not 400 <= len(observed) <= 440:
        raise RuntimeError("Unexpected 2024 House geographic key totals")
    status_only = json.loads(UNOPPOSED.read_text(encoding="utf-8"))["records"] if UNOPPOSED.exists() else []
    status_keys = {(r["state"], int(r["district"])) for r in status_only}
    if len(status_keys) != len(status_only) or not status_keys.issubset(expected) or status_keys.intersection(observed):
        raise RuntimeError("Status-only seats must be unique Census keys absent from vote rows")
    if any(r.get("reportedVoteTotal") is not None or r.get("reviewStatus") != "official_house_clerk_2024_status_only" for r in status_only):
        raise RuntimeError("Status-only records must not impute vote totals")
    missing = sorted(expected - observed - status_keys)
    extra = sorted(observed - expected)
    doc = {
        "schema": "power-atlas.house-2024-key-audit.v1",
        "status": "missing_keys" if missing else "all_keys_accounted_for_vote_totals_not_complete",
        "comparisonYear": 2024,
        "congress": 119,
        "scope": "50 states and DC; excludes Puerto Rico resident commissioner and other territorial delegates; normalizes DC MEDSL district 0 to Census delegate code 98",
        "expectedCensusDistrictKeys": len(expected),
        "observedMEDSLDistrictKeys": len(observed),
        "officialUnopposedStatusOnlyKeys": len(status_keys),
        "accountedForDistrictKeys": len(observed | status_keys),
        "unopposedStatusSource": "https://clerk.house.gov/member_info/electionInfo/2024/statistics2024.pdf",
        "missingCount": len(missing),
        "missing": [{"state": state, "district": district} for state,district in missing],
        "extraCount": len(extra),
        "extra": [{"state": state, "district": district} for state,district in extra],
        "geographySource": geo["source"],
        "electionSource": "https://doi.org/10.7910/DVN/IG0UN2",
        "interpretation": "Districts without reported general-election vote totals may be documented as elected unopposed using the official House Clerk publication. Never replace unavailable totals with zero; key coverage is not vote-total validation or a gerrymandering measure."
    }
    DEST.parent.mkdir(parents=True,exist_ok=True)
    rendered = json.dumps(doc,indent=2,ensure_ascii=False)+"\n"
    if not DEST.exists() or DEST.read_text(encoding="utf-8") != rendered:
        DEST.write_text(rendered,encoding="utf-8")
    print("2024 House Census-key audit:",len(observed),"vote rows +",len(status_keys),"official status-only /",len(expected),"expected; unresolved:",doc["missing"],"extra:",doc["extra"])

if __name__ == "__main__":
    audit()
