#!/usr/bin/env python3
"""Public-source financial transmission layer: FRED households and SEC issuer filings.

No claim of individual private-credit performance, real-time stock prices, or
causation from an equity correction. A failed source stays unavailable.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

UTC = dt.timezone.utc
HERE = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = HERE / "public/analysis/financial-transmission.json"
USER_AGENT = "EasternAxisOpenIntelligence/1.0 eastern-axis-data@agentmail.to (https://github.com/jbmeadows26/Power-Atlas)"
HOUSEHOLD_SERIES = (
    # series, label, domain, cadence, unit, primary data producer
    ("DRCCLACBS", "Credit-card loan delinquency", "Households", "quarterly", "% loans", "Federal Reserve Board"),
    ("TDSP", "Household debt-service burden", "Households", "quarterly", "% disposable income", "Federal Reserve Board"),
    ("PSAVERT", "Personal saving rate", "Households", "monthly", "% disposable income", "Bureau of Economic Analysis"),
    ("UNRATE", "Unemployment rate", "Labor", "monthly", "% labor force", "Bureau of Labor Statistics"),
    ("ICSA", "Initial jobless claims", "Labor", "weekly", "persons", "US Department of Labor"),
    ("DRTSCILM", "C&I bank lending standards", "Credit", "quarterly", "net % tightening", "Federal Reserve Board"),
    ("BAMLC0A0CM", "Investment-grade credit spread", "Credit", "daily", "percentage points", "ICE Data Indices, LLC"),
    ("DRBLACBS", "Bank business-loan delinquency", "Credit", "quarterly", "% loans", "Federal Reserve Board"),
    ("QBPLNTLNNCUR", "FDIC noncurrent loan rate", "Credit", "quarterly", "% loans", "Federal Deposit Insurance Corporation"),
)
TICKERS = ("ANT", "NVDA", "MSFT", "GOOGL", "META", "AMZN", "ORCL", "AMD", "AVGO", "CRWV", "ARCC", "OBDC", "BXSL", "GBDC")
BDC_TICKERS = {"ARCC", "OBDC", "BXSL", "GBDC"}
# Official CIKs confirmed against issuer SEC filings; only a fallback when
# the public ticker lookup is unavailable (per-filer submissions still probed).
VERIFIED_CIKS = {"ANT": 2130357, "NVDA": 1045810, "ARCC": 1287750,
                 "OBDC": 1655888, "BXSL": 1736035, "GBDC": 1476765}
ITEMS = {
    "1.03": ("Bankruptcy or receivership", "filing-review"),
    "2.04": ("Debt acceleration / obligation trigger", "filing-review"),
    "2.03": ("New direct financial obligation", "financing-context"),
}
FRED_MAX_AGE = {"daily": 8, "weekly": 22, "monthly": 110, "quarterly": 270}
SEC_CIK_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_BASE = "https://data.sec.gov"
SAFE_DOC = re.compile(r"^[A-Za-z0-9._-]+$")
ITEM_REGEX = re.compile(r"\b(?:1\.03|2\.04|2\.03)\b")


def utc_stamp(now: dt.datetime) -> str:
    return now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def http_text(url: str, accept: str = "application/json", cap: int = 7_000_000) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=18) as response:
        payload = response.read(cap + 1)
    if len(payload) > cap:
        raise ValueError("Response exceeded bounded source size")
    return payload.decode("utf-8-sig")


def parse_fred_csv(raw: str, series: str, today: dt.date) -> list[tuple[str, float]]:
    reader = csv.DictReader(io.StringIO(raw))
    col = "observation_date" if reader.fieldnames and "observation_date" in reader.fieldnames else "DATE"
    if not reader.fieldnames or series not in reader.fieldnames or col not in reader.fieldnames:
        raise ValueError("Invalid FRED CSV schema for " + series)
    values: dict[str, float] = {}
    for line in reader:
        try:
            period = str(line[col]).strip()
            d = dt.date.fromisoformat(period)
            value = float(line[series])
        except (TypeError, ValueError, KeyError):
            continue
        if d > today or not math.isfinite(value):
            continue
        values[period] = value
    return sorted(values.items())


def household_metric(spec, observations: list[tuple[str, float]], checked: str, today: dt.date) -> dict:
    sid, label, domain, cadence, unit, producer = spec
    if not observations:
        raise ValueError("No numeric values from " + sid)
    latest = observations[-1]
    previous = observations[-2] if len(observations) >= 2 else None
    age = (today - dt.date.fromisoformat(latest[0])).days
    return {
        "id": sid, "label": label, "domain": domain, "cadence": cadence, "unit": unit,
        "value": round(latest[1], 5), "period": latest[0],
        "previous": round(previous[1], 5) if previous else None,
        "previousPeriod": previous[0] if previous else None,
        "changePoints": round(latest[1] - previous[1], 5) if previous else None,
        "status": "stale" if age > FRED_MAX_AGE[cadence] else "ok",
        "periodAgeDays": age, "source": "FRED / " + producer,
        "sourceUrl": "https://fred.stlouisfed.org/series/" + sid,
        "history": [{"date": date, "value": round(value, 5)} for date, value in observations[-16:]],
        "checkedAt": checked,
    }


def collect_households(now: dt.datetime, fetch=http_text):
    checked, today = utc_stamp(now), now.date()
    since = (today - dt.timedelta(days=900)).isoformat()
    result, sources = [], []
    for spec in HOUSEHOLD_SERIES:
        sid = spec[0]
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?" + urllib.parse.urlencode({"id": sid, "cosd": since})
        try:
            observations = parse_fred_csv(fetch(url, "text/csv"), sid, today)
            metric = household_metric(spec, observations, checked, today)
            result.append(metric)
            status, detail = metric["status"], "Last observation period " + metric["period"]
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as err:
            status, detail = "error", str(err)[:150]
        sources.append({"id": "fred:" + sid, "status": status, "detail": detail,
                        "sourceUrl": "https://fred.stlouisfed.org/series/" + sid, "checkedAt": checked})
    return result, sources


def parse_company_tickers(payload: dict, tickers=TICKERS) -> dict:
    allowed = set(tickers)
    result = {}
    for row in payload.values():
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker")
        cik = row.get("cik_str")
        name = row.get("title")
        if ticker in allowed and isinstance(cik, int) and cik > 0 and isinstance(name, str):
            result[ticker] = {"ticker": ticker, "cik": cik, "name": name}
    return result


def sec_filing_url(cik: int, accession: str, primary_document: str) -> str | None:
    if not accession or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        return None
    if not primary_document or not SAFE_DOC.fullmatch(primary_document) or primary_document in (".", ".."):
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{primary_document}"


def parse_sec_filings(payload: dict, company: dict, today: dt.date) -> tuple[list[dict], dict | None]:
    recent = payload.get("filings", {}).get("recent", {})
    if not isinstance(recent, dict) or not isinstance(recent.get("accessionNumber"), list):
        raise ValueError("Unexpected SEC submissions schema")
    columns = ("accessionNumber", "form", "filingDate", "primaryDocument", "items")
    rows = len(recent["accessionNumber"])
    if not all(isinstance(recent.get(key), list) and len(recent[key]) >= rows for key in columns):
        raise ValueError("Incomplete SEC filings index")
    filings = []
    latest_report = None
    cutoff = today - dt.timedelta(days=120)
    for i in range(rows):
        accession = str(recent["accessionNumber"][i])
        form = str(recent["form"][i])
        period = str(recent["filingDate"][i])
        document = str(recent["primaryDocument"][i])
        try:
            filing_day = dt.date.fromisoformat(period)
        except ValueError:
            continue
        if filing_day > today:
            continue
        url = sec_filing_url(company["cik"], accession, document)
        if not url:
            continue
        if form in ("10-K", "10-Q", "20-F") and (latest_report is None or period > latest_report["filed"]):
            latest_report = {"form": form, "filed": period, "url": url}
        if form not in ("8-K", "8-K/A") or filing_day < cutoff:
            continue
        raw_items = str(recent["items"][i])
        item_codes = set(ITEM_REGEX.findall(raw_items))
        for code in sorted(item_codes):
            title, classification = ITEMS[code]
            filings.append({
                "id": company["ticker"] + ":" + accession + ":" + code,
                "ticker": company["ticker"], "company": company["name"],
                "filed": period, "item": code, "title": title,
                "classification": classification, "source": "SEC EDGAR",
                "sourceUrl": url, "accessionNumber": accession,
                "note": "SEC item-coded disclosure: read the actual filing before attributing a default or loss.",
            })
    filings.sort(key=lambda row: (row["filed"], row["ticker"]), reverse=True)
    return filings[:25], latest_report


def latest_stock_fact(companyfacts: dict, tag_names: tuple[str, ...], today: dt.date):
    usgaap = companyfacts.get("facts", {}).get("us-gaap", {})
    candidates = []
    for tag in tag_names:
        values = usgaap.get(tag, {}).get("units", {}).get("USD", [])
        for row in values:
            if row.get("form") not in ("10-K", "10-Q") or "start" in row:
                continue
            if not isinstance(row.get("val"), (int, float)) or not math.isfinite(row["val"]):
                continue
            try:
                end, filed = dt.date.fromisoformat(row["end"]), dt.date.fromisoformat(row["filed"])
            except (TypeError, ValueError, KeyError):
                continue
            if end > today or filed > today:
                continue
            candidates.append((end, filed, tag, row))
    if not candidates:
        return None
    end, filed, tag, row = max(candidates, key=lambda v: (v[0], v[1], v[2]))
    return {
        "valueUSD": round(row["val"]), "periodEnd": end.isoformat(),
        "filed": filed.isoformat(), "form": row["form"], "taxonomyTag": tag,
        "sourceUrl": f"https://www.sec.gov/Archives/edgar/data/{int(companyfacts['cik'])}/{row['accn'].replace('-', '')}/"
                     if re.fullmatch(r"\d{10}-\d{2}-\d{6}", str(row.get("accn", ""))) else None,
    }


def parse_company_facts(payload: dict, today: dt.date) -> dict:
    return {
        "cash": latest_stock_fact(payload, ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"), today),
        "longTermDebt": latest_stock_fact(payload, ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"), today),
        "note": "USD balance-sheet amounts. Cash and debt may use different taxonomy definitions and report dates; no net-debt or leverage ratio inferred.",
    }


def collect_sec(now: dt.datetime, fetch=http_text, sleep=time.sleep):
    today, checked = now.date(), utc_stamp(now)
    records, issuers, sources = [], [], []
    try:
        companies = parse_company_tickers(json.loads(fetch(SEC_CIK_MAP_URL)))
        if not companies:
            raise ValueError("SEC ticker index returned no watchlist companies")
        sources.append({"id": "sec:tickers", "status": "ok", "detail": str(len(companies)) + " mapped watchlist symbols",
                        "sourceUrl": SEC_CIK_MAP_URL, "checkedAt": checked})
    except (OSError, UnicodeError, ValueError, TypeError) as err:
        companies = {ticker: {"ticker": ticker, "cik": cik, "name": ticker, "cikSource": "SEC-filed CIK cross-reference"}
                     for ticker, cik in VERIFIED_CIKS.items()}
        sources.append({"id": "sec:tickers", "status": "error", "detail": str(err)[:180],
                        "sourceUrl": SEC_CIK_MAP_URL, "checkedAt": checked})
    for ticker in TICKERS:
        company = companies.get(ticker)
        if not company:
            issuers.append({"ticker": ticker, "sector": "Listed private-credit BDC" if ticker in BDC_TICKERS else "AI ecosystem",
                            "status": "unavailable", "name": ticker,
                            "cik": None, "latestReport": None, "balanceSheet": None})
            sources.append({"id": "sec:" + ticker, "status": "error", "detail": "CIK mapping unavailable",
                            "checkedAt": checked, "sourceUrl": SEC_CIK_MAP_URL})
            continue
        sleep(0.14)  # Always remain comfortably below SEC 10 requests/second.
        url = f"{EDGAR_BASE}/submissions/CIK{company['cik']:010d}.json"
        entry = {**company, "sector": "Listed private-credit BDC" if ticker in BDC_TICKERS else "AI ecosystem",
                 "status": "unavailable", "sourceUrl": url,
                 "latestReport": None, "balanceSheet": None}
        try:
            filing_payload = json.loads(fetch(url))
            found, latest_report = parse_sec_filings(filing_payload, company, today)
            entry["latestReport"] = latest_report
            entry["status"] = "ok"
            records.extend(found)
            status, detail = "ok", "Recent SEC filings indexed"
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as err:
            status, detail = "error", str(err)[:160]
        sources.append({"id": "sec:" + ticker, "status": status, "detail": detail,
                        "sourceUrl": url, "checkedAt": checked})
        if status == "ok":
            sleep(0.14)
            fact_url = f"{EDGAR_BASE}/api/xbrl/companyfacts/CIK{company['cik']:010d}.json"
            try:
                facts = json.loads(fetch(fact_url))
                entry["balanceSheet"] = parse_company_facts(facts, today)
                sources.append({"id": "sec:xbrl:" + ticker, "status": "ok",
                                "detail": "Filed US-GAAP facts checked", "checkedAt": checked, "sourceUrl": fact_url})
            except (OSError, UnicodeError, ValueError, TypeError, KeyError) as err:
                sources.append({"id": "sec:xbrl:" + ticker, "status": "error",
                                "detail": str(err)[:160], "checkedAt": checked, "sourceUrl": fact_url})
        issuers.append(entry)
    records.sort(key=lambda v: (v["filed"], v["ticker"]), reverse=True)
    return issuers, records, sources


def derive_alerts(fred: list[dict], filings: list[dict], today: dt.date) -> list[dict]:
    by_id = {m["id"]: m for m in fred if m["status"] == "ok"}
    alerts = []
    ig = by_id.get("BAMLC0A0CM")
    if ig is not None and ig["changePoints"] is not None and ig["changePoints"] >= 0.25:
        alerts.append({"id": "ig-spread-widening", "domain": "Credit", "level": "watch",
                       "title": "Investment-grade spread widened",
                       "rule": ">=25 basis points since prior daily observation",
                       "evidenceIds": ["BAMLC0A0CM"], "claim": "Broad spread screen, not direct private-credit defaults."})
    credit = by_id.get("DRCCLACBS")
    if credit is not None and credit["changePoints"] is not None and credit["changePoints"] >= 0.3:
        alerts.append({"id": "card-delinquency", "domain": "Households", "level": "watch",
                       "title": "Credit-card delinquency deteriorated",
                       "rule": ">=0.3 percentage points between quarterly reported periods",
                       "evidenceIds": ["DRCCLACBS"],
                       "claim": "Observed broad bank-loan distress proxy; not attributed to AI equity prices."})
    biz = by_id.get("DRBLACBS")
    if biz is not None and biz["changePoints"] is not None and biz["changePoints"] >= 0.3:
        alerts.append({"id": "business-delinquency", "domain": "Credit", "level": "watch",
                       "title": "Business-loan delinquency deterioration",
                       "rule": ">=0.30 percentage points between published quarterly observations",
                       "evidenceIds": ["DRBLACBS"],
                       "claim": "Bank business-loan aggregate, not loan-by-loan private-credit defaults."})
    stress = [f for f in filings if f["item"] in ("1.03", "2.04")
              and (today - dt.date.fromisoformat(f["filed"])).days <= 30]
    if stress:
        alerts.append({"id": "sec-disclosure-review", "domain": "Issuer disclosures", "level": "investigate",
                       "title": "SEC financial-obligation / bankruptcy disclosure requires review",
                       "rule": "Recent item 1.03 or 2.04 on a watchlist issuer 8-K; inspect primary filing",
                       "evidenceIds": [f["id"] for f in stress],
                       "claim": "SEC item metadata alone does not establish missed payments, private-credit defaults or losses."})
    return alerts


def collect(now: dt.datetime | None = None, fred_fetch=http_text, sec_fetch=http_text, sleep=time.sleep) -> dict:
    now = now or dt.datetime.now(UTC)
    fred, fred_sources = collect_households(now, fetch=fred_fetch)
    issuers, filings, sec_sources = collect_sec(now, fetch=sec_fetch, sleep=sleep)
    sources = fred_sources + sec_sources
    good_fred = sum(m["status"] == "ok" for m in fred)
    good_sec = sum(e["status"] == "ok" for e in issuers)
    return {
        "schemaVersion": 1, "checkedAt": utc_stamp(now),
        "status": "ok" if good_fred == len(HOUSEHOLD_SERIES) and good_sec == len(TICKERS) else
                  "partial" if (good_fred or good_sec) else "unavailable",
        "scope": "US household/lending indicators, AI issuers and publicly listed private-credit BDCs",
        "householdMetrics": fred, "issuers": issuers,
        "filings": filings[:90],
        "signals": derive_alerts(fred, filings, now.date()),
        "sources": sources,
        "intradayQuotes": {
            "status": "not-connected", "coverage": [],
            "reason": "No verified public-redistribution market-data license and authorized API feed are configured. Intraday share prices are not fabricated or scraped.",
            "requirements": "An approved data vendor API, secure GitHub Actions credential and written public-display/redistribution entitlement.",
        },
        "coverage": {
            "creditDefaults": "Public SEC 8-K event metadata for watchlist issuers only; not private-credit loan-level defaults, guarantees or realized lender losses.",
            "households": "Published US aggregate indicators only; neither individual portfolio returns nor AI-specific causal household harm.",
            "issuers": "Public AI issuers and four listed business-development-company lenders. CIK-mapped public filings and selected US-GAAP balance-sheet facts; not direct underlying loan performance or issuer stock prices.",
        },
        "limitations": [
            "Freshness is evaluated against the ORIGINAL observation period; quarterly time-series observation dates are quarter starts, not publication timestamps.",
            "This monitor does not read private credit agreements or infer that an event-coded 8-K is a default.",
            "SEC watchlist is intentionally bounded; absent filings are not proof of no defaults elsewhere.",
            "Government rates and filings measure broad conditions or company disclosures, not impacts caused by an AI selloff.",
            "Unlicensed exchange quotes and individual household data remain explicitly unconnected.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--strict", action="store_true",
                        help="Fail if fewer than 4 FRED indicators have current reported observations.")
    args = parser.parse_args()
    snapshot = collect()
    good = sum(m["status"] == "ok" for m in snapshot["householdMetrics"])
    if args.strict and good < 4:
        print("Insufficient current FRED household/credit observations: refusing replacement of verified snapshot")
        for row in snapshot["sources"]:
            print(row["id"], row["status"], row["detail"])
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Financial transmission:", snapshot["status"], "household:", good,
          "SEC issuers:", sum(i["status"] == "ok" for i in snapshot["issuers"]),
          "disclosure records:", len(snapshot["filings"]), "file:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
