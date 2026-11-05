"""Privacy-safe Washington PDC 2026 filer-category campaign finance snapshot.

Queries the state Socrata server *after* grouping by filing class. Never
downloads or republishes individual contributor names, organization names,
streets, email, or exact filing-level transactions. Adds contextual state
coverage, not an inter-committee money-flow graph.
"""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/finance/wa-pdc/summary-aggregate-2026.json"
BASE="https://data.wa.gov/resource/3h9x-7bvm.json"
DOCS="https://www.pdc.wa.gov/political-disclosure-reporting-data/open-data"
QUERY={
    "$select":"election_year, filer_type, count(*) as rows, "
              "sum(contributions_amount) as contributions, "
              "sum(expenditures_amount) as expenditures",
    "$where":"election_year = '2026'",
    "$group":"election_year, filer_type",
    "$order":"election_year, filer_type",
    "$limit":"250",
}
MIN_GROUP=5

def parse(rows):
    if not isinstance(rows,list) or not rows or len(rows)>250:
        raise ValueError("WA PDC 2026 grouped source unavailable")
    result=[];seen=set()
    for item in rows:
        if not isinstance(item,dict):
            raise ValueError("WA PDC grouped row invalid")
        if str(item.get("election_year"))!="2026":
            raise ValueError("WA grouped query returned a different election year")
        kind=item.get("filer_type")
        if not isinstance(kind,str) or not kind or len(kind)>150:
            raise ValueError("WA filer class invalid")
        if kind in seen:raise ValueError("Duplicate WA filer category")
        seen.add(kind)
        n=int(item.get("rows") or 0)
        if n<MIN_GROUP:continue
        def usd(field):
            try:
                v=Decimal(str(item.get(field)))
                if not v.is_finite() or v<0 or v>Decimal("1000000000000"):
                    raise ValueError("Invalid WA PDC total")
                return format(v.quantize(Decimal("0.01")),"f")
            except (InvalidOperation, TypeError) as e:
                raise ValueError("Missing WA PDC aggregate") from e
        result.append({"electionYear":2026,"filerType":kind,
                       "publishedSummaryRows":n,
                       "sumOfPublishedContributionsUSD":usd("contributions"),
                       "sumOfPublishedExpendituresUSD":usd("expenditures")})
    if not result:raise ValueError("WA PDC 2026 grouped response below privacy minimum")
    return sorted(result,key=lambda r:r["filerType"])

def collect():
    url=BASE+"?"+urllib.parse.urlencode(QUERY)
    req=urllib.request.Request(url,headers={"Accept":"application/json",
       "User-Agent":"PowerAtlasPublicInterestResearch/1.2 (aggregated nonpersonal PDC data)"})
    with urllib.request.urlopen(req,timeout=40) as resp:
        host=urllib.parse.urlsplit(resp.geturl()).hostname
        if host!="data.wa.gov":raise ValueError("Unexpected WA API endpoint")
        blob=resp.read(350001)
    if len(blob)>350000:raise ValueError("WA grouped response too large")
    records=parse(json.loads(blob))
    obj={"schema":"power-atlas.wa-pdc-campaign-aggregate.2026.v1",
         "sourceURL":url,"sourcePublisherURL":DOCS,
         "coverageStatus":"2026_PDC_grouped_summary_not_individual_transactions",
         "state":"WA","electionYear":2026,"groupedCategoryCount":len(records),
         "minFilerRowsPerPublishedGroup":MIN_GROUP,
         "all50StatesComplete":False,
         "individualRecordsPublished":False,
         "hasStateOrLocalMoneyTransferEdges":False,
         "licenseNote":"PDC noncommercial restrictions apply to lists of individuals; no lists or individual-level details were fetched or published. Review source terms before commercial use.",
         "financialInterpretation":"Summed PDC published financial SUMMARY rows by election year and filer class, not individually reconciled transactions or an election cost total.",
         "records":records}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return obj
if __name__=="__main__":
    print(json.dumps({"categories":collect()["groupedCategoryCount"],"state":"WA","year":2026}))
