"""Import official NYC CFB candidate-level 2025 financial analysis (NOT individual contributions).

Uses NYC Open Data source m3tj-a2pb. The dataset reports one financial
analysis per candidate/campaign and is not an organization-to-organization
transaction ledger. No donor names, contact info, or addresses are requested.
No records are linked to federal donors or inferred dark money.
"""
from __future__ import annotations
import hashlib
import json
import re
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/finance/nyc-cfb/campaign-financial-analysis-2025.json"
DATASET="m3tj-a2pb"
BASE="https://data.cityofnewyork.us/resource/"+DATASET+".json"
PUBLISHER="https://data.cityofnewyork.us/City-Government/Campaign-Financial-Analysis/m3tj-a2pb"
YEAR="2025"
COLUMNS="el_cycle,from_stmt,to_stmt,office,cand_name,cand_id,boro_dist,termnd,incumbent,cntrs_no,cntns_no,net_cntns,match_amt,i_no,i_cntns_no"
SELECT={"$select":COLUMNS,"$where":"el_cycle='2025'",
        "$limit":"4000","$order":"cand_id,boro_dist"}
OFFICES={"1":"Mayor","2":"Public Advocate","3":"Comptroller","4":"Borough President",
         "5":"City Council","6":"Undeclared"}

def decimal_amount(val):
    try:
        amt=Decimal(str(val))
        if not amt.is_finite() or abs(amt)>Decimal("1000000000"):
            raise ValueError("Impossible CFB financial amount")
        return float(amt.quantize(Decimal(".01")))
    except (InvalidOperation,TypeError):
        raise ValueError("CFB financial amount missing or invalid")

def parse(rows):
    if not isinstance(rows,list) or not 15<=len(rows)<=4000:
        raise ValueError("NYC financial analysis source unexpectedly empty or oversized")
    canonical={}
    multiplicities={}
    for raw in rows:
        if raw.get("el_cycle")!=YEAR:
            raise ValueError("Source query escaped election-year filter")
        cid=str(raw.get("cand_id") or "").strip()
        name=str(raw.get("cand_name") or "").strip()
        office=OFFICES.get(str(raw.get("office") or "").strip(),"Other / not classified")
        if not re.fullmatch(r"[A-Za-z0-9-]{2,35}",cid) or not name or len(name)>145:
            raise ValueError("NYC candidate/campaign identity invalid")
        boro=str(raw.get("boro_dist") or "").strip()
        key=(cid,boro)
        total=decimal_amount(raw.get("net_cntns"))
        if total<0:
            raise ValueError("Negative net receipts require manual investigation before publication")
        match=decimal_amount(raw.get("match_amt") or "0")
        if match<0:
            raise ValueError("Negative matching claim unsupported")
        num=raw.get("cntns_no")
        if num is None or not str(num).isdigit() or int(num)>100_000_000:
            raise ValueError("Invalid published NYC contribution count")
        to_stmt=str(raw.get("to_stmt") or "").strip()
        if to_stmt and not to_stmt.isdigit():
            raise ValueError("Invalid NYC statement-through number")
        record={
            "id":"nyc:cfb:"+cid+(":"+boro if boro else ""),
            "electionYear":2025,
            "candidateId":cid,"candidateName":name,
            "office":office,
            "boroughOrDistrict":boro,
            "statementFrom":str(raw.get("from_stmt") or ""),
            "statementThrough":to_stmt,
            "reportedNetContributionsUSD":total,
            "reportedContributionsCount":int(num),
            "contributionsClaimedForMatchingUSD":match,
            "source":PUBLISHER,
            "evidenceType":"NYC_CFB_candidate_campaign_financial_analysis",
            "reviewStatus":"official_city_dataset_not_individually_audited",
        }
        multiplicities[key]=multiplicities.get(key,0)+1
        # Latest through-statement wins; never add multiple versions of one
        # candidate/district record. On ties choose a deterministic
        # canonical row (highest reported receipt, then sorted name).
        rank=(int(to_stmt or 0),total,name)
        previous=canonical.get(key)
        if previous is None or rank > previous[0]:
            canonical[key]=(rank,record)
    out=[]
    for key,(_,record) in canonical.items():
        record["sourceRowsForCampaignDistrict"]=multiplicities[key]
        record["selectionStatus"]=("one_source_row" if multiplicities[key]==1 else
            "selected_highest_statement_through_from_multiple_source_rows")
        out.append(record)
    return sorted(out,key=lambda r:(-r["reportedNetContributionsUSD"],r["id"]))

def collect():
    params=urllib.parse.urlencode(SELECT)
    url=BASE+"?"+params
    req=urllib.request.Request(url,headers={"Accept":"application/json",
           "User-Agent":"PowerAtlasPublicInterestResearch/1.3 (public candidate aggregates only)"})
    with urllib.request.urlopen(req,timeout=50) as resp:
        endpoint=urllib.parse.urlsplit(resp.geturl())
        if endpoint.hostname!="data.cityofnewyork.us" or endpoint.scheme!="https":
            raise ValueError("Unexpected NYC public data endpoint")
        body=resp.read(3_500_001)
    if len(body)>3_500_000:raise ValueError("NYC aggregated response over bounded limit")
    source=json.loads(body)
    rows=parse(source)
    obj={"schema":"power-atlas.nyc-cfb.campaign-financial-analysis.v1",
         "publisher":"New York City Campaign Finance Board, NYC Open Data",
         "datasetId":DATASET,"sourceURL":PUBLISHER,
         "queryURL":url,"sourceResponseSHA256":hashlib.sha256(body).hexdigest(),
         "electionYear":2025,"coverageStatus":"official_candidate_campaign_aggregate_partial",
         "grain":"candidate_id AND borough_or_district (unique reported analysis row)",
         "individualDonorsIncluded":False,"donorToRecipientEdgesCreated":0,
         "amountMeaning":"NET CONTRIBUTIONS to campaign per source analysis row, NOT committee transfers, total expenditures, or identified original funders.",
         "matchingMeaning":"Contributions CLAIMED for matching, not total public matching payments received.",
         "completenessLimitations":[
             "CFB city-office candidate campaign analysis, not independent spender or ballot-measure contribution records.",
             "Dataset as updated December 2025; later amendments, 2026 races and future campaign filings may not be reflected.",
             "Source rows may be district- or borough-specific; do not sum across incompatible grains without reconciliation.",
             "No source contributor names or identities were downloaded; not a dark-money donor database."],
         "recordCount":len(rows),"sourceRowsRead":len(source),
         "sourceRowsWithRepeatedCampaignDistrict":sum(r["sourceRowsForCampaignDistrict"]-1 for r in rows),
         "sourceVersionRule":"For repeated candidate ID and borough/district, retain latest to_stmt; never sum source versions.",
         "records":rows}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    return obj
if __name__=="__main__":
    result=collect()
    print(json.dumps({"recordCount":result["recordCount"],
                      "electionYear":result["electionYear"],
                      "sourceResponseSHA256":result["sourceResponseSHA256"]},indent=2))
