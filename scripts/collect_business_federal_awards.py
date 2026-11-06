"""Bounded, fail-closed Treasury USAspending transaction collector for Power Atlas.

Uses published legal-entity UEIs; it never joins people to companies by name,
never presumes subsidiaries share a UEI, and never infers a donation/award exchange.
No API key, paid provider or third-party scraping is required.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/business-influence/federal-contract-transactions-v1.json"
ENDPOINT = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"
DOCS = "https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/search/spending_by_transaction.md"
EARLIEST_FY = 2018
PAGE_SIZE = 100
MAX_PAGES_PER_YEAR = 40  # cap 4000 records per UEI-year; fail rather than silently truncate
FIELDS = [
    "Action Date", "Award ID", "Mod", "Recipient Name", "Recipient UEI",
    "Transaction Amount", "Awarding Agency", "Awarding Sub Agency",
    "Award Type", "generated_internal_id", "internal_id",
]
ENTITIES = [
    {
        "id": "geo",
        "name": "The GEO Group, Inc.",
        "uei": "JMLKZZ1NL2Z6",
        "identitySource": "https://www.usaspending.gov/recipient/9b308edb-a62c-659b-704b-ef4e5cf3f795-C/latest",
        "identityMeaning": "Verified direct recipient UEI, NOT the full parent-and-subsidiaries corporate group",
        "politicalEvidenceSource": "https://www.geogroup.com/our-commitments/responsible-governance/political-engagement/",
        "fecCommitteeId": "C00382150",
    },
    {
        "id": "pacmar",
        "name": "PacMar Technologies LLC (Navatek)",
        "uei": "L1WZRB6JKWJ4",
        "identitySource": "https://www.sbir.gov/portfolio/245768",
        "identityMeaning": "SBIR government-recognized recipient UEI; no other affiliate UEIs assumed",
        "politicalEvidenceSource": "https://www.fec.gov/data/legal/matter-under-review/7690/",
        "fecCommitteeId": None,
    },
]


def fiscal_window(year: int, today: dt.date):
    start = dt.date(year - 1, 10, 1)
    end = min(dt.date(year, 9, 30), today)
    return start, end


def money_cents(raw):
    if raw is None or isinstance(raw, bool):
        raise ValueError("Missing/invalid federal transaction amount")
    try:
        d = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid federal transaction amount") from exc
    if not d.is_finite() or abs(d) > Decimal("100000000000"):
        raise ValueError("Federal transaction amount outside safe range")
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def as_money(cents: int):
    return round(cents / 100, 2)


def build_request(uei: str, start: dt.date, end: dt.date, page: int):
    if not re.fullmatch(r"[A-Z0-9]{12}", uei):
        raise ValueError("Invalid UEI")
    if not 1 <= page <= MAX_PAGES_PER_YEAR:
        raise ValueError("Invalid page")
    return {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],
            "recipient_search_text": [uei],
            "time_period": [{"start_date": start.isoformat(), "end_date": end.isoformat()}],
        },
        "fields": FIELDS,
        "page": page,
        "limit": PAGE_SIZE,
        "sort": "Transaction Amount",
        "order": "desc",
    }


def api_post(payload):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "PowerAtlasPublicResearch/1.0 (open data, no credentials)"},
    )
    # A failed or malformed request halts without replacing existing good data.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                if response.status != 200:
                    raise RuntimeError(f"USAspending returned HTTP {response.status}")
                raw = response.read(3_000_001)
                if len(raw) > 3_000_000:
                    raise ValueError("Oversized USAspending response")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("USAspending retry budget exhausted")


def normalize_row(raw, expected_uei: str, start: dt.date, end: dt.date):
    if not isinstance(raw, dict):
        raise ValueError("Unexpected transaction row")
    recipient_uei = str(raw.get("Recipient UEI") or "").upper().strip()
    if not recipient_uei:
        # No guessing: the source must return the legally identifying UEI.
        raise ValueError("USAspending result lacks UEI; cannot verify company linkage")
    if recipient_uei != expected_uei:
        return None  # fuzzy recipient_search_text can return other legal entities
    try:
        action_date = dt.date.fromisoformat(str(raw["Action Date"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("Missing or invalid contract transaction action date") from exc
    if not start <= action_date <= end:
        raise ValueError("USAspending transaction escaped requested fiscal-year window")
    aw = str(raw.get("Award ID") or "").strip()
    gid = str(raw.get("generated_internal_id") or "").strip()
    mod = str(raw.get("Mod") or "").strip()
    if not aw or not gid or len(aw) > 120 or len(gid) > 220 or len(mod) > 40:
        raise ValueError("Missing or oversized award identification")
    cents = money_cents(raw.get("Transaction Amount"))
    name = str(raw.get("Recipient Name") or "").strip()
    agency = str(raw.get("Awarding Agency") or "").strip()
    if not name or not agency:
        raise ValueError("Missing recipient/agency source fields")
    if any(len(x) > 220 for x in [name, agency]):
        raise ValueError("Unexpectedly long source entity name")
    if not re.fullmatch("[A-Za-z0-9_-]+", gid):
        raise ValueError("Invalid natural award ID")
    return {
        "awardId": aw,
        "awardNaturalId": gid,
        "modification": mod,
        "actionDate": action_date.isoformat(),
        "amountUsd": as_money(cents),
        "_cents": cents,
        "recipientUEI": recipient_uei,
        "recipientName": name,
        "awardingAgency": agency,
        "awardingSubAgency": str(raw.get("Awarding Sub Agency") or "")[:180],
        "awardType": str(raw.get("Award Type") or "")[:120],
        "source": "https://www.usaspending.gov/award/" + gid,
        "evidenceType": "Treasury_reported_prime_contract_transaction",
        "reviewStatus": "official_api_not_individually_adjudicated",
    }


def collect_year(entity: dict, year: int, today: dt.date, fetcher=api_post):
    start, end = fiscal_window(year, today)
    rows = []
    seen = set()
    pages = 0
    excluded = 0
    while True:
        if pages >= MAX_PAGES_PER_YEAR:
            raise RuntimeError("Full year exceeds configured page cap; refusing partial financial total")
        request = build_request(entity["uei"], start, end, pages + 1)
        response = fetcher(request)
        if not isinstance(response, dict) or not isinstance(response.get("results"), list):
            raise ValueError("Malformed USAspending page")
        meta = response.get("page_metadata")
        if not isinstance(meta, dict) or not isinstance(meta.get("hasNext"), bool):
            raise ValueError("Missing USAspending pagination metadata")
        if response.get("limit") not in (None, PAGE_SIZE):
            raise ValueError("USAspending returned unexpected page size")
        items = response["results"]
        if len(items) > PAGE_SIZE:
            raise ValueError("USAspending page bigger than requested")
        if meta["hasNext"] and not items:
            raise ValueError("USAspending reported additional records after empty page")
        for raw in items:
            row = normalize_row(raw, entity["uei"], start, end)
            if row is None:
                excluded += 1
                continue
            key = (row["awardNaturalId"], row["modification"],
                   row["actionDate"], row["_cents"])
            if key in seen:
                raise ValueError("Duplicate indistinguishable transaction keys; totals cannot be audited")
            seen.add(key)
            rows.append(row)
        pages += 1
        if not meta["hasNext"]:
            break
        # Request sequentially to limit free public API pressure.
        time.sleep(0.1)

    net = sum(x["_cents"] for x in rows)
    positives = sum(x["_cents"] for x in rows if x["_cents"] > 0)
    negatives = sum(x["_cents"] for x in rows if x["_cents"] < 0)
    awards = defaultdict(lambda: {"amount": 0, "count": 0, "date": "", "agency": "", "awardId": "", "link": ""})
    agencies = defaultdict(int)
    for row in rows:
        a = awards[row["awardNaturalId"]]
        a["amount"] += row["_cents"]
        a["count"] += 1
        a["awardId"] = row["awardId"]
        a["link"] = row["source"]
        if row["actionDate"] >= a["date"]:
            a["date"] = row["actionDate"]
            a["agency"] = row["awardingAgency"]
        agencies[row["awardingAgency"]] += row["_cents"]
    top_awards = sorted(awards.items(), key=lambda it: (-abs(it[1]["amount"]), it[0]))[:12]
    record = {
        "fiscalYear": year,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "partialFiscalYear": end < dt.date(year, 9, 30),
        "recordCoverage": "complete_uei_search_page_walk_not_a_contract_universe_audit",
        "netObligationsUsd": as_money(net),
        "grossPositiveObligationsUsd": as_money(positives),
        "deobligationsUsd": as_money(negatives),
        "transactionCount": len(rows),
        "distinctPrimeAwards": len(awards),
        "sourcePagesRead": pages,
        "otherRecipientUEIRowsExcluded": excluded,
        "topAwardsByAbsoluteNetChange": [
            {
                "awardId": a["awardId"], "awardNaturalId": gid, "netObligationsUsd": as_money(a["amount"]),
                "reportedActions": a["count"], "lastActionDate": a["date"],
                "awardingAgency": a["agency"], "source": a["link"],
            } for gid, a in top_awards
        ],
        "agenciesByNetObligationsUsd": [
            {"agency": name, "amountUsd": as_money(total)}
            for name, total in sorted(agencies.items(), key=lambda x: (-abs(x[1]), x[0]))[:8]
        ],
        "sampleActionsByMagnitude": [
            {k: v for k, v in row.items() if k != "_cents"}
            for row in sorted(rows, key=lambda x: (-abs(x["_cents"]), x["awardNaturalId"], x["actionDate"]))[:8]
        ],
    }
    # Aggregation invariants, checked on raw integer cents.
    if net != positives + negatives:
        raise AssertionError("Net obligation arithmetic mismatch")
    if net != sum(x["amount"] for x in awards.values()):
        raise AssertionError("Award rollup mismatch")
    if net != sum(agencies.values()):
        raise AssertionError("Agency rollup mismatch")
    return record


def collect(today=None, fetcher=api_post):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    last_fy = today.year + int(today.month >= 10)
    entities = []
    for entity in ENTITIES:
        annual = [collect_year(entity, y, today, fetcher) for y in range(EARLIEST_FY, last_fy + 1)]
        entities.append({
            **entity,
            "years": annual,
            "scope": "exact_UEI_prime_contract_actions_only_excludes_sibling_subsidiary_UEIs",
            "coverageNote": "No donation-to-agency decision linkage; year totals are net action obligations, not paid cash, awarded contract ceilings, sales or profit.",
        })
    return {
        "schema": "power-atlas.business-federal-contract-transactions.v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": ENDPOINT,
        "documentation": DOCS,
        "yearDefinition": "U.S. federal fiscal year October 1 through September 30, by contract action date",
        "moneyDefinition": "Sum of distinct public prime-contract action obligations for an exact UEI, including negative deobligations. Not company group revenue, award face value, outlays, or causal donation ROI.",
        "dataFreshness": "FY2026 defense contract reporting can be delayed; FY2027 is in progress and partial; historical actions can be modified.",
        "entityMatching": "Verified UEI equality only. No fuzzy or name-only source match is accepted.",
        "causalStatus": "no_validated_donation_to_award_decision_path_or_matched_counterfactual",
        "entities": entities,
    }


def publish(doc):
    if not isinstance(doc, dict) or len(doc.get("entities", [])) != len(ENTITIES):
        raise ValueError("Refusing incomplete entity collection")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(OUT)


if __name__ == "__main__":
    result = collect()
    publish(result)
    print(json.dumps({"dataset": str(OUT.relative_to(ROOT)),
                      "entities": [(x["id"], len(x["years"]), sum(y["transactionCount"] for y in x["years"]))
                                   for x in result["entities"]]}))
