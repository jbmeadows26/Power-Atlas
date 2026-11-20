#!/usr/bin/env python3
"""Publish bounded, source-dated financial-market screens for Eastern Axis.

This is an end-of-day / last-published-data monitor, NOT a live price feed.
Only observed values appear. Missing/stale series are explicit and may not
be used to infer credit contagion or absence of distress.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UTC = dt.timezone.utc
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "public/analysis/financial-markets.json"
SERIES = (
    ("SP500", "S&P 500", "Equities", "index", "S&P Dow Jones Indices", "daily"),
    ("NASDAQCOM", "Nasdaq Composite", "Equities", "index", "Nasdaq, Inc.", "daily"),
    ("VIXCLS", "VIX volatility", "Volatility", "index", "Cboe", "daily"),
    ("BAMLH0A0HYM2", "US high-yield spread", "Credit", "percentage points", "ICE Data Indices, LLC", "daily"),
    ("T10Y2Y", "US 10y–2y Treasury curve", "Rates", "percentage points", "Federal Reserve Bank of St. Louis", "daily"),
    ("STLFSI4", "St. Louis financial stress index", "Credit", "index", "Federal Reserve Bank of St. Louis", "weekly"),
)
SPECS = {item[0]: item for item in SERIES}


def iso_utc(now: dt.datetime) -> str:
    return now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def series_url(series_id: str, start: dt.date) -> str:
    qs = urllib.parse.urlencode({"id": series_id, "cosd": start.isoformat()})
    return "https://fred.stlouisfed.org/graph/fredgraph.csv?" + qs


def parse_csv(raw: str, series_id: str, today: dt.date) -> list[tuple[str, float]]:
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or series_id not in reader.fieldnames:
        raise ValueError("Unexpected FRED CSV columns for " + series_id)
    date_col = "observation_date" if "observation_date" in reader.fieldnames else "DATE"
    if date_col not in reader.fieldnames:
        raise ValueError("Missing observation date column")
    seen: dict[str, float] = {}
    for row in reader:
        day = row.get(date_col, "").strip()
        try:
            day_parsed = dt.date.fromisoformat(day)
            value = float((row.get(series_id) or "").strip())
        except (ValueError, AttributeError):
            continue
        if day_parsed > today or not math.isfinite(value):
            continue
        seen[day] = value
    return sorted(seen.items())


def build_metric(spec: tuple[str, str, str, str, str, str],
                 observations: list[tuple[str, float]], checked_at: str,
                 today: dt.date) -> dict:
    sid, label, group, unit, provider, cadence = spec
    if not observations:
        raise ValueError("No numeric observations")
    latest = observations[-1]
    age = (today - dt.date.fromisoformat(latest[0])).days
    max_age = 17 if cadence == "weekly" else 7
    previous = observations[-2] if len(observations) > 1 else None
    prior_five = observations[-6] if len(observations) > 5 else None
    last_60 = observations[-60:]
    peak = max(val for _, val in last_60) if group == "Equities" else None
    pct = lambda before: round((latest[1] / before - 1) * 100, 2) if before not in (None, 0) else None
    return {
        "id": sid, "label": label, "group": group, "unit": unit,
        "value": round(latest[1], 4), "period": latest[0],
        "previous": round(previous[1], 4) if previous else None,
        "previousPeriod": previous[0] if previous else None,
        "change1Pct": pct(previous[1]) if previous else None,
        "change5Pct": pct(prior_five[1]) if prior_five else None,
        "change5Points": round(latest[1] - prior_five[1], 4) if prior_five else None,
        "drawdown60Pct": round((latest[1] / peak - 1) * 100, 2) if peak and peak > 0 else None,
        "history": [{"date": date, "value": round(value, 4)} for date, value in observations[-30:]],
        "source": "FRED / " + provider,
        "sourceUrl": "https://fred.stlouisfed.org/series/" + sid,
        "provider": provider, "cadence": cadence, "checkedAt": checked_at,
        "status": "stale" if age > max_age else "ok",
        "ageDays": age,
    }


def derive_signals(metrics: list[dict]) -> list[dict]:
    # Only fresh series may establish an alert. A signal is a SCREEN, not
    # a calibrated forecast or evidence of defaults or lender impairment.
    by_id = {m["id"]: m for m in metrics if m["status"] == "ok"}
    sp = by_id.get("SP500")
    nd = by_id.get("NASDAQCOM")
    hy = by_id.get("BAMLH0A0HYM2")
    vix = by_id.get("VIXCLS")
    output = []

    correction = any(
        m is not None and m["drawdown60Pct"] is not None and m["drawdown60Pct"] <= -10
        for m in (sp, nd)
    )
    broad = all(
        m is not None and m["change5Pct"] is not None and m["change5Pct"] <= -3
        for m in (sp, nd)
    )
    if correction or broad:
        output.append({
            "id": "equity-stress", "domain": "Equities", "level": "watch",
            "title": "Equity correction / broad selloff screen",
            "explanation": "Recent benchmark declines exceed disclosed screens; this is not evidence of loan defaults.",
            "evidenceIds": [m["id"] for m in (sp, nd) if m is not None],
            "rule": "S&P 500 or Nasdaq >10% below 60-observation peak, OR both fall >=3% over five observations.",
        })
    if vix is not None and vix["value"] >= 30:
        output.append({
            "id": "volatility-stress", "domain": "Volatility", "level": "watch",
            "title": "Elevated implied equity volatility",
            "explanation": "VIX is elevated, but volatility is not proof of contagion.",
            "evidenceIds": ["VIXCLS"], "rule": "VIX >= 30 at last published observation.",
        })
    if hy is not None and hy["change5Points"] is not None and hy["change5Points"] >= 0.5:
        output.append({
            "id": "credit-spread-stress", "domain": "Credit", "level": "watch",
            "title": "High-yield credit-spread widening",
            "explanation": "A broad credit-price screen, not verified borrower defaults or lender impairment.",
            "evidenceIds": ["BAMLH0A0HYM2"],
            "rule": "ICE BofA US high-yield option-adjusted spread widens >=50 basis points across five observations.",
        })
    if any(s["id"] == "equity-stress" for s in output) and any(
        s["id"] == "credit-spread-stress" for s in output
    ):
        output.append({
            "id": "cross-market-stress", "domain": "Cross-market", "level": "investigate",
            "title": "Equity AND high-yield spread stress",
            "explanation": "Correlated price screens warrant investigation. Systemic credit contagion is unverified.",
            "evidenceIds": ["SP500", "NASDAQCOM", "BAMLH0A0HYM2"],
            "rule": "Both equity-stress and credit-spread-stress screens breached on fresh observations.",
        })
    return output


def collect(now: dt.datetime | None = None, fetcher=None) -> dict:
    now = now or dt.datetime.now(UTC)
    today = now.date()
    checked_at = iso_utc(now)
    start = today - dt.timedelta(days=160)
    metrics, sources = [], []
    def download(url):
        req = urllib.request.Request(url, headers={
            "User-Agent": "EasternAxis-Research/1.0 public-source-monitor",
            "Accept": "text/csv",
        })
        with urllib.request.urlopen(req, timeout=17) as response:
            return response.read(2_000_001).decode("utf-8-sig")
    fetcher = fetcher or download
    for spec in SERIES:
        sid = spec[0]
        url = series_url(sid, start)
        try:
            raw = fetcher(url)
            if len(raw) > 2_000_000:
                raise ValueError("Response too large")
            metric = build_metric(spec, parse_csv(raw, sid, today), checked_at, today)
            metrics.append(metric)
            status = metric["status"]
            detail = "Latest observation " + metric["period"]
        except (OSError, UnicodeError, ValueError, KeyError) as exc:
            status, detail = "error", str(exc)[:180]
        sources.append({"id": sid, "status": status, "detail": detail,
                        "sourceUrl": "https://fred.stlouisfed.org/series/" + sid,
                        "checkedAt": checked_at})
    observed = sum(m["status"] == "ok" for m in metrics)
    return {
        "schemaVersion": 1, "checkedAt": checked_at,
        "status": "ok" if observed == len(SERIES) else "partial" if observed else "unavailable",
        "scope": "US benchmark financial market conditions; not country-specific",
        "cadence": "Scheduled 6-hour collection; most series publish daily and the stress index weekly. Not intraday quotes.",
        "metrics": metrics, "signals": derive_signals(metrics), "sources": sources,
        "limitations": [
            "Equity market capitalization losses are not cash outflows, defaults or loan impairment.",
            "No direct private-credit loan tapes, funding agreements, guarantees, margin calls, bank exposures or household losses are ingested.",
            "Index and option-adjusted spread data are provided by their original owners via FRED; source terms may restrict reuse.",
            "A 60-observation high is not an all-time high; dates are source observations, not collection timestamps.",
            "Screens are investigative leads and cannot establish a systemic credit crisis or recession.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--strict", action="store_true",
                        help="Fail when insufficient fresh readings to publish a credible market panel.")
    args = parser.parse_args()
    snapshot = collect()
    if args.strict and sum(m["status"] == "ok" for m in snapshot["metrics"]) < 3:
        print("Refusing to publish a mostly unavailable market snapshot")
        for item in snapshot["sources"]:
            print(item["id"], item["status"], item["detail"])
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(snapshot["status"], "fresh:", sum(m["status"] == "ok" for m in snapshot["metrics"]),
          "signals:", len(snapshot["signals"]), "output:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
