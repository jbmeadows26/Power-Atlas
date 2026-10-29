#!/usr/bin/env python3
"""Audit persisted Census 2000-2015 historical state-government *code families*.

This intentionally makes no sums of financial amounts, percentages of capital
spending, or election-cycle coefficients. Historical G can include K equipment;
the category rows are not independent, additive observations.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/fiscal/state-legacy"
OUT=DATA/"quality-audit.json"
YEAR_START,YEAR_END=2000,2015
VALID_STATUSES={"numeric_reported","published_missing_marker_dot","published_missing_marker_blank"}
CLASSIFICATION="https://www2.census.gov/govs/class/classfull.pdf"
BREAK_2022="https://www2.census.gov/programs-surveys/state/technical-documentation/complete-technical-documentation/statetechdoc2022.pdf"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def compile_audit():
    idx=read(DATA/"index.json")
    years=idx.get("years",[])
    expected=list(range(YEAR_START,YEAR_END+1))
    if years!=expected or len(idx.get("sources",[]))!=len(expected):
        raise ValueError("Archived-year inventory incomplete or unordered; no inferred coverage")
    if idx.get("spendingShares") is not None or idx.get("electionCycleEstimates") is not None:
        raise ValueError("Historical raw-code inventory unexpectedly reports inferential estimates")
    source_by_year={x["year"]:x for x in idx["sources"]}
    if len(source_by_year)!=len(expected):
        raise ValueError("Duplicated vintage source in index")
    annual=[]
    item_sets={}
    total_rows=0
    missing_total=0
    for year in expected:
        source=source_by_year[year]
        expected_path=f"data/fiscal/state-legacy/fy{year}.json"
        if source.get("path")!=expected_path:
            raise ValueError(f"{year}: source path mismatch; refusing traversal")
        year_doc=read(ROOT/expected_path)
        if year_doc.get("collectionYear")!=year:
            raise ValueError(f"{year}: source vintage mismatch")
        if year_doc.get("publicationStatus")!="official_raw_code_family_staged_not_harmonized":
            raise ValueError(f"{year}: fiscal observations are not marked as raw/unharmonized")
        if year_doc.get("source",{}).get("sha256OriginalBytes")!=source.get("sha256OriginalBytes"):
            raise ValueError(f"{year}: original source SHA-256 mismatch")
        rows=year_doc.get("records")
        if not isinstance(rows,list):
            raise ValueError(f"{year}: expected source-level records")
        if len(rows)!=source.get("capitalFamilyRowsRetained"):
            raise ValueError(f"{year}: row count disagrees with source index")
        families=Counter()
        missing=Counter()
        state_rows=Counter()
        codes=set()
        keys=set()
        for row in rows:
            gov=row.get("stateGovernmentCode","")
            code=row.get("itemCode","")
            status=row.get("amountStatus")
            amount=row.get("amountAsPublished")
            if len(gov)!=14 or gov[2:]!="0"*12 or gov[:2]=="09" or not gov.isdigit():
                raise ValueError(f"{year}: non-state government record")
            if len(code)!=3 or code[0] not in "FGK":
                raise ValueError(f"{year}: outside capital character codes")
            if status not in VALID_STATUSES:
                raise ValueError(f"{year}: unrecognized amount missingness status")
            if status=="published_missing_marker_blank" and str(amount).strip()!="":
                raise ValueError(f"{year}: malformed blank marker")
            if status=="published_missing_marker_dot" and str(amount).strip()!=".":
                raise ValueError(f"{year}: malformed dot marker")
            if status=="numeric_reported" and not str(amount).strip().lstrip("-").isdigit():
                raise ValueError(f"{year}: malformed numeric published amount")
            key=(gov,code,row.get("surveyYearTwoDigits"),row.get("dataYearTwoDigits"),row.get("originCode"))
            if key in keys:
                raise ValueError(f"{year}: duplicate original source record")
            keys.add(key)
            families[code[0]]+=1
            state_rows[gov[:2]]+=1
            codes.add(code)
            if status!="numeric_reported":
                missing[status]+=1
        if len(state_rows)!=50 or any(v<10 for v in state_rows.values()):
            raise ValueError(f"{year}: incomplete state-code coverage")
        if dict(families)!={k:year_doc["coverage"]["capitalFamilyRowCounts"][k] for k in families}:
            raise ValueError(f"{year}: category-family count differs from collector")
        if sum(missing.values())!=year_doc["coverage"].get("missingMarkerRows"):
            raise ValueError(f"{year}: missing values differ from ingest summary")
        item_sets[year]=codes
        total_rows+=len(rows)
        missing_total+=sum(missing.values())
        annual.append({
            "year":year,
            "sourceSHA256":source["sha256OriginalBytes"],
            "sourceURL":source["url"],
            "sourceRecordWidthChars":year_doc["source"]["recordWidthChars"],
            "originalCodeRows":len(rows),
            "distinctItemCodes":len(codes),
            "capitalFamilyRows":{k:families.get(k,0) for k in "FGK"},
            "stateGovernmentsWithRows":len(state_rows),
            "missingValuesByMarker":{k:missing.get(k,0) for k in ("published_missing_marker_dot","published_missing_marker_blank")},
            "minimumRowsPerState":min(state_rows.values()),
            "maximumRowsPerState":max(state_rows.values()),
        })
    transitions=[]
    for before,after in zip(expected,expected[1:]):
        left,right=item_sets[before],item_sets[after]
        prev=annual[before-YEAR_START]["originalCodeRows"]
        nxt=annual[after-YEAR_START]["originalCodeRows"]
        transitions.append({
            "fromYear":before,"toYear":after,
            "newItemCodesCount":len(right-left),
            "disappearingItemCodesCount":len(left-right),
            "recordCountDelta":nxt-prev,
            "largeChangeInRowCount":abs(nxt-prev)>0.15*prev,
            "interpretation":"coding_universe_or_data_scope_change_requires_review_not_expenditure_change"
        })
    return {
        "schema":"power-atlas.census-legacy-code-audit.v1",
        "publicationStatus":"source_code_coverage_audited_not_spending_model_ready",
        "sourceYears":expected,
        "totalRawCapitalFamilyRecords":total_rows,
        "totalPublishedMissingValueMarkers":missing_total,
        "distinctStateYearKeys":16*50,
        "annualCoverage":annual,
        "adjacentYearCodeUncertainty":transitions,
        "nonadditiveCharacterCodes":{
            "F":"Construction",
            "G":"Capital outlay other than construction; in published data may already include K equipment",
            "K":"Equipment subcategory; not independently additive to G without evidence of alternative layout",
            "forbidNaiveFPlusGPlusK":True,
            "reference":CLASSIFICATION,
        },
        "knownBreaks":[
            {"year":2013,"reason":"Observed source-record count discontinuity between 2012 and 2013; scope/coding investigation required, not an observed spending change","status":"requires_review"},
            {"year":2022,"reason":"Census formally consolidated historic F/G/K categories into a new F capital code, and changed some other accounting treatments","status":"verified_documented_break","source":BREAK_2022},
        ],
        "excludedCoverage":{"2016_to_2025":"not_imported_by_this_archival_collection"},
        "spendingShares":None,
        "electionProximityCoefficients":None,
        "causalFindings":None,
        "warnings":[
            "Source-code rows are neither unique infrastructure projects nor additive spending categories.",
            "G and K are potentially nested in Census archival statistics; do not sum them as if disjoint.",
            "FY 2000–2015 are state-government only, not state-plus-local total public spending.",
            "Fiscal year end varies by state and must be aligned to election months before inference.",
            "No monetary amounts are converted, deflated or harmonized in this code-quality audit."
        ],
    }


def main():
    audit=compile_audit()
    rendered=json.dumps(audit,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if "--check" in sys.argv[1:]:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=rendered:
            raise SystemExit("Source-code quality audit is missing or stale; regenerate it")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=rendered:
            OUT.write_text(rendered,encoding="utf-8")
    print(json.dumps({
        "years":len(audit["sourceYears"]),"originalCodeRows":audit["totalRawCapitalFamilyRecords"],
        "missingMarkers":audit["totalPublishedMissingValueMarkers"],
        "suspectedLargeRowCountDiscontinuities":[t for t in audit["adjacentYearCodeUncertainty"] if t["largeChangeInRowCount"]],
        "publicationStatus":audit["publicationStatus"]
    },indent=2))


if __name__=="__main__":
    main()
