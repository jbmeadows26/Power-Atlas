"""Bounded, provenance-preserving probe of four state keyword-result gaps.

Run once within the Oct 30 sprint. Sample at most five search hits per
jurisdiction; request bill detail only when the search hit lacks a usable
official-source URL. No login, rate-limit bypass, full text or donor data.
A successful query is not an exhaustive state bill inventory.
"""
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import json
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from expand_state_bill_coverage import record

ROOT = Path(__file__).resolve().parents[1]
BILLS = ROOT / "data/legislation/state-redistricting-bills.json"
CHECKPOINT = ROOT / "data/legislation/state-redistricting-jurisdictions.json"
AUDIT = ROOT / "data/health/state-bill-record-filter-audit.json"
BASE = "https://api.billcommons.org/api/v1"
STATES = ("CA", "MD", "OK", "VT")
PER_PAGE = 5
MAX_DETAILS_PER_STATE = 2
MAX_BYTES = 90000
END = date(2026, 10, 30)
UUID = re.compile(r"[0-9a-fA-F-]{36}\Z")


def reject_reason(raw):
    if not isinstance(raw, dict):
        return "invalid_record"
    if not UUID.fullmatch(str(raw.get("id") or "")):
        return "missing_or_invalid_uuid"
    if not str(raw.get("title") or "").strip():
        return "missing_title"
    if not str(raw.get("identifier") or "").strip():
        return "missing_identifier"
    source = str(raw.get("source_url") or "")
    if not source:
        return "missing_source_url"
    if not source.startswith("https://"):
        return "non_https_source_url"
    return None


def get_json(url):
    req = Request(url, headers={
        "User-Agent": "PowerAtlasPublicResearch/1.0 bounded source-link audit",
        "Accept": "application/json"})
    with urlopen(req, timeout=16) as response:
        if response.status != 200:
            raise ValueError("unexpected_http_status")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("response_exceeds_size_cap")
    return json.loads(raw)


def detail_source(raw, get=get_json):
    """Only the same bill UUID may supply a missing official source URL."""
    uid = str(raw.get("id") or "")
    if not UUID.fullmatch(uid):
        return None
    detail = get(BASE + "/bills/" + uid)
    if not isinstance(detail, dict):
        return None
    detail = detail.get("data", detail)
    if not isinstance(detail, dict) or str(detail.get("id") or "") != uid:
        return None
    url = str(detail.get("source_url") or "")
    return url if url.startswith("https://") else None


def process_state(state, indexed, get=get_json):
    url = BASE + "/search?" + urlencode({
        "q": "redistricting", "jurisdiction": state,
        "page": 1, "per_page": PER_PAGE})
    payload = get(url)
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) > PER_PAGE:
        raise ValueError("unexpected_search_result_schema")
    rejected = Counter()
    new_rows = 0
    detail_requests = 0
    detail_failures = 0
    non_https_schemes = Counter()
    non_https_hosts = Counter()
    pending = {}
    for raw in rows:
        reason = reject_reason(raw)
        if reason == "non_https_source_url":
            parsed_url = urlparse(str(raw.get("source_url") or ""))
            non_https_schemes[parsed_url.scheme or "relative_or_unknown"] += 1
            if parsed_url.scheme == "http" and parsed_url.hostname:
                non_https_hosts[parsed_url.hostname.lower()] += 1
        if reason in ("missing_source_url", "non_https_source_url") and detail_requests < MAX_DETAILS_PER_STATE:
            detail_requests += 1
            try:
                source = detail_source(raw, get)
            except HTTPError as exc:
                if exc.code in (401, 403, 429):
                    raise
                detail_failures += 1
                source = None
            except (URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError):
                detail_failures += 1
                source = None
            if source:
                raw = dict(raw, source_url=source)
                reason = reject_reason(raw)
        if reason:
            rejected[reason] += 1
            continue
        candidate = record(raw, state, PER_PAGE)
        if candidate is None:
            rejected["record_validation_failed"] += 1
        elif candidate["id"] not in indexed and candidate["id"] not in pending:
            candidate["retrievalScope"] = "first_5_state_keyword_results_source_link_recovery_only"
            candidate["reviewStatus"] = "third_party_index_official_source_review_required"
            pending[candidate["id"]] = candidate
            new_rows += 1
    indexed.update(pending)
    return {
        "status": "bounded_five_hit_source_link_audit_not_exhaustive",
        "searchHitsSampled": len(rows),
        "providerTotalMatches": payload.get("pagination", {}).get("total"),
        "newCandidateRows": new_rows,
        "rejectionCounts": dict(sorted(rejected.items())),
        "nonHttpsSourceSchemes": dict(sorted(non_https_schemes.items())),
        "nonHttpsSourceHosts": dict(sorted(non_https_hosts.items())),
        "billDetailRequests": detail_requests,
        "billDetailFailures": detail_failures,
        "source": url,
    }


