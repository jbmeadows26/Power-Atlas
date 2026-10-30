#!/usr/bin/env python3
"""Source-linked state economic controls, clearly NOT causal treatment validation.

Uses public (no-key) FRED CSV mirrors for BEA annual real GDP / BLS monthly
unemployment and U.S. Census official time-series ZIP revenue aggregates.
50 states x FY 2012-2024 required. BEA/BLS calendar year y-2 for
outcome FY y; transfers are CONTEMPORANEOUS FY y, potentially a mediator.
Therefore controlsPreTreatmentVerified is False and no causal model may
label this joined file exogenous.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter,defaultdict
from pathlib import Path

from scripts.probe_census_state_timeseries_zip import download,URL as CENSUS_URL

ROOT=Path(__file__).resolve().parents[1]
FIN=ROOT/"data/fiscal/state-timeseries"
OUT=FIN/"economic-controls-2012-2024.json"
FISCAL=FIN/"aggregate-capital-2012-2024.json"
CENSUS_SHA="888dfbb3f8eeebce01b409e4e86178ac04c596c7fc355047beef2433a9b5be48"
STATES={
"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT","10":"DE",
"12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN","19":"IA","20":"KS",
"21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI","27":"MN","28":"MS",
"29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ","35":"NM","36":"NY",
"37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA","44":"RI","45":"SC",
"46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA","54":"WV",
"55":"WI","56":"WY"
}
REVENUE_CODES={
  "SF0002":"Revenue - Total General Revenue",
  "SF0004":"Revenue - General Revenue - Intergovernmental - Total From Federal Government",
}

def fetch_fred_batch(series):
    ids=",".join(series)
    url="https://fred.stlouisfed.org/graph/fredgraph.csv?"+urllib.parse.urlencode({"id":ids})
    request=urllib.request.Request(url,headers={
      "Accept":"text/csv","User-Agent":"PowerAtlasResearch/1.0 (source-cited reproducible state economic indicators)"})
    err=None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request,timeout=35) as response:
                if response.geturl()!=url:
                    raise ValueError("Unexpected FRED source redirect")
                data=response.read(2_000_001)
            if len(data)>2_000_000:
                raise ValueError("FRED batch source oversized")
            rows=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
            if not rows or set(rows[0])!={"observation_date",*series}:
                raise ValueError("FRED response schema differs from requested official BEA/BLS series")
            return rows,{"url":url,"sha256SourceBytes":hashlib.sha256(data).hexdigest(),"rows":len(rows),"seriesIds":series}
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            err=e
            if attempt<3:
                time.sleep(1+2*attempt)
    raise ValueError("FRED source download failed after retries: "+str(err))

def load_fred():
    # 5+5 moderate source requests to reduce rate and avoid undocumented API keys
    series_by_type={
        "realGDP":{f"{abbr}RGSP":fips for fips,abbr in STATES.items()},
        "unemployment":{f"{abbr}UR":fips for fips,abbr in STATES.items()},
    }
    result={}
    sources=[]
    for kind,mapping in series_by_type.items():
        merged={}
        ids=sorted(mapping)
        for i in range(0,len(ids),10):
            group=ids[i:i+10]
            rows,source=fetch_fred_batch(group)
            sources.append({**source,"kind":kind})
            for row in rows:
                date=row["observation_date"]
                if not date or len(date)!=10:continue
                for series in group:
                    v=row[series].strip()
                    if v in ("","."):continue
                    try: fv=float(v)
                    except ValueError as e:raise ValueError(f"Non-numeric source value {kind}/{series}/{date}") from e
                    if not math.isfinite(fv):raise ValueError("Nonfinite FRED observation")
                    key=(mapping[series],date)
                    if key in merged:raise ValueError(f"Duplicate FRED source {key}")
                    merged[key]=fv
        result[kind]=merged
    return result,sources

def load_census_transfers():
    raw=download()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=CENSUS_SHA:raise ValueError("Pinned official Census source SHA changed; source audit required")
    found={}
    years=set(range(2012,2025))
    with zipfile.ZipFile(io.BytesIO(raw)) as z, z.open("GOVSSTATEFINTIMESERIES.dat") as src:
        reader=csv.DictReader(io.TextIOWrapper(src,encoding="utf-8-sig"),delimiter="|")
        for row in reader:
            if row["GEOTYPE"]!="02" or row["GOVTYPE"]!="002" or row["ST"] not in STATES or row["AGG_DESC"] not in REVENUE_CODES:
                continue
            year=int(row["YEAR"])
            if year not in years:continue
            code=row["AGG_DESC"]
            if row["AGG_DESC_LABEL"]!=REVENUE_CODES[code] or row["CATEGORY"]!="01" or row["ITEM_CODE"]!="AGG":
                raise ValueError(f"Unexpected official revenue category schema {row['ST']}/{year}/{code}")
            if row["AMOUNT_F"] or not row["AMOUNT"].strip().isdigit():
                raise ValueError("Flagged/missing Census federal transfer general revenue aggregate")
            key=(row["ST"],year,code)
            if key in found:raise ValueError("Duplicate official state revenue aggregate "+str(key))
            found[key]=int(row["AMOUNT"])
    expected={(s,y,c) for s in STATES for y in years for c in REVENUE_CODES}
    if set(found)!=expected:
        raise ValueError(f"Unbalanced Census state revenue codes: absent={len(expected-set(found))}, extra={len(set(found)-expected)}")
    return found,sha

def build():
    original=json.loads(FISCAL.read_text(encoding="utf-8"))
    if len(original.get("records",[]))!=650:
        raise ValueError("Census capital outlay panel must be 650 state-year records")
    data,sources=load_fred()
    revenue,sha=load_census_transfers()
    output=[]
    for row in original["records"]:
        state=row["fipsState"]
        fiscal_year=row["fiscalYear"]
        baseline=fiscal_year-2
        past=fiscal_year-3
        rgdp=data["realGDP"]
        unemployment=data["unemployment"]
        key1=(state,f"{baseline:04d}-01-01")
        key0=(state,f"{past:04d}-01-01")
        if key1 not in rgdp or key0 not in rgdp or rgdp[key0]<=0:
            raise ValueError(f"Missing BEA GDP annual series for {state} {past}/{baseline}")
        gdp_pct=100*(rgdp[key1]/rgdp[key0]-1)
        monthly=[unemployment[(state,f"{baseline:04d}-{month:02d}-01")] for month in range(1,13)
                 if (state,f"{baseline:04d}-{month:02d}-01") in unemployment]
        if len(monthly)!=12:raise ValueError(f"Missing BLS monthly unemployment {state}/{baseline}")
        unemp_pct=sum(monthly)/12
        general=revenue[(state,fiscal_year,"SF0002")]
        fed=revenue[(state,fiscal_year,"SF0004")]
        if general<=0 or fed<0 or fed>general:
            raise ValueError(f"Invalid Census revenue composition {state}/{fiscal_year}")
        output.append({
          "id":row["id"],"fipsState":state,"stateAbbreviation":STATES[state],"fiscalYear":fiscal_year,
          "gdpGrowthPriorAvailableCalendarYearPct":round(gdp_pct,6),
          "unemploymentPriorAvailableCalendarYearPct":round(unemp_pct,6),
          "gdpCalendarYear":baseline,"unemploymentCalendarYear":baseline,
          "federalTransfersShareOfCurrentGeneralRevenue":round(fed/general,9),
          "federalTransfersThousandsUSD":fed,"totalGeneralRevenueThousandsUSD":general,
          "transferSourceFiscalYear":fiscal_year,
          "preTreatmentStatus":{
              "macroLaggedCalendarYear":"FY_year_minus_2; not verified published by each state's budget proposal date",
              "federalTransfer":"contemporaneous outcome-year fiscal value, possibly post-treatment mediator",
              "causalControlsVerified":False,
          }
        })
    if len(output)!=650 or len({x["id"] for x in output})!=650:
        raise ValueError("Duplicate/absent source-matched economic controls")
    return {
        "schema":"power-atlas.us-state-economic-controls.v1",
        "publicationStatus":"source_linked_complete_650_exploratory_controls_not_prebudget_verified",
        "source":{"censusZip":CENSUS_URL,"censusOriginalSHA256":sha,
                  "censusRevenueCodes":REVENUE_CODES,
                  "economicSourceSeries":sources,
                  "gdpAgency":"US Bureau of Economic Analysis via FRED",
                  "unemploymentAgency":"US Bureau of Labor Statistics via FRED"},
        "coverage":{"years":list(range(2012,2025)),"states":50,"stateYears":650,
                    "BEAAnnualGrowthObservations":650,"BLSAnnualMonthlyAverages":650,
                    "CensusCurrentYearFederalTransferShares":650},
        "researchReadiness":{"historicallyVerifiedPreBudgetControls":False,
             "federalTransferEndogeneityUnresolved":True,
             "historicalFiscalClockStillProvisional":True,
             "causalModelReady":False},
        "records":sorted(output,key=lambda r:(r["fipsState"],r["fiscalYear"])),
        "causalEffect":None,
        "warning":"Official BEA/BLS/Census values, but the transfer share is contemporaneous and may be a mediator; lagged annual economic readings may be revised ex post. For descriptive association, not identified causation."
    }

def main():
    doc=build()
    encoded=json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=encoded:
        OUT.write_text(encoded,encoding="utf-8")
    print(json.dumps({"coverage":doc["coverage"],"sources":len(doc["source"]["economicSourceSeries"]),
        "causalReady":doc["researchReadiness"]["causalModelReady"],
        "example":doc["records"][0]},indent=2))

if __name__=="__main__":
    main()
