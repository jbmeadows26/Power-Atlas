#!/usr/bin/env python3
"""Collect official HUD FY2026 Small Area Fair Market Rents from HUD's ArcGIS service.

No API key. Reconciles ArcGIS pagination, preserves ZIP-to-HUD-area one-to-many
relationships and refuses to overwrite a valid snapshot with partial responses.
SAFMR is a HUD program benchmark, NOT observed asking rent or median paid rent.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = ("https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/"
        "HUD_PDR_Small_Area_Fair_Market_Rents/FeatureServer")
TABLE = BASE + "/1"
QUERY = TABLE + "/query"
FIELDS = ["OBJECTID", "ID", "ZCTA_ID", "HUD_CODE", "FMR_NAME",
          "SAFMR_0BR", "SAFMR_1BR", "SAFMR_2BR", "SAFMR_3BR", "SAFMR_4BR"]
OUT = Path(__file__).resolve().parents[1] / "data/housing/hud-safmr-fy2026-v1.json"

def get_json(path, **params):
    uri = path + "?" + urllib.parse.urlencode({"f": "json", **params})
    last = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(uri, headers={
                "User-Agent": "PowerAtlas-Research/1.0 (public noncommercial HUD data audit)",
                "Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=35) as response:
                out = json.load(response)
            if isinstance(out, dict) and out.get("error"):
                raise ValueError("ArcGIS error: " + str(out["error"])[:350])
            if not isinstance(out, dict):
                raise ValueError("Expected ArcGIS JSON object")
            return out
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last = error
            if attempt != 3:
                time.sleep(1.5 * 2 ** attempt)
    raise RuntimeError("HUD source request failed: " + str(last))

def parse_row(attrs):
    zip_ = attrs.get("ZCTA_ID") or attrs.get("ID")
    if attrs.get("ZCTA_ID") and attrs.get("ID") and attrs["ZCTA_ID"] != attrs["ID"]:
        raise ValueError("HUD ZIP keys conflict; inspect ArcGIS relationship")
    if not isinstance(zip_, str) or len(zip_) != 5 or not zip_.isdigit():
        return None
    if not attrs.get("HUD_CODE") or not attrs.get("FMR_NAME"):
        return None
    values = {}
    for n in range(5):
        raw = attrs.get("SAFMR_" + str(n) + "BR")
        if raw is None:
            values[str(n)] = None
        elif isinstance(raw, (int, float)) and not isinstance(raw, bool) and 100 <= raw <= 15000:
            values[str(n)] = int(raw) if int(raw) == raw else raw
        else:
            raise ValueError("Invalid HUD bedroom rent for " + zip_)
    if values["1"] is None or values["2"] is None:
        return None
    return {"zip": zip_, "hudCode": str(attrs["HUD_CODE"]),
            "hudArea": str(attrs["FMR_NAME"]).strip(),
            "usdByBedroom": values}

def collect():
    service = get_json(BASE)
    desc = " ".join([str(service.get("serviceDescription") or ""),
                     str(service.get("description") or "")])
    if "2026" not in desc:
        raise RuntimeError("HUD service no longer identifies FY2026; refuse misdated download")
    table = get_json(TABLE)
    field_names = {f.get("name") for f in table.get("fields", [])}
    if not set(FIELDS).issubset(field_names):
        raise RuntimeError("HUD table schema changed: " + str(set(FIELDS) - field_names))
    count = get_json(QUERY, where="1=1", returnCountOnly="true").get("count")
    if not isinstance(count, int) or count < 1000:
        raise RuntimeError("HUD returned suspicious record count: "+repr(count))
    seen, rows, skipped = set(), [], 0
    for offset in range(0, count, 900):
        payload = get_json(QUERY, where="1=1", outFields=",".join(FIELDS),
                           orderByFields="OBJECTID ASC", resultOffset=offset,
                           resultRecordCount=900, returnGeometry="false")
        features = payload.get("features")
        if not isinstance(features, list) or len(features) != min(900, count-offset):
            raise RuntimeError("Partial or mispaginated HUD response at offset " + str(offset))
        for feature in features:
            attrs = feature.get("attributes") if isinstance(feature, dict) else None
            if not isinstance(attrs, dict) or attrs.get("OBJECTID") in seen:
                raise RuntimeError("HUD duplicate or missing object ID")
            seen.add(attrs["OBJECTID"])
            record = parse_row(attrs)
            if record:
                rows.append(record)
            else:
                skipped += 1
        time.sleep(0.08)
    if len(seen) != count or len(rows) < 1000:
        raise RuntimeError("Incomplete HUD import: " + str((len(seen), len(rows), count)))
    rows.sort(key=lambda r: (r["zip"], r["hudCode"]))
    return {
        "schema": "power-atlas.hud-fy2026-safmr-v1",
        "publicationStatus": "verified_original_program_benchmark_not_market_rent",
        "fiscalYear": 2026,
        "source": BASE,
        "table": TABLE,
        "sourceLastEditEpochMs": table.get("editingInfo", {}).get("lastEditDate"),
        "retrievedUTC": datetime.now(timezone.utc).isoformat(),
        "sourceObjectCount": count,
        "validSourceRelations": len(rows),
        "excludedIncompleteRelations": skipped,
        "uniqueZctas": len({r["zip"] for r in rows}),
        "grain": "ZIP Code Tabulation Area × HUD-defined FMR area",
        "joinKey": "Layer 1 ID (ZCTA_ID is null); ArcGIS relationship to layer 0 ZCTA5CE20",
        "geographicLimitation": ("A ZCTA can intersect multiple HUD metropolitan areas; do not "
                                 "collapse distinct records, assume precise ZIP boundaries, or "
                                 "assign legal jurisdiction from a ZCTA."),
        "measure": "HUD FY2026 Small Area Fair Market Rent, USD per month by bedroom count",
        "interpretation": ("HUD Housing Choice Voucher benchmark, not current asking rent, "
                           "median rent paid, a family bill, or a causal ownership effect."),
        "rows": rows,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    options = parser.parse_args()
    data = collect()
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False)+"\n",
                              encoding="utf-8")
    for digit in "0123456789":
        selected = [r for r in data["rows"] if r["zip"].startswith(digit)]
        shard = {key: value for key, value in data.items() if key != "rows"}
        shard["schema"] = "power-atlas.hud-fy2026-safmr-shard-v1"
        shard["prefix"] = digit
        shard["validSourceRelations"] = len(selected)
        shard["rows"] = selected
        target = options.output.parent / ("hud-safmr-fy2026-" + digit + ".json")
        target.write_text(json.dumps(shard, separators=(",", ":"), ensure_ascii=False)+"\n",
                          encoding="utf-8")
    print(json.dumps({k: data[k] for k in ("fiscalYear", "sourceObjectCount",
               "validSourceRelations", "excludedIncompleteRelations", "uniqueZctas")}))

if __name__ == "__main__":
    main()
