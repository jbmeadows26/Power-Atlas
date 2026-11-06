#!/usr/bin/env python3
"""Build source-preserving ZIP/bedroom HUD FMR snapshots for Power Atlas.

Reads free public FY2027 HUD-derived Small Area FMR files compiled by
Multifamily Today under CC BY 4.0.  No private addresses, sign-ins, browser
sessions, or paid APIs.  Both original HUD publication and compilation are
credited. Fail-closed: only publish after every state requested passes schema
checks, so a broken partial refresh never replaces good data.

Usage:
    python scripts/ingest_hud_bedroom_rents.py
    python scripts/ingest_hud_bedroom_rents.py --states NJ NY
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import json
import os
from pathlib import Path
import random
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "housing" / "bedroom-rents"
STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI "
          "MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT "
          "VT VA WA WV WI WY").split()
URL = "https://multifamily.today/data/zips/{state}.json"
OFFICIAL = "https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html"
LICENSE_URL = "https://multifamily.today/data/"
EXPECTED_FY = 2027


def is_rent_series(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 5
        and all(
            isinstance(n, (int, float)) and not isinstance(n, bool)
            and 0 < n <= 50000 for n in value
        )
    )


def validate(data: dict, state: str) -> tuple[int, int]:
    if not isinstance(data, dict):
        raise ValueError("Source is not a JSON object")
    if data.get("state") != state or data.get("fy") != EXPECTED_FY:
        raise ValueError("Wrong state or fiscal year")
    if data.get("effective") != "2026-10-01":
        raise ValueError("Unknown effective date")
    areas = data.get("areas")
    zips = data.get("zips")
    if not isinstance(areas, dict) or not isinstance(zips, dict) or not zips:
        raise ValueError("Missing area dictionary or ZIP rows")
    count = 0
    for zipcode, entries in zips.items():
        if not re.fullmatch(r"[0-9]{5}", zipcode):
            raise ValueError(f"Invalid ZIP {zipcode!r}")
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"Missing area records for {zipcode}")
        for item in entries:
            if not isinstance(item, list) or len(item) < 2 or len(item) > 3:
                raise ValueError(f"Malformed area record for {zipcode}")
            if item[0] not in areas:
                raise ValueError(f"Unknown HUD area for {zipcode}")
            if not is_rent_series(item[1]):
                raise ValueError(f"Invalid FY27 studio–4BR values for {zipcode}")
            if len(item) == 3 and not is_rent_series(item[2]):
                raise ValueError(f"Invalid retained FY26 values for {zipcode}")
            count += 1
    for key, area in areas.items():
        if not isinstance(area, dict) or not isinstance(area.get("name"), str):
            raise ValueError(f"Missing HUD area name for {key}")
        if "fmr" in area and not is_rent_series(area["fmr"]):
            raise ValueError(f"Invalid area-wide FMR for {key}")
    return len(zips), count


def download(state: str) -> tuple[str, dict, tuple[int, int]]:
    address = URL.format(state=state)
    last_error = None
    for attempt in range(3):
        req = Request(
            address,
            headers={
                "User-Agent": "PowerAtlas/1.0 (+https://github.com/jbmeadows26/Power-Atlas)",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(req, timeout=50) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                contents = response.read(3_500_000)
                if len(contents) >= 3_500_000:
                    raise ValueError("State response exceeds safety cap")
            data = json.loads(contents)
            counts = validate(data, state)
            # Preserve the source's area, effective-year and exception records.
            # Only add provenance; no synthesis of rents.
            data["publishedBy"] = "U.S. Department of Housing and Urban Development"
            data["compiledBy"] = "Multifamily Today"
            data["source"] = address
            data["officialSource"] = OFFICIAL
            data["license"] = "CC BY 4.0"
            data["attribution"] = "Data: Multifamily Today (multifamily.today)"
            data["compilerDocs"] = LICENSE_URL
            return state, data, counts
        except (OSError, HTTPError, URLError, TimeoutError, ValueError,
                json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1) + random.random())
    raise RuntimeError(f"{state} source unavailable or invalid: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--states", nargs="*", choices=STATES, default=STATES)
    args = parser.parse_args()
    selected = sorted(set(args.states))
    if not selected:
        parser.error("Choose at least one state")
    results: dict[str, tuple[dict, tuple[int, int]]] = {}
    errors = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(download, state): state for state in selected}
        for future in as_completed(futures):
            state = futures[future]
            try:
                _, obj, counts = future.result()
                results[state] = obj, counts
                print(f"{state}: {counts[0]:,} ZIPs / {counts[1]:,} area records", flush=True)
            except Exception as exc:
                errors.append(str(exc))
    if errors:
        print("Refresh did not publish any files; incomplete source:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    DEST.mkdir(parents=True, exist_ok=True)
    for state in selected:
        obj, _ = results[state]
        # Avoid date stamps in payloads so unchanged data produce no Git churn.
        raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
        target = DEST / f"{state}.json"
        if target.exists() and target.read_text(encoding="utf-8") == raw:
            continue
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(raw, encoding="utf-8")
        os.replace(tmp, target)
    print(f"Completed source-validated FY{EXPECTED_FY} snapshot for {len(selected)} states.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
