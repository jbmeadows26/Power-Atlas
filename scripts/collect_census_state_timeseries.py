#!/usr/bin/env python3
"""Collect official Census 2012–2024 state-only finance aggregate series.

Provides real fiscal-year cash/accounting aggregate observations but NO
election dates, policy claims or causal estimates. Aggregates are used directly
to avoid double counting historical nested G/K code families.

The official archive is a publicly indexed ZIP, not a Census API endpoint.
Amounts are published in units of $1,000 (per included field dictionary).
"""
import csv
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

from scripts.probe_census_state_timeseries_zip import URL, download, MAX_ZIP_BYTES

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"data/fiscal/state-timeseries"
OUTPUT=DEST/"aggregate-capital-2012-2024.json"
EXPECTED_SOURCE_SHA256="888dfbb3f8eeebce01b409e4e86178ac04c596c7fc355047beef2433a9b5be48"
DAT_NAME="GOVSSTATEFINTIMESERIES.dat"
FIELDS_NAME="GOVSSTATEFINTIMESERIES_FIELDS.txt"
YEAR_SET=set(range(2012,2025))
METRICS={
    "SF0132":("totalExpenditure","Expenditure - Total Expenditure"),
    "SF0175":("directExpenditure","Expenditure - Total Direct Expenditure"),
    "SF0176":("directGeneralExpenditure","Expenditure - Direct Expenditure - Total General Expenditure"),
    "SF0177":("currentOperations","Expenditure - Direct Expenditure - Total Current Operations"),
    "SF0178":("capitalOutlay","Expenditure - Direct Expenditure - Total Capital Outlay"),
}
REQUIRED_COLUMNS={"#GEO_ID","ST","GEOTYPE","GOVTYPE","YEAR","CATEGORY",
                 "AGG_DESC","AGG_DESC_LABEL","ITEM_CODE","AMOUNT","AMOUNT_F"}


