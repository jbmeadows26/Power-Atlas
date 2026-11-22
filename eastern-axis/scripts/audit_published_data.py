#!/usr/bin/env python3
"""Fail-closed structural checks for every published Eastern Axis analyst snapshot.

This checks provenance and internal consistency, not whether a sourced claim is true.
Unavailable upstream data is reported explicitly rather than replaced with zero.
"""
import json
import math
import pathlib
import re
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1] / "public" / "analysis"
RECORDS = {
    "manifest.json": "records",
    "early-warning-triage.json": "reviews",
    "financial-markets.json": "metrics",
    "financial-transmission.json": "householdMetrics",
    "global-conflict-watch.json": "zones",
    "military-inventory.json": "assets",
    "physical-early-warning.json": "metrics",
    "product-inventory-context.json": "metrics",
    "product-shortage-outlook.json": "forecasts",
}
SOURCE_KEYS = {"url", "sourceUrl"}
CODE = re.compile(r"^[A-Z]{2}$")
errors = []
warnings = []

def require(condition, message):
    if not condition:
        errors.append(message)

def validate_provenance(item, place):
    url = item.get("sourceUrl") or item.get("url")
    require(isinstance(url, str) and url.startswith("https://") and len(url) > 12,
            place + ": missing or non-HTTPS original source URL")

def check_text(value, path):
    if isinstance(value, float):
        require(math.isfinite(value), path + ": NaN/infinite metric")
    elif isinstance(value, str):
        require(value.lower().strip() not in {"undefined", "nan", "null"},
                path + ": literal placeholder instead of missing-data status")
    elif isinstance(value, dict):
        for key, element in value.items():
            check_text(element, path + "." + key)
    elif isinstance(value, list):
        for idx, element in enumerate(value):
            check_text(element, path + "[" + str(idx) + "]")

def run():
    snapshots = {}
    for file, key in RECORDS.items():
        path = ROOT / file
        if not path.is_file():
            errors.append(file + ": missing snapshot")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"),
                              parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
        except (ValueError, OSError) as exc:
            errors.append(file + ": invalid JSON (" + str(exc)[:100] + ")")
            continue
        snapshots[file] = data
        require(isinstance(data, dict), file + ": root must be an object")
        if not isinstance(data, dict):
            continue
        check_text(data, file)
        records = data.get(key)
        require(isinstance(records, list), file + ": expected list " + key)
        if not isinstance(records, list):
            continue
        ids = []
        for idx, record in enumerate(records):
            place = file + "." + key + "[" + str(idx) + "]"
            require(isinstance(record, dict), place + ": record is not an object")
            if not isinstance(record, dict):
                continue
            require(isinstance(record.get("id"), str) and bool(record["id"]),
                    place + ": missing stable record ID")
            ids.append(record.get("id"))
            if file in {"manifest.json", "military-inventory.json",
                        "financial-markets.json", "financial-transmission.json",
                        "early-warning-triage.json", "product-inventory-context.json"}:
                validate_provenance(record, place)
            if file == "military-inventory.json":
                require(bool(CODE.fullmatch(str(record.get("code", "")))), place + ": invalid ISO2")
                require(isinstance(record.get("value"), (int, float))
                        and not isinstance(record.get("value"), bool)
                        and math.isfinite(record["value"]) and record["value"] >= 0,
                        place + ": invalid quantitative observation")
                require(bool(record.get("published")) and bool(record.get("publisher")),
                        place + ": missing publication year or publisher")
                require(bool(record.get("unit")) and bool(record.get("basis")),
                        place + ": missing unit or measurement basis")
            if file == "global-conflict-watch.json":
                require(isinstance(record.get("countryCodes"), list)
                        and all(isinstance(c, str) and CODE.fullmatch(c)
                                for c in record["countryCodes"]),
                        place + ": invalid country associations")
                for evidence in record.get("evidence", []):
                    validate_provenance(evidence, place + ".evidence")
        require(len(ids) == len(set(ids)), file + ": duplicate record IDs")
        print(file + ": " + str(len(records)) + " records checked")

    conflict = snapshots.get("global-conflict-watch.json", {})
    if conflict:
        require(conflict.get("summary", {}).get("hotspots") == len(conflict.get("zones", [])),
                "global-conflict-watch.json: displayed hotspot total differs from records")
    military = snapshots.get("military-inventory.json", {})
    if military:
        statuses = military.get("collectionHealth", {}).get("worldBank")
        if statuses == "not-run":
            warnings.append("World Bank military enrichment not present in checked repository snapshot; Pages build must run collector")
        elif isinstance(statuses, dict):
            for indicator in ("MS.MIL.TOTL.P1", "MS.MIL.XPND.CD"):
                state = statuses.get(indicator, {}).get("state")
                if state != "ok":
                    warnings.append(indicator + ": " + str(state) + " (missing/stale, not zero)")
        else:
            errors.append("Military inventory: missing World Bank source health")

    for msg in warnings:
        print("WARNING: " + msg, file=sys.stderr)
    for msg in errors:
        print("ERROR: " + msg, file=sys.stderr)
    print("Integrity result: " + str(len(errors)) + " error(s), " + str(len(warnings)) + " coverage warning(s)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(run())
