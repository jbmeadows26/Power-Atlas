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
            observed.add((row["state"], int(row["district"])))
    if not 430 <= len(expected) <= 440 or not 400 <= len(observed) <= 440:
        raise RuntimeError("Unexpected 2024 House geographic key totals")
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    doc = {
        "schema": "power-atlas.house-2024-key-audit.v1",
        "status": "missing_keys" if missing else "key_coverage_only",
        "comparisonYear": 2024,
        "congress": 119,
        "scope": "50 states and DC; excludes Puerto Rico resident commissioner and other territorial delegates",
        "expectedCensusDistrictKeys": len(expected),
        "observedMEDSLDistrictKeys": len(observed),
        "missingCount": len(missing),
        "missing": [{"state": state, "district": district} for state,district in missing],
        "extraCount": len(extra),
        "extra": [{"state": state, "district": district} for state,district in extra],
        "geographySource": geo["source"],
        "electionSource": "https://doi.org/10.7910/DVN/IG0UN2",
        "interpretation": "A missing key identifies a gap in this derived dataset, not a missing election, a vote discrepancy, or evidence of gerrymandering. Key coverage does not validate vote totals."
    }
    DEST.parent.mkdir(parents=True,exist_ok=True)
    rendered = json.dumps(doc,indent=2,ensure_ascii=False)+"\n"
    if not DEST.exists() or DEST.read_text(encoding="utf-8") != rendered:
        DEST.write_text(rendered,encoding="utf-8")
    print("2024 House Census-key audit:",len(observed),"/",len(expected),"missing:",doc["missing"],"extra:",doc["extra"])

if __name__ == "__main__":
    audit()
