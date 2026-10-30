"""Collect privacy-minimized official WA campaign-finance aggregate summary.

State of Washington PDC Socrata source (no paid key). Public release ONLY
coarse filer-type/election-year groups; never publish any original person's
name, address, e-mail or detailed contribution list. The PDC source has
noncommercial restrictions on lists of individuals; all commercial licensing
decisions remain gated for legal review.

Amounts are summed over published campaign-finance summary rows, not checked
to original amended filing totals. Do not infer donation transactions.
"""
import hashlib
import json
import math
import re
import urllib.parse
import urllib.request
from decimal import Decimal,InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/finance/wa-pdc/summary-aggregate-2020-2024.json"
BASE="https://data.wa.gov/resource/3h9x-7bvm.json"
PUBLISHER="https://www.pdc.wa.gov/political-disclosure-reporting-data/open-data"
YEARS=(2020,2022,2024)
K_ANON_MIN=5
SELECT=("election_year, filer_type, count(*) as rows,"
        "sum(contributions_amount) as contributions,"
        "sum(expenditures_amount) as expenditures")
WHERE="election_year in('2020','2022','2024')"
PARAMS={"$select":SELECT,"$where":WHERE,"$group":"election_year,filer_type","$order":"election_year,filer_type","$limit":1000}

def request():
    url=BASE+"?"+urllib.parse.urlencode(PARAMS)
    req=urllib.request.Request(url,headers={"Accept":"application/json",
       "User-Agent":"PowerAtlasPublicResearch/1.0 (nonindividual published PDC aggregated records)"})
    with urllib.request.urlopen(req,timeout=50) as response:
        if urllib.parse.urlsplit(response.geturl()).hostname!="data.wa.gov":
            raise ValueError("Unexpected PDC source")
        raw=response.read(700001)
    if len(raw)>700000:raise ValueError("PDC aggregated API response unexpectedly large")
    return raw,url

def amount(x,key):
    if x is None:return None
    try:
        v=Decimal(str(x))
    except (InvalidOperation,ValueError) as e:
        raise ValueError("Invalid published PDC aggregate amount "+key) from e
    if not v.is_finite():raise ValueError("Nonfinite published PDC amount")
    return format(v.quantize(Decimal("0.01")),"f")

def parse(raw,url):
    d=json.loads(raw)
    if not isinstance(d,list) or not d or len(d)>1000:
        raise ValueError("PDC source grouped output empty/unexpected")
    output=[]
    omitted=[]
    seen=set()
    for item in d:
        if not {"election_year","filer_type","rows"}.issubset(item):
            raise ValueError("Grouped PDC response missing required fields")
        year=item["election_year"]
        if year not in {str(y) for y in YEARS}:
            raise ValueError("Unexpected PDC election year "+str(year))
        ftype=item["filer_type"]
        if not isinstance(ftype,str) or not ftype or len(ftype)>150:
            raise ValueError("Unexpected PDC filer class")
        if not str(item["rows"]).isdigit():
            raise ValueError("Noninteger reported group row count")
        n=int(item["rows"])
        key=(year,ftype)
        if key in seen:raise ValueError("Duplicated published election-year/filer category")
        seen.add(key)
        if n<K_ANON_MIN:
            omitted.append({"year":year,"reason":"suppressed_small_filer_group"})
            continue
        output.append({
           "electionYear":int(year),
           "filerType":ftype,
           "publishedSummaryRows":n,
           "sumOfPublishedContributionsUSD":amount(item.get("contributions"),"contributions"),
           "sumOfPublishedExpendituresUSD":amount(item.get("expenditures"),"expenditures"),
           "status":"official_grouped_source_not_original_filing_reconciled",
        })
    if not output:raise ValueError("No reportable PDC aggregates")
    if not all(v["publishedSummaryRows"]>=K_ANON_MIN for v in output):
        raise ValueError("K-anonymity filter failed")
    years={v["electionYear"] for v in output}
    if not set(YEARS).issubset(years):
        raise ValueError("PDC missing expected historical election-year groups")
    return {
        "schema":"power-atlas.wa-pdc-campaign-aggregate.v1",
        "dataStatus":"public_coarse_aggregate_only_not_statewide_itemized_filings_or_licensed_personal_lists",
        "state":"WA",
        "authority":"Washington Public Disclosure Commission via official State Open Data Socrata",
        "sourceURL":url,
        "sourcePublisherURL":PUBLISHER,
        "originalJSONResponseSHA256":hashlib.sha256(raw).hexdigest(),
        "electionYears":list(YEARS),
        "categoryRows":len(output),
        "minFilerRowsPerPublishedGroup":K_ANON_MIN,
        "suppressedSmallGroupsCount":len(omitted),
        "groupBy":"election_year, filer_type",
        "financialInterpretation":"Sum of published PDC finance summary rows, NOT certified donation transactions, not filing-amendment reconciliation",
        "notIncluded":"individual contributors, identities, filer names, addresses, treasurers, personal contact details, loans at transaction level, filing amendments, independent expenditure detail",
        "licensingGate":"PDC imposes noncommercial restrictions on lists of individuals; no personal list is republished. Review license/policy before commercial reuse of any derived fields.",
        "campaignFinanceCompleteForWA":False,
        "all50StatesComplete":False,
        "records":sorted(output,key=lambda r:(r["electionYear"],r["filerType"])),
    }

def main():
    raw,url=request()
    doc=parse(raw,url)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf8")!=content:
        OUT.write_text(content,encoding="utf8")
    print(json.dumps({"state":doc["state"],"years":doc["electionYears"],
                      "groupRecords":doc["categoryRows"],"privacyMinRows":K_ANON_MIN,
                      "complete":doc["campaignFinanceCompleteForWA"],
                      "licensingGate":doc["licensingGate"]},indent=2))

if __name__=="__main__":
    main()
