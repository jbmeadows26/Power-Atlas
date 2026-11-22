#!/usr/bin/env python3
"""Build a source-attributed, openly licensed country military equipment layer.

A pinned CC BY 4.0 editorial compilation provides equipment estimates; it is
NOT authoritative confirmation of operational readiness or active deployment.
The SHA-256 pin prevents silent changes, and an upstream failure aborts a new
publish rather than replacing a previously verified site with missing data.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import pathlib
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "analysis" / "military-inventory.json"
RELEASE = "2026-q4-r20261121"
DOWNLOAD_URL = "https://www.defensematrixlab.com/data/" + RELEASE + "/countries_latest_long.csv"
SOURCE_PAGE = "https://www.defensematrixlab.com/en/data-download"
LICENCE = "https://creativecommons.org/licenses/by/4.0/"
EXPECTED_SHA256 = "fb12f0ba6209b84c2ff4207d7567480051be5bba8eff1791530da801a449ef82"
# These represent countable units or people, not power scores, budget, booleans
# or an unverified claim that an estimated zero is definitively none.
CATEGORIES = {
    "active_personnel": "Personnel",
    "reserve_personnel": "Personnel",
    "paramilitary": "Personnel",
    "main_battle_tanks": "Land",
    "armored_vehicles": "Land",
    "artillery": "Land",
    "mlrs": "Land",
    "fighter_aircraft": "Air",
    "attack_aircraft": "Air",
    "transport_aircraft": "Air",
    "trainer_aircraft": "Air",
    "tanker_aircraft": "Air",
    "awacs_aircraft": "Air",
    "attack_helicopters": "Air",
    "utility_helicopters": "Air",
    "combat_uav": "Air",
    "aircraft_carriers": "Naval",
    "amphibious_ships": "Naval",
    "destroyers": "Naval",
    "frigates": "Naval",
    "corvettes": "Naval",
    "submarines": "Naval",
    "patrol_vessels": "Naval",
    "mine_warfare": "Naval",
    "ballistic_missiles": "Missiles",
    "cruise_missiles": "Missiles",
    "military_satellites": "Space",
}
REQUIRED_COLUMNS = set("iso2 iso3 country metric_code metric category unit year value confidence source source_url".split())
CONFIDENCE = {"high", "medium", "estimate"}

def download(url=DOWNLOAD_URL, attempts=2):
    request = urllib.request.Request(url, headers={
        "Accept": "text/csv, text/plain, */*",
        "User-Agent": "EasternAxisPublicOSINT/1.0 (CC BY 4.0 data attribution; GitHub Pages)"
    })
    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                if response.status != 200:
                    raise ValueError("Source HTTP " + str(response.status))
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000 or len(raw) < 100_000:
                raise ValueError("Implausible CSV size")
            return raw
        except Exception as exc:
            last = exc
            if i + 1 < attempts:
                time.sleep(2)
    raise RuntimeError("Pinned equipment source not available: " + str(last))

def parse_verified_csv(raw: bytes):
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError("DML pinned CSV changed unexpectedly: sha256 " + sha)
    text = raw.decode("utf-8-sig")
    parser = csv.DictReader(io.StringIO(text))
    if parser.fieldnames is None or set(parser.fieldnames) != REQUIRED_COLUMNS:
        raise ValueError("DML military equipment CSV schema drift")
    rows = list(parser)
    if len(rows) != 9641:
        raise ValueError("DML row count differs from the reviewed 2026-11-21 edition")
    return rows

def make_equipment_entries(rows):
    result = []
    ids = set()
    per_category = {}
    countries = set()
    for row in rows:
        metric = row["metric_code"].strip()
        if metric not in CATEGORIES:
            continue
        if row["category"].lower() not in {"land", "air", "naval", "personnel", "missile", "space"}:
            raise ValueError("Unexpected source category for " + metric)
        if row["unit"] != "count":
            raise ValueError("Countable equipment must have count unit: " + metric)
        code = row["iso2"].strip().upper()
        if len(code) != 2 or not code.isalpha():
            raise ValueError("Invalid country code")
        year_text = row["year"].strip()
        if not year_text.isdigit() or int(year_text) < 2020 or int(year_text) > 2026:
            raise ValueError("Invalid observation year " + year_text)
        confidence = row["confidence"].strip().lower()
        if confidence not in CONFIDENCE:
            raise ValueError("Unknown estimate confidence " + confidence)
        raw_number = row["value"].strip()
        if not raw_number:
            continue
        value = float(raw_number)
        if not math.isfinite(value) or value < 0 or value != int(value):
            raise ValueError("Invalid equipment count " + raw_number)
        # The source contains many inferred zeros (often landlocked fleets).
        # Do not report these as independently established absence of equipment.
        if value == 0:
            continue
        count = int(value)
        if count > 100_000_000:
            raise ValueError("Out-of-range count")
        record_id = "dml-" + RELEASE + "-" + code.lower() + "-" + metric
        if record_id in ids:
            raise ValueError("Duplicate country + equipment type")
        ids.add(record_id)
        subject = row["metric"].strip()
        if not subject or len(subject) > 140:
            raise ValueError("Invalid metric label")
        issued_by = row["source"].strip()
        if not issued_by:
            raise ValueError("Missing editorial source")
        year = int(year_text)
        category = CATEGORIES[metric]
        detail = (
            "Independent published estimate, not a verified count of combat-ready systems. "
            "Storage, maintenance and availability may differ from the stated inventory."
        )
        if metric == "combat_uav":
            detail = ("Reported armed UAVs only. Tactical and one-way attack drones "
                      "are likely incompletely counted; this is not total UAV capacity.")
        if metric in {"ballistic_missiles", "cruise_missiles"}:
            detail = ("Very uncertain count based on open reporting; do not treat as "
                      "deployed ready-to-launch weapons or launch-system totals.")
        if category == "Personnel":
            detail = ("Estimated headcount for " + year_text + ". Active, reserve and "
                      "paramilitary are different personnel groups; do not sum with "
                      "historical WDI figures.")
        if year < 2026:
            detail += " Historical observation: " + year_text + "."
        source_url = row.get("source_url", "").strip()
        if not source_url.startswith("https://"):
            source_url = DOWNLOAD_URL
        record = {
            "id": record_id,
            "code": code,
            "countryName": row["country"].strip(),
            "category": category,
            "metricCode": metric,
            "name": subject,
            "quantity": f"{count:,}",
            "value": count,
            "unit": "people" if category == "Personnel" else "systems",
            "published": year_text,
            "publisher": "DefenseMatrixLab (CC BY 4.0)",
            "url": source_url,
            "sourceDatasetUrl": DOWNLOAD_URL,
            "basis": "DML " + RELEASE + " · " + confidence + " confidence · " + issued_by[:120],
            "detail": detail,
            "status": "editorial-estimate" if confidence == "estimate" else "independent-inventory-estimate",
            "confidence": confidence,
            "observationYear": year,
            "estimate": True,
            "readiness": "not-verified",
            "licence": LICENCE
        }
        result.append(record)
        countries.add(code)
        per_category[category] = per_category.get(category, 0) + 1
    if len(result) < 1600 or len(countries) < 145:
        raise ValueError("Incomplete source collection: " + str(len(result)) + " rows across " + str(len(countries)) + " countries")
    for required, floor in (("Land", 300), ("Air", 400), ("Naval", 180), ("Personnel", 250), ("Missiles", 50)):
        if per_category.get(required, 0) < floor:
            raise ValueError("Incomplete domain " + required)
    return result, {"countries": len(countries), "records": len(result), "byCategory": per_category}

def main():
    raw = download()
    parsed = parse_verified_csv(raw)
    entries, coverage = make_equipment_entries(parsed)
    data = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if not isinstance(data.get("assets"), list):
        raise ValueError("Published inventory schema missing")
    # Idempotent overwrite: keep FAS nuclear, government estimates and WDI.
    data["assets"] = [x for x in data["assets"] if not x["id"].startswith("dml-")]
    original_ids = set(x["id"] for x in data["assets"])
    if len(original_ids) != len(data["assets"]) or any(x["id"] in original_ids for x in entries):
        raise ValueError("Baseline record collision")
    data["assets"].extend(entries)
    data["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    health = data.get("collectionHealth") or {}
    health["equipment"] = {
        "status": "ok",
        "release": RELEASE,
        "sha256": EXPECTED_SHA256,
        "source": DOWNLOAD_URL,
        "licence": LICENCE,
        "attribution": "DefenseMatrixLab, data release 2026-Q4 (revision 2026-11-21)",
        "confidence": "source-described editorial estimates; not independently validated combat readiness",
        **coverage
    }
    data["collectionHealth"] = health
    data["sources"] = [x for x in data["sources"] if x.get("id") != "dml-equipment"]
    data["sources"].append({
        "id": "dml-equipment",
        "name": "DefenseMatrixLab · 2026-Q4 open military inventories",
        "group": "Research",
        "what": "CC BY 4.0; ~185-country equipment estimates. Pinned revision, observation years and confidence retained. NOT verified operational readiness.",
        "url": SOURCE_PAGE
    })
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUTPUT.parent, delete=False) as tmp:
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.write("\n")
        filename = tmp.name
    os.replace(filename, OUTPUT)
    print("Military equipment accepted:", json.dumps(coverage, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