def process_archive(body, enforce_source_hash=True):
    if not isinstance(body,bytes) or not body.startswith(b"PK") or len(body)>MAX_ZIP_BYTES:
        raise ValueError("Untrusted ZIP input")
    digest=hashlib.sha256(body).hexdigest()
    if enforce_source_hash and digest!=EXPECTED_SOURCE_SHA256:
        raise ValueError("Official source ZIP changed; require review before publishing new vintage")
    state_codes={f"{i:02}" for i in list(range(1,9))+list(range(10,52))}
    records={}
    counts=Counter()
    sample_labels={}
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        if DAT_NAME not in z.namelist() or FIELDS_NAME not in z.namelist():
            raise ValueError("Official ZIP missing data/field-dictionary members")
        if sum(i.file_size for i in z.infolist())>100_000_000:
            raise ValueError("ZIP uncompressed size exceeds validated bound")
        fields=z.read(FIELDS_NAME).decode("utf-8-sig")
        if "AMOUNT|Amount ($1,000)|NUMBER|20|0" not in fields:
            raise ValueError("Published amount unit or field schema changed")
        with z.open(DAT_NAME) as source:
            decoded=io.TextIOWrapper(source,encoding="utf-8-sig",errors="strict",newline="")
            rows=csv.DictReader(decoded,delimiter="|")
            if not rows.fieldnames or not REQUIRED_COLUMNS.issubset(set(rows.fieldnames)):
                raise ValueError("Official DAT columns changed")
            for row in rows:
                counts["allSourceRows"]+=1
                if counts["allSourceRows"]>400_000:
                    raise ValueError("Unexpected expansion of modern data source")
                if row["ST"] not in state_codes or row["GEOTYPE"]!="02" or row["GOVTYPE"]!="002":
                    continue
                year_raw=row["YEAR"]
                if not year_raw.isdigit() or int(year_raw) not in YEAR_SET:
                    raise ValueError("Unsupported state-fiscal observation year")
                code=row["AGG_DESC"]
                if code not in METRICS:
                    continue
                key=(row["ST"],int(year_raw))
                if row["CATEGORY"]!="02" or row["ITEM_CODE"]!="AGG":
                    raise ValueError(f"{key} {code}: unexpected category or item-type")
                if row["AGG_DESC_LABEL"]!=METRICS[code][1]:
                    raise ValueError(f"{key} {code}: published aggregate label changed")
                if row["AMOUNT_F"]:
                    raise ValueError(f"{key} {code}: flagged amount requires explicit review")
                s=row["AMOUNT"].strip()
                if not s.isdigit():
                    raise ValueError(f"{key} {code}: missing or negative published aggregate")
                amt=int(s)
                if amt<0:
                    raise ValueError(f"{key} {code}: negative expenditure")
                records.setdefault(key,{})
                if code in records[key]:
                    raise ValueError(f"{key} {code}: duplicate official aggregate")
                records[key][code]=amt
                sample_labels.setdefault(key,row["GEO_LABEL"])
                counts["retainedAggregateRows"]+=1
    expected_keys={(state,year) for state in state_codes for year in YEAR_SET}
    if set(records)!=expected_keys:
        missing=sorted(expected_keys-set(records))
        extra=sorted(set(records)-expected_keys)
        raise ValueError(f"State-year coverage incomplete; missing sample {missing[:5]}; extra {extra[:5]}")
    out=[]
    for key in sorted(records):
        vals=records[key]
        if set(vals)!=set(METRICS):
            raise ValueError(f"{key}: missing required official summary aggregates: {set(METRICS)-set(vals)}")
        total_direct=vals["SF0175"]
        capital=vals["SF0178"]
        current=vals["SF0177"]
        if not (total_direct>0 and 0<=capital<=total_direct and 0<=current<=total_direct):
            raise ValueError(f"{key}: aggregate arithmetic sanity check failed")
        state,year=key
        out.append({
            "id":f"US-{state}-{year}",
            "country":"US","fipsState":state,"state":sample_labels[key],"fiscalYear":year,
            "governmentType":"state_only","sourceAmountUnits":"thousands_of_USD",
            "totalsThousandsUSD":{METRICS[code][0]:vals[code] for code in METRICS},
            "capitalOutlayShareOfDirectExpenditureBasisPoints":round(10_000*capital/total_direct),
            "classificationRegime":"pre_2022" if year<=2021 else "post_2022_reclassified",
            "fiscalClock":"state_specific_fiscal_year_boundaries_not_yet_attached",
            "sourceMissingness":"no_missing_in_selected_aggregate_values",
        })
    return {
        "schema":"power-atlas.census-state-finance-aggregates.v1",
        "publicationStatus":"official_yearly_state_aggregates_descriptive_not_election_horizon_analyses",
        "asOf":"2026-06-17",
        "source":{
            "url":URL,"sha256OriginalBytes":digest,
            "fieldDictionaryMember":FIELDS_NAME,
            "datMember":DAT_NAME,
            "units":"thousands_of_USD",
            "sourcePublisher":"US Census Bureau",
            "sourceScope":"annual_state_government_finances_only",
        },
        "coverage":{
            "startYear":2012,"endYear":2024,"yearCount":13,
            "stateGovernmentsPerYear":50,
            "stateYearObservations":len(out),
            "sourceRowsInspected":counts["allSourceRows"],
            "officialAggregateRowsRetained":counts["retainedAggregateRows"],
            "selectedAggregateCodes":{code:{"key":key,"publishedLabel":label} for code,(key,label) in METRICS.items()},
        },
        "comparabilityWarnings":[
            "Capital outlay is an official aggregated metric, not a sum of separately published F/G/K source-code rows.",
            "Census 2022 methodology changed historic capital-expenditure classifications and other finance accounting; cross-2022 time comparisons require a documented bridge.",
            "Amounts are reported in current nominal USD thousands and have not been adjusted for inflation.",
            "State-only finance comparisons exclude local governmental spending, which is organized differently across states.",
            "Fiscal-year ending dates and governor-election calendars remain unlinked. No causal election-cycle conclusions are authorized.",
        ],
        "descriptiveInterpretation":"Ratio measures recorded official total direct capital outlay divided by total direct expenditure within each state fiscal year, not economic ROI or electoral myopia.",
        "electionClockAttached":False,
        "electoralShortTermismModel":None,
        "causalEstimates":None,
        "records":out,
    }


def build():
    body=download()
    doc=process_archive(body,enforce_source_hash=True)
    DEST.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8")!=serialized:
        OUTPUT.write_text(serialized,encoding="utf-8")
    print(json.dumps({"publishedSourceSHA256":doc["source"]["sha256OriginalBytes"],
                      "coverage":doc["coverage"],
                      "capitalShareBoundsBps":[min(r["capitalOutlayShareOfDirectExpenditureBasisPoints"] for r in doc["records"]),
                                               max(r["capitalOutlayShareOfDirectExpenditureBasisPoints"] for r in doc["records"])],
                      "model":doc["electoralShortTermismModel"],
                      "status":doc["publicationStatus"]},indent=2))


if __name__=="__main__":
    build()
