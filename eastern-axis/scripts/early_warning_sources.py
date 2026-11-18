"""Bounded, attributable FAO and flight-derived GNSS observations.
This module does not characterize interference as deliberate or attribute actors.
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timezone
from io import StringIO
import json
import math
import re

FAO_CSV_URL = "https://www.fao.org/media/docs/worldfoodsituationlibraries/wfs-library/food_price_indices_data.csv"
FAO_SOURCE = "https://www.fao.org/worldfoodsituation/foodpricesindex"
GPS_BASE = "https://api.gpsinterference.com/v1/interference/series/"
GPS_SOURCE = "https://gpsinterference.com/"
# Slugs are part of the provider's documented public country / region taxonomy.
# Regional observations deliberately do not become country-scoped data.
GPS_SCOPES = (
    ("world", "global", "Worldwide"),
    ("united-states", "US", "United States"),
    ("taiwan-strait", "regional:taiwan-strait", "Taiwan Strait"),
    ("persian-gulf", "regional:persian-gulf", "Persian Gulf"),
    ("baltic-sea", "regional:baltic-sea", "Baltic Sea"),
    ("strait-of-hormuz", "regional:strait-of-hormuz", "Strait of Hormuz"),
    ("eastern-mediterranean", "regional:eastern-mediterranean", "Eastern Mediterranean"),
    ("east-asia", "regional:east-asia", "East Asia"),
)
FOOD_COLUMNS = (
    ("food", ("food price index",), "FAO Food Price Index"),
    ("meat", ("meat",), "FAO Meat Price Index"),
    ("dairy", ("dairy",), "FAO Dairy Price Index"),
    ("cereals", ("cereals",), "FAO Cereal Price Index"),
    ("oils", ("oils", "vegetable oils"), "FAO Vegetable Oils Price Index"),
    ("sugar", ("sugar",), "FAO Sugar Price Index"),
)
MONTHS = {name.lower(): index for index, name in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}


def numeric(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("Boolean is not an observation")
    f = float(str(value).strip().replace(",", ""))
    if not math.isfinite(f) or not (0 <= f < 1_000_000):
        raise ValueError("Invalid numeric observation")
    return f


def period(value: object) -> str | None:
    text = str(value or "").strip()
    patterns = (
        r"^(\d{4})[Mm-](\d{1,2})$",
        r"^(\d{4})-(\d{2})-(?:0[1-9]|[12][0-9]|3[01])$",
        r"^(\d{4})/(\d{2})$",
    )
    for pat in patterns:
        m = re.fullmatch(pat, text)
        if m:
            year, mon = map(int, m.groups())
            return f"{year:04d}-{mon:02d}" if 1990 <= year <= date.today().year and 1 <= mon <= 12 else None
    mon = re.fullmatch(r"([A-Za-z]{3,9})[- ]+(\d{4})", text)
    if mon:
        year = int(mon.group(2))
        mm = MONTHS.get(mon.group(1).lower()[:3])
        return f"{year:04d}-{mm:02d}" if mm and 1990 <= year <= date.today().year else None
    return None


def read_fao_csv(raw: bytes) -> list[dict]:
    decoded = raw.decode("utf-8-sig", errors="strict")
    # FAO CSV contains a text preamble in some vintages. Discover the dated header,
    # rather than assuming first line / column order.
    sample = decoded[:8000]
    dialect = csv.excel
    if sample.count(";") > sample.count(",") * 2:
        dialect = csv.excel()
        dialect.delimiter = ";"
    rows = list(csv.reader(StringIO(decoded), dialect=dialect))
    header_at = None
    for i, row in enumerate(rows[:25]):
        cells = [str(x or "").strip().lower() for x in row]
        if any(x == "date" for x in cells) and any("food price index" in x for x in cells):
            header_at = i
            break
    if header_at is None:
        raise ValueError("FAO official index header missing")
    heads = [str(x or "").strip().lower() for x in rows[header_at]]
    date_ix = heads.index("date")
    columns = {}
    for key, aliases, label in FOOD_COLUMNS:
        index = next((i for i, head in enumerate(heads)
                      if head in aliases or any(head.startswith(a+" (") for a in aliases)), None)
        if index is not None:
            columns[key] = (index, label)
    if "food" not in columns or len(columns) < 4:
        raise ValueError("FAO nominal index categories not verified")
    observations = {k: {} for k in columns}
    for row in rows[header_at+1:]:
        if date_ix >= len(row):
            continue
        when = period(row[date_ix])
        if not when or when > date.today().strftime("%Y-%m"):
            continue
        for key, (idx, _) in columns.items():
            if idx >= len(row) or not row[idx].strip():
                continue
            try:
                value = numeric(row[idx])
            except (ValueError, TypeError):
                continue
            if value > 0:
                observations[key][when] = value
    result = []
    for key, points in observations.items():
        dates = sorted(points, reverse=True)
        if len(dates) < 2:
            continue
        latest, previous = dates[:2]
        if (int(latest[:4])*12+int(latest[5:]))-(int(previous[:4])*12+int(previous[5:])) > 2:
            continue
        value, prior = points[latest], points[previous]
        _, label = columns[key]
        result.append({
            "id": "fao-" + key,
            "label": label,
            "value": value,
            "previous": prior,
            "period": latest,
            "previousPeriod": previous,
            "interval": "monthly",
            "unit": "index, 2014–2016=100",
            "group": "global",
            "compareMode": "percent",
            "changePct": round((value/prior-1)*100, 3),
            "changeBps": None,
            "source": "FAO (Food and Agriculture Organization of the United Nations)",
            "sourceUrl": FAO_SOURCE,
        })
    if len(result) < 4 or not any(m["id"] == "fao-food" for m in result):
        raise ValueError("Insufficient FAO dated nominal observations")
    return result


def read_gps_series(raw: bytes, slug: str, group: str, label: str) -> list[dict]:
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("slug") != slug or not isinstance(data.get("days"), list):
        raise ValueError("GPSInterference.com series schema or slug mismatch")
    observations = []
    for row in data["days"]:
        if not isinstance(row, dict):
            continue
        dt = str(row.get("date", ""))
        try:
            when = date.fromisoformat(dt)
            if dt != when.isoformat() or when > date.today():
                continue
            pct = numeric(row.get("pct"))
            hexes = int(row.get("hexes"))
            red, yellow, green = (int(row.get(field)) for field in ("red","yellow","green"))
            aircraft, bad = int(row.get("aircraft")), int(row.get("bad"))
            if hexes < 20 or not (0 <= pct <= 100) or min(red, yellow, green, aircraft, bad) < 0:
                continue
            if red + yellow + green > hexes or bad > aircraft:
                continue
            observations.append((dt,pct,hexes,aircraft))
        except (ValueError, TypeError, OverflowError):
            continue
    observations.sort(key=lambda x:x[0], reverse=True)
    if len(observations) < 2 or observations[0][0] == observations[1][0]:
        raise ValueError("No comparable GPS coverage window")
    newest, previous = observations[:2]
    if (date.today()-date.fromisoformat(newest[0])).days > 5:
        raise ValueError("GNSS sample too old to present as recent")
    change_points = round(newest[1]-previous[1], 2)
    return [{
        "id": "gps-accuracy-"+slug,
        "label": label + " aviation GNSS quality anomaly",
        "value": newest[1],
        "previous": previous[1],
        "period": newest[0],
        "previousPeriod": previous[0],
        "interval": "daily",
        "unit": "% affected sampled hexagons",
        "group": group,
        "compareMode": "percentage-points",
        "changePct": round((newest[1]/previous[1]-1)*100,3) if previous[1]>0 else 0,
        "changePp": change_points,
        "changeBps": None,
        "sampleSize": newest[2],
        "source": "GPSInterference.com (ADS-B-derived estimate; not confirmed jamming)",
        "sourceUrl": GPS_SOURCE,
    }]
