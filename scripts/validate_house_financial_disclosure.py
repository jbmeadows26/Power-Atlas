#!/usr/bin/env python3
"""Validate provenance-first House financial disclosure intervals; no net-worth imputation."""
import json
import sys
import math
from datetime import datetime
from urllib.parse import urlsplit
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
            if not isinstance(url, str) or urlsplit(url).scheme != "https" or urlsplit(url).hostname != "disclosures-clerk.house.gov" or urlsplit(url).username or urlsplit(url).password:
                raise ValueError("verified filing requires official original URL")
            if not row.get("reviewedAtUTC") or not row.get("filingType"):
                raise ValueError("missing filing provenance")
        else:
            if row.get("assetLowerUSD") is not None or row.get("assetUpperUSD") is not None:
                raise ValueError("unverified filing must retain null intervals")
        lo, hi = row.get("assetLowerUSD"), row.get("assetUpperUSD")
        open_ended = row.get("assetUpperOpenEnded", False)
        if not isinstance(open_ended, bool):
            raise ValueError("open-ended marker must be boolean")
        if open_ended and (status != "verified_filing" or lo is None or hi is not None):
            raise ValueError("open-ended intervals require verified lower bound and null upper bound")
        if not open_ended and (lo is None) != (hi is None):
            raise ValueError("incomplete interval")
        for value in (lo, hi):
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                raise ValueError("invalid interval bound")
        if lo is not None and hi is not None and hi < lo:
            raise ValueError("reversed interval")
        if status != "verified_filing" and (lo is not None or hi is not None or open_ended):
            raise ValueError("unverified interval")
        if row.get("estimatedNetWorthUSD") is not None:
            raise ValueError("net worth point estimates prohibited")
    return len(rows)

if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(validate(data["records"]))
