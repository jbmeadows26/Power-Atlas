#!/usr/bin/env python3
"""Validate provenance-first House financial disclosure intervals; no net-worth imputation."""
import json
import sys
from pathlib import Path

OFFICIAL_HOST = "https://disclosures-clerk.house.gov/"
ALLOWED = {"verified_filing", "not_reviewed", "no_filing_found", "ambiguous_identity", "unreadable_filing"}

def validate(rows):
    if not isinstance(rows, list):
        raise ValueError("records must be a list")
    seen = set()
    for row in rows:
        key = (row.get("bioguideId"), row.get("filingYear"), row.get("documentId"))
        if any(v is None for v in key) or key in seen:
            raise ValueError("missing or duplicate composite key")
        seen.add(key)
        status = row.get("status")
        if status not in ALLOWED:
            raise ValueError("invalid review status")
        url = row.get("originalFilingUrl")
        if status == "verified_filing":
            if not isinstance(url, str) or not url.startswith(OFFICIAL_HOST):
                raise ValueError("verified filing requires official original URL")
            if not row.get("reviewedAtUTC") or not row.get("filingType"):
                raise ValueError("missing filing provenance")
        else:
            if row.get("assetLowerUSD") is not None or row.get("assetUpperUSD") is not None:
                raise ValueError("unverified filing must retain null intervals")
        lo, hi = row.get("assetLowerUSD"), row.get("assetUpperUSD")
        if (lo is None) != (hi is None):
            raise ValueError("incomplete interval")
        if lo is not None and (not isinstance(lo, (int,float)) or not isinstance(hi,(int,float)) or lo < 0 or hi < lo):
            raise ValueError("invalid interval")
        if row.get("estimatedNetWorthUSD") is not None:
            raise ValueError("net worth point estimates prohibited")
    return len(rows)

if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(validate(data["records"]))
