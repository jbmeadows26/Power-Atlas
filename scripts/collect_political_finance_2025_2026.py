#!/usr/bin/env python3
"""Bounded public-interest audit of disclosed Congressional PTR transactions.

Primary-source links are checked. No raw Senate reports are republished.
Annual financial holdings are a separate research data product.
"""
import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

INDEX_URL = "https://publicfilings.org/congress/data/feed/index.v1.json"
PART_PREFIX = "https://publicfilings.org/congress/data/feed/"
ALLOWED_OFFICIAL_HOSTS = {"disclosures-clerk.house.gov", "efdsearch.senate.gov"}
REQUIRED_COLS = {"filed", "traded", "name", "bioguide", "chamber", "ticker",
                 "side", "owner", "low", "high", "late", "flags", "doc",
                 "assetType", "txnId"}
OUTPUT = Path("data/research/political-authenticity/congress-trades-2025-2026-summary.json")

def fetch_json(url, limit=2097152):
    if not url.startswith("https://publicfilings.org/congress/data/feed/"):
        raise ValueError("Refusing unapproved external dataset location")
    req = Request(url, headers={"User-Agent": "PowerAtlas/1.0 public-interest evidence audit"})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=25) as response:
                raw = response.read(limit + 1)
                if len(raw) > limit:
                    raise ValueError("Downloaded source exceeds bounded size")
                return json.loads(raw), hashlib.sha256(raw).hexdigest()
        except (HTTPError, URLError, TimeoutError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 2:
                raise
            time.sleep(1 + attempt * 2)

def _day(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None

def _valid_amount(lo, hi):
    if any(isinstance(v, bool) for v in (lo, hi)):
        return False
    return (isinstance(lo, (int, float)) and isinstance(hi, (int, float))
            and lo >= 0 and hi >= lo and hi < 1e15)

def validate_part(descriptor, data, expected_build_id):
    if data.get("dataset_version") != 3 or data.get("build_id") != expected_build_id:
        raise ValueError("Part schema/version/build ID differs from index")
    if data.get("part") != descriptor["part"] or data.get("offset") != descriptor["offset"]:
        raise ValueError("Part identity/offset mismatch")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != descriptor["rows"]:
        raise ValueError("Part count mismatch; refuse partial disclosure publish")
    tx = data.get("txn_cols")
    paper = data.get("paper_cols")
    if not isinstance(tx, list) or not REQUIRED_COLS.issubset(tx) or not isinstance(paper, list):
        raise ValueError("Missing required source schema columns")
    if len(set(tx)) != len(tx):
        raise ValueError("Duplicate transaction column names")
    result = []
    papers = []
    for raw in rows:
        if not isinstance(raw, list) or not raw:
            raise ValueError("Malformed disclosure row")
        if raw[0] == "t":
            if len(raw) != len(tx) + 1:
                raise ValueError("Malformed transaction record length")
            result.append(dict(zip(tx, raw[1:])))
        elif raw[0] == "p":
            if len(raw) != len(paper) + 1:
                raise ValueError("Malformed paper filing record length")
            papers.append(dict(zip(paper, raw[1:])))
        else:
            raise ValueError("Unexpected disclosure row type")
    if len(result) != descriptor["txn_rows"]:
        raise ValueError("Transaction count disagrees with published index")
    return result, papers

def audit(index, parts, as_of=None, minimum_transactions=1000):
    if as_of is None:
        as_of = date.today()
    if index.get("dataset_version") != 3 or not isinstance(index.get("parts"), list):
        raise ValueError("Index version missing or changed")
    selected = [p for p in index["parts"] if p.get("year") in (2025, 2026)]
    if len(selected) != len(parts) or not selected:
        raise ValueError("Expected 2025/2026 parts are missing")
    ordered = sorted(selected, key=lambda p: p["offset"])
    for i, desc in enumerate(ordered[1:], 1):
        if desc["offset"] != ordered[i-1]["offset"] + ordered[i-1]["rows"]:
            raise ValueError("Noncontiguous parts: possible missing rows")
    counts = Counter()
    owners = Counter()
    chambers = Counter()
    filing_years = Counter()
    asset_types = Counter()
    tickers = Counter()
    filers = set()
    tx_ids = set()
    source_docs = set()
    flags = Counter()
    lower_sum = 0
    upper_sum = 0
    lags = []
    abnormal = 0
    incomplete_amounts = 0
    future_dates = 0
    covered_amounts = 0
    paper_count = 0
    primary_doc_invalid = 0
    missing_bioguide = 0
    verified_original_sources = 0
    for descriptor, doc in zip(ordered, parts):
        txs, paper = validate_part(descriptor, doc, index["build_id"])
        paper_count += len(paper)
        filing_years[str(descriptor["year"])] += len(txs)
        for row in txs:
            identity = row.get("txnId")
            if not isinstance(identity, str) or not identity or identity in tx_ids:
                raise ValueError("Missing or duplicate transaction identity; amendments not resolved")
            tx_ids.add(identity)
            v = row.get("bioguide")
            if isinstance(v, str) and re.fullmatch(r"[A-Z][0-9]{6}", v):
                filers.add(v)
            else:
                missing_bioguide += 1
            chambers[str(row.get("chamber") or "unknown")] += 1
            counts[str(row.get("side") or "unknown")] += 1
            owners[str(row.get("owner") or "unknown")] += 1
            asset_types[str(row.get("assetType") or "unknown")] += 1
            symbol = row.get("ticker")
            if isinstance(symbol, str) and re.fullmatch(r"[A-Za-z0-9.\\-]{1,14}", symbol):
                tickers[symbol] += 1
            doc_url = row.get("doc")
            if not isinstance(doc_url, str) or urlsplit(doc_url).scheme != "https" or urlsplit(doc_url).hostname not in ALLOWED_OFFICIAL_HOSTS:
                primary_doc_invalid += 1
            else:
                source_docs.add(doc_url)
                verified_original_sources += 1
            if isinstance(row.get("flags"), list):
                for reason in row["flags"]:
                    flags[str(reason)] += 1
            if _valid_amount(row.get("low"), row.get("high")):
                covered_amounts += 1
                lower_sum += row["low"]
                upper_sum += row["high"]
            else:
                incomplete_amounts += 1
            filed = _day(row.get("filed"))
            traded = _day(row.get("traded"))
            if (filed and filed > as_of) or (traded and traded > as_of):
                future_dates += 1
            if filed and traded:
                lag = (filed - traded).days
                if lag < 0:
                    abnormal += 1
                else:
                    lags.append(lag)
    if len(tx_ids) < minimum_transactions:
        raise ValueError("Insufficient source rows; preserve previous validated summary")
    if primary_doc_invalid:
        raise ValueError("One or more transactions lack an approved official source URL")
    lags.sort()
    median_lag = (lags[(len(lags)-1)//2] if len(lags) % 2 else
                  (lags[len(lags)//2-1] + lags[len(lags)//2]) / 2) if lags else None
    return {
        "schema": "power-atlas.political-authenticity.congressional-trade-aggregate.v1",
        "status": "OBSERVED_SOURCE_LINKED_THIRD_PARTY_PARSED_NOT_INDEPENDENT_FULL_CORPUS_AUDIT",
        "publicationType": "aggregate_public_interest_research_not_trading_service",
        "sourceIndex": INDEX_URL,
        "sourceBuildId": index["build_id"],
        "sourceGeneratedAt": index["generated_at"],
        "asOf": as_of.isoformat(),
        "yearsIncluded": [2025, 2026],
        "sourceParts": [p["part"] for p in ordered],
        "sourcePartCount": len(ordered),
        "transactionRows": len(tx_ids),
        "paperFilingRowsExcludedFromMachineReadTransactions": paper_count,
        "distinctFilersIdentifiedByBioguideId": len(filers),
        "transactionRowsWithMissingBioguide": missing_bioguide,
        "distinctOriginalDocumentLinks": len(source_docs),
        "transactionRowsWithApprovedOfficialDocumentLink": verified_original_sources,
        "chamber": dict(sorted(chambers.items())),
        "side": dict(sorted(counts.items())),
        "owner": dict(sorted(owners.items())),
        "filingYear": dict(sorted(filing_years.items())),
        "assetTypes": dict(asset_types.most_common()),
        "topTickerSymbolsByRows": [{"ticker":k,"rows":v} for k,v in tickers.most_common(12)],
        "amounts": {
            "rowsWithFiniteVerifiedDisclosedRanges": covered_amounts,
            "rowsWithoutFiniteRanges": incomplete_amounts,
            "sumOfLowerBoundsUSDForFiniteRangeRows": lower_sum,
            "sumOfUpperBoundsUSDForFiniteRangeRows": upper_sum
        },
        "timeliness": {
            "rowsWithNonnegativeComparableLag": len(lags),
            "medianTradeToFilingDaysForNonnegativeRows": median_lag,
            "rowsWithLagOver45Days": sum(x > 45 for x in lags),
            "negativeLagRowsExcluded": abnormal,
            "rowsWithAnyFutureDate": future_dates
        },
        "sourceFlags": dict(flags.most_common(20)),
        "limitations": [
            "2025-26 filed-report cohorts, not a sample of all historical trades or a census of current members",
            "House and Senate extraction completeness differ; unreadable paper filings are counted but have no invented transaction rows",
            "Senate source had not refreshed past 2026-10-22 as of index generation, per source publisher",
            "Never interpret filing-year activity as trade-year activity, or absent disclosures as no trading",
            "Reported dollar bands are transaction intervals, not the value of holdings, net worth, financial returns or profits",
            "Missing/open upper range rows are excluded from finite-bound sums, which are only partial totals",
            "Source flags for apparent late filing or date anomalies are screens, not a legal determination",
            "Owner spouse/joint/dependent is not the same as an order personally directed by the member",
            "Underlying official PDFs and Senate filings require spot checks before any individual assertion",
            "Original government disclosure records retain 5 U.S.C. 13107(c) limitations on use"
        ]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUTPUT)
    args = parser.parse_args()
    index, index_sha = fetch_json(INDEX_URL, limit=100000)
    pieces = sorted((p for p in index["parts"] if p.get("year") in (2025, 2026)), key=lambda p: p["offset"])
    data = []
    digests = {}
    for piece in pieces:
        part_id = piece["part"]
        if not re.fullmatch(r"20(25|26)-[1-9][0-9]*", part_id):
            raise ValueError("Unexpected part identifier")
        part, sha = fetch_json(PART_PREFIX + part_id + ".v1.json")
        data.append(part)
        digests[part_id] = sha
        time.sleep(0.1)
    summary = audit(index, data)
    summary["sourceIndexSha256"] = index_sha
    summary["sourcePartSha256"] = digests
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if not args.out.exists() or args.out.read_text(encoding="utf-8") != rendered:
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps({"tradeRows": summary["transactionRows"], "filers": summary["distinctFilersIdentifiedByBioguideId"],
                      "paperUnparsed": summary["paperFilingRowsExcludedFromMachineReadTransactions"],
                      "anomalousTradeDate": summary["timeliness"]["negativeLagRowsExcluded"]}))
if __name__ == "__main__":
    main()