def main():
    if date.today() > END:
        print("Deadline passed; no source requests")
        return
    if AUDIT.exists():
        previous = json.loads(AUDIT.read_text(encoding="utf-8"))
        if previous.get("auditVersion") == 2 and previous.get("dateUTC") == date.today().isoformat():
            print("Version-2 bounded audit already completed today; no repeated source requests")
            return
    bills = json.loads(BILLS.read_text(encoding="utf-8"))
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    indexed = {row["id"]: row for row in bills["records"]}
    audit = {
        "schema": "power-atlas.state-bill-filter-audit.v1",
        "auditVersion": 2,
        "dateUTC": date.today().isoformat(),
        "status": "bounded_four_jurisdiction_source_link_recovery",
        "scope": "First five redistricting keyword hits only; not exhaustive state legislation",
        "jurisdictions": {},
        "accessPolicy": "No auth bypass; 401/403/429 stop all requests; preserve prior records.",
    }
    for state in STATES:
        try:
            result = process_state(state, indexed)
            audit["jurisdictions"][state] = result
        except HTTPError as exc:
            audit["jurisdictions"][state] = {
                "status": "access_or_rate_deferred" if exc.code in (401, 403, 429) else "http_failure",
                "httpStatus": exc.code,
                "newCandidateRows": 0,
            }
            if exc.code in (401, 403, 429):
                audit["status"] = "stopped_on_access_or_rate_restriction"
                break
        except (URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            audit["jurisdictions"][state] = {
                "status": "temporary_unavailable",
                "errorType": type(exc).__name__,
                "newCandidateRows": 0,
            }
        time.sleep(0.4)
    bills["records"] = sorted(indexed.values(), key=lambda row: row["id"])
    if len(bills["records"]) > 1200:
        raise RuntimeError("Candidate row cap exceeded")
    rendered = json.dumps(bills, indent=2, ensure_ascii=False) + "\n"
    if len(rendered.encode("utf-8")) > 850000:
        raise RuntimeError("Candidate byte cap exceeded")
    counts = Counter(row["state"] for row in bills["records"])
    for state, meta in checkpoint["jurisdictions"].items():
        count = counts[state]
        meta["persistedCandidateRows"] = count
        if count:
            meta["status"] = "first_page_indexed_not_exhaustive"
        elif (meta.get("totalMatchesReported") or 0) > 0:
            meta["status"] = "first_page_matches_reported_no_candidates_persisted"
        else:
            meta["status"] = "first_page_empty_search_not_no_bills"
    audit["candidateRowsAfter"] = len(bills["records"])
    audit["jurisdictionsWithCandidateRowsAfter"] = sum(counts[s] > 0 for s in checkpoint["jurisdictions"])
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    for path, data in (
        (BILLS, rendered),
        (CHECKPOINT, json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n"),
        (AUDIT, json.dumps(audit, indent=2, ensure_ascii=False) + "\n"),
    ):
        if not path.exists() or path.read_text(encoding="utf-8") != data:
            path.write_text(data, encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
