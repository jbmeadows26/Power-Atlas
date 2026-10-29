#!/usr/bin/env python3
"""Stage original Census legacy state-finance code families, without harmonizing them.

Official archived file listing: https://www2.census.gov/govs/state/
Format reference: 2024 State Government Finances Technical Documentation pp. 3-4; official 2012 archive file was observed with 38 columns despite the newer 35-column documented layout,
https://www2.census.gov/programs-surveys/state/technical-documentation/complete-technical-documentation/statetechdoc2024.pdf

THIS IS A PROVENANCE/FORMAT INGESTION ONLY, NOT A CAPITAL-SPENDING ANALYSIS.
Pre-2022 F/G/K codes must not be silently treated as equivalent to post-2022
F codes (which consolidate construction, land, buildings and equipment).
The 2022 social-insurance treatment also changed the expenditure denominator.

Usage: python -m scripts.collect_state_fiscal_legacy --years 2012 2013 2014 2015
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/fiscal/state-legacy"
BASE = "https://www2.census.gov/govs/state/"
AVAILABLE = range(2000, 2016)
STATE_CODES = {f"{i:02d}" for i in list(range(1, 9)) + list(range(10, 52))}
CAPITAL_FAMILIES = frozenset("FGK")
MAX_SOURCE_BYTES = 1_500_000
SOURCE_FORMAT = "census.legacy_state35.fixed_width_vintage_detected.v1"
SCHEMA = "power-atlas.census-legacy-capital-components.v1"


def read_source(year, fetcher=None):
    if year not in AVAILABLE:
        raise ValueError("Only directly listed 2000-2015 official vintage files are supported")
    url = f"{BASE}{year % 100:02d}state35.txt"
    if fetcher is not None:
        return fetcher(url), url
    request = urllib.request.Request(url, headers={
        "User-Agent": "PowerAtlasResearch/1.0 (source-linked public academic data collector)",
        "Accept": "text/plain",
    })
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                final_url = response.geturl()
                if final_url != url:
                    raise ValueError("Unexpected Census source redirect; source URL requires review")
                data = response.read(MAX_SOURCE_BYTES + 1)
                if len(data) > MAX_SOURCE_BYTES:
                    raise ValueError("Source exceeds configured safe size cap")
                return data, url
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"Official source unavailable for fiscal {year}: {last_error}")


def parse_records(raw: bytes, source_year: int):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Empty, wrong type, or oversized official source")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("Expected ASCII fixed-width Census file") from exc
    all_count = 0
    record_width = None
    selected = []
    state_seen = set()
    unique = set()
    code_families = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            continue
        all_count += 1
        if len(line) not in (35, 38):
            raise ValueError(f"Invalid record width at line {line_number}: {len(line)} (expected documented 35 or observed legacy 38); public-source prefix={line[:65]!r}")
        if record_width is None:
            record_width = len(line)
        elif len(line) != record_width:
            raise ValueError(f"Mixed fixed-width layouts at line {line_number}: {record_width} vs {len(line)}")
        # Census archival state35 files from 2012 have 38 columns: a 15-character
        # amount, not the 12-character amount shown in the newer 2024 codebook.
        amount_end = 29 if record_width == 35 else 32
        gov, item, amount, survey, data_year, origin = (
            line[:14], line[14:17], line[17:amount_end],
            line[amount_end:amount_end + 2],
            line[amount_end + 2:amount_end + 4],
            line[amount_end + 4:amount_end + 6],
        )
        if not gov.isascii() or not gov.isdigit() or not re.fullmatch(r"[A-Z0-9]{3}", item):
            raise ValueError(f"Invalid government code or item code at line {line_number}")
        if not re.fullmatch(r"-?[0-9]+", amount.strip()):
            raise ValueError(f"Unexpected amount encoding at line {line_number}: {amount!r}")
        if not survey.isdigit() or not data_year.isdigit() or not re.fullmatch(r"[A-Z0-9 ]{2}", origin):
            raise ValueError(f"Invalid source year/origin columns at line {line_number}")
        if gov[:2] not in STATE_CODES or gov[2:] != "0"*12:
            # Legacy file may include non-state observations. Do not silently reclassify.
            continue
        if item[:1] not in CAPITAL_FAMILIES:
            continue
        key = (gov, item, survey, data_year, origin)
        if key in unique:
            raise ValueError(f"Repeated (government,item,vintage,origin) at line {line_number}")
        unique.add(key)
        state_seen.add(gov[:2])
        code_families[item[0]] = code_families.get(item[0], 0) + 1
        selected.append({
            "stateGovernmentCode": gov,
            "itemCode": item,
            "amountAsPublished": amount,
            "surveyYearTwoDigits": survey,
            "dataYearTwoDigits": data_year,
            "originCode": origin,
        })
    if all_count < 100 or len(selected) < 100 or len(state_seen) < 40:
        raise ValueError(f"Incomplete original data: all={all_count}, selected={len(selected)}, states={len(state_seen)}")
    # Stable, code-level evidence rows; never compute a ratio from these raw components.
    selected.sort(key=lambda r: (r["stateGovernmentCode"], r["itemCode"], r["surveyYearTwoDigits"], r["dataYearTwoDigits"], r["originCode"]))
    return {
        "year": source_year,
        "recordWidthChars": record_width,
        "allRecordsInspected": all_count,
        "capitalFamilyRowsRetained": len(selected),
        "stateGovernmentCount": len(state_seen),
        "capitalFamilyRowCounts": {k: code_families.get(k, 0) for k in sorted(CAPITAL_FAMILIES)},
        "records": selected,
    }


def make_document(year, raw, url):
    parsed = parse_records(raw, year)
    return {
        "schema": SCHEMA,
        "collectionYear": year,
        "publicationStatus": "official_raw_code_family_staged_not_harmonized",
        "source": {
            "url": url,
            "sourceFormat": SOURCE_FORMAT,
            "recordWidthChars": parsed["recordWidthChars"],
            "sha256OriginalBytes": hashlib.sha256(raw).hexdigest(),
            "bytesRead": len(raw),
            "documentation": "https://www2.census.gov/programs-surveys/state/technical-documentation/complete-technical-documentation/statetechdoc2024.pdf",
        },
        "coverage": {k: parsed[k] for k in ("allRecordsInspected", "capitalFamilyRowsRetained", "stateGovernmentCount", "capitalFamilyRowCounts")},
        "currencyUnits": "unverified_do_not_assume_raw_amount_scale",
        "fiscalYearInterpretation": "source collection year; source data-year and survey-year fields retained separately",
        "warning": "Not a harmonized state spending series; 2022 redefined capital F item codes and social insurance expenditure totals. Do not estimate political business cycles from this raw table.",
        "records": parsed["records"],
    }


def write_outputs(years, fetcher=None):
    outputs = []
    # Download & validate ALL requested source years before writing ANY file.
    for year in sorted(set(years)):
        raw, url = read_source(year, fetcher=fetcher)
        outputs.append(make_document(year, raw, url))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for obj in outputs:
        path = OUTPUT / f"fy{obj['collectionYear']}.json"
        content = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
    index = {
        "schema": "power-atlas.census-legacy-vintage-index.v1",
        "publicationStatus": "real_official_vintage_downloads_not_analysis_ready",
        "years": [r["collectionYear"] for r in outputs],
        "sources": [
            {
                "year": r["collectionYear"], "url": r["source"]["url"],
                "sha256OriginalBytes": r["source"]["sha256OriginalBytes"],
                "stateGovernmentCount": r["coverage"]["stateGovernmentCount"],
                "capitalFamilyRowsRetained": r["coverage"]["capitalFamilyRowsRetained"],
                "path": f"data/fiscal/state-legacy/fy{r['collectionYear']}.json",
            } for r in outputs
        ],
        "spendingShares": None,
        "electionCycleEstimates": None,
        "warning": "Only raw coded record families have been staged; no fiscal comparisons or spending ratios are authorized.",
    }
    p = OUTPUT / "index.json"
    content = json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if not p.exists() or p.read_text(encoding="utf-8") != content:
        p.write_text(content, encoding="utf-8")
    return index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2012, 2013, 2014, 2015])
    args = ap.parse_args()
    summary = write_outputs(args.years)
    print(json.dumps({"years": summary["years"], "sources": summary["sources"], "readiness": summary["publicationStatus"]}, indent=2))


if __name__ == "__main__":
    main()
