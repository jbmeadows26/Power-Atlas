"""Source-only CoreCivic prime contract actions, matching the GEO/PacMar method.

Output is additive: it never rewrites the existing GEO/PacMar source, never
conflates corporate-parent and affiliate UEIs, and publishes only after the
entire bounded fiscal-year page walk is validated.
"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from scripts.collect_business_federal_awards import (
    ROOT, EARLIEST_FY, ENDPOINT, DOCS, collect_year, api_post
)

OUT = ROOT / "data/business-influence/corecivic-federal-contracts-v1.json"
CORECIVIC = {
    "id": "corecivic",
    "name": "CoreCivic, Inc.",
    "uei": "HJGMJN1JKL46",
    "identitySource": "https://www.usaspending.gov/recipient/b7ab6cd4-f511-cfe7-c92f-b20d45921e9c-P/all",
    "identityMeaning": "Exact registered parent-recipient UEI, not verified corporate family/affiliate aggregation",
    "politicalEvidenceSource": "https://ir.corecivic.com/static-files/a9909e7f-91e2-4171-ad85-9fd73f933920",
    "fecCommitteeId": "C00366468",
}

def collect(today=None, fetcher=api_post):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    last_fy = today.year + int(today.month >= 10)
    years = [collect_year(CORECIVIC, y, today, fetcher) for y in range(EARLIEST_FY, last_fy + 1)]
    return {
        "schema": "power-atlas.corecivic-federal-contracts.v1",
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": ENDPOINT,
        "documentation": DOCS,
        "matching": "exact_legal_UEI_only_historical_federal_prime_contract_actions",
        "yearDefinition": "Federal fiscal year October 1–September 30 by contract action date",
        "limitations": [
            "Parent UEI not a consolidated corporate-group or all affiliates total",
            "Net obligations include negative contract modifications, not outlays, corporate revenue or profit",
            "Reporting may be delayed or later amended",
            "No FEC political donation or lobbying expenditure linked to an individual contract decision",
            "No comparable control-group or business benefit causal inference"
        ],
        "entity": {**CORECIVIC, "years": years}
    }

def publish(doc):
    if doc.get("schema") != "power-atlas.corecivic-federal-contracts.v1":
        raise ValueError("Unrecognized CoreCivic data")
    if doc.get("entity", {}).get("uei") != CORECIVIC["uei"]:
        raise ValueError("Wrong government-recipient UEI")
    if not doc["entity"].get("years"):
        raise ValueError("No annual observations, refusing source overwrite")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    tmp.replace(OUT)

if __name__ == "__main__":
    d = collect()
    publish(d)
    print(json.dumps({"uei": CORECIVIC["uei"],
                      "years": [(x["fiscalYear"], x["netObligationsUsd"], x["transactionCount"])
                                for x in d["entity"]["years"]]}))
