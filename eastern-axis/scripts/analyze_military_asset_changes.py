#!/usr/bin/env python3
"""Eastern Axis military asset change analyst.

A SIPRI TIV delivery-volume anomaly is NOT a change in equipment inventory.
World Bank armed-forces personnel are historical estimates, NOT 2026 troop
counts. Dated national/UNROCA equipment holdings are a separate input; absent
comparable disclosure years, no equipment-change assertion is made.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
from statistics import median
import tempfile
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"public/analysis/military-asset-changes.json"
HOLDINGS=ROOT/"public/analysis/military-holdings-history.json"
INVENTORY=ROOT/"public/analysis/military-inventory.json"
WDI="https://api.worldbank.org/v2"
SERIES={
    "MS.MIL.MPRT.KD":("Arms imports","arms-transfer-volume","SIPRI transfer trend-indicator values","SIPRI via World Bank WDI"),
    "MS.MIL.XPRT.KD":("Arms exports","arms-transfer-volume","SIPRI transfer trend-indicator values","SIPRI via World Bank WDI"),
    "MS.MIL.TOTL.P1":("Armed forces personnel","personnel-estimate","people","IISS via World Bank WDI"),
}
INVENTORY_CATEGORIES={"Land","Naval","Air","Missiles","Nuclear","Personnel"}
MIN_HISTORY=8
USER_AGENT="EasternAxis-OSINT/1.0 (public-data analyst; non-tactical)"

def now():
    return datetime.now(timezone.utc)

def timestamp(stamp):
    return stamp.isoformat(timespec="seconds").replace("+00:00","Z")

def https_url(url):
    if not isinstance(url,str) or len(url)>600:return False
    p=urllib.parse.urlsplit(url)
    return p.scheme=="https" and bool(p.hostname) and not p.username and not p.password and p.port in (None,443)

def get_json(url):
    request=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=35) as response:
        payload=response.read(15_000_001)
    if len(payload)>15_000_000:raise ValueError("WDI data larger than configured cap")
    return json.loads(payload)

def checked_page(response, name):
    if not isinstance(response,list) or len(response)!=2 or not isinstance(response[0],dict) or not isinstance(response[1],list):
        raise ValueError(name+": invalid World Bank response shape")
    meta=response[0]
    pages=int(meta.get("pages",0))
    total=int(meta.get("total",-1))
    if pages!=1 or total<0 or total>len(response[1]):
        raise ValueError(name+": truncated paginated response rejected")
    return response[1]

def crosswalk(response):
    rows=checked_page(response,"WDI country crosswalk")
    countries={}
    for entry in rows:
        if not isinstance(entry,dict):continue
        iso3=entry.get("id")
        iso2=entry.get("iso2Code")
        region=entry.get("region")
        if isinstance(iso3,str) and re.fullmatch("[A-Z]{3}",iso3) and isinstance(iso2,str) and re.fullmatch("[A-Z]{2}",iso2) and isinstance(region,dict) and region.get("id")!="NA":
            countries[iso3]=iso2
    if len(countries)<100:raise ValueError("WDI crosswalk has unexpectedly few countries")
    return countries

def parse_indicator(response, countries, indicator, as_of):
    records=defaultdict(dict)
    for row in checked_page(response,indicator):
        if not isinstance(row,dict):continue
        code=countries.get(row.get("countryiso3code"))
        raw_year=str(row.get("date") or "")
        value=row.get("value")
        if not code or not re.fullmatch(r"20\d\d",raw_year):continue
        year=int(raw_year)
        if year<2009 or year>as_of.year or isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:continue
        if indicator=="MS.MIL.TOTL.P1" and value!=int(value):continue
        if year in records[code]:raise ValueError("duplicate country / year observation "+indicator+" "+code+" "+raw_year)
        records[code][year]={"value":float(value),
            "country":str((row.get("country") or {}).get("value") or code)[:100]}
    return records

def robust_change(history, value, indicator):
    """Eight actual annual prior values; never fill absent years with zero."""
    if len(history)!=MIN_HISTORY or not all(math.isfinite(x) and x>=0 for x in history):
        return {"status":"insufficient-history","robustZ":None,"median":None,"changePct":None,"direction":"unassessed"}
    center=median(history)
    mad=median(abs(n-center) for n in history)
    # TIV is a volume indicator in reported dollar-equivalent units; use a
    # non-trivial floor to avoid explosive z-scores from sparse zero values.
    floor=(max(2.0,0.06*center) if indicator=="HOLDINGS" else
           4_000 if indicator=="MS.MIL.TOTL.P1" else 60_000_000)
    spread=max(1.4826*mad,0.12*center,floor)
    z=(value-center)/spread
    change=None if center==0 else 100*(value/center-1)
    direction="within-baseline"
    if center==0:
        direction="unassessed"  # Zero-only histories cannot establish percent changes.
    elif indicator=="HOLDINGS":
        if z>=3 and change>=30 and value>=5:direction="expanding"
        elif z<=-3 and change<=-30 and center>=5:direction="contracting"
    elif indicator=="MS.MIL.TOTL.P1":
        if z>=3 and change>=25:direction="expanding"
        elif z<=-3 and change<=-25:direction="contracting"
    else:
        if z>=3 and change>=50 and value>=150_000_000:direction="expanding"
        elif z<=-3 and change<=-50 and center>=150_000_000:direction="contracting"
    return {"status":"assessable","robustZ":round(z,2),"median":round(center,2),
            "changePct":round(change,1) if change is not None else None,"direction":direction}

def annual_review(code, country, indicator, series, as_of):
    title,kind,unit,publisher=SERIES[indicator]
    years=sorted(series)
    latest=years[-1]
    value=series[latest]["value"]
    prior_years=list(range(latest-MIN_HISTORY,latest))
    consecutive=all(y in series for y in prior_years)
    history=[series[y]["value"] for y in prior_years] if consecutive else []
    stats=robust_change(history,value,indicator)
    stale=latest<as_of.year-2
    anomaly=stats["direction"] in ("expanding","contracting") and not stale
    # Transfer volumes are delivered major arms, not domestic production,
    # operational readiness, troop positions or complete inventories.
    source_url=f"https://data.worldbank.org/indicator/{indicator}?locations={code}"
    status="historical" if stale else "review" if anomaly else "data-gap" if not consecutive else "monitor"
    return {
        "id":indicator.replace(".","-")+"-"+code,"code":code,"country":country,
        "metricId":indicator,"metric":title,"kind":kind,"unit":unit,
        "observationYear":latest,"value":value,"previousYear":latest-1 if latest-1 in series else None,
        "previousValue":series[latest-1]["value"] if latest-1 in series else None,
        "history":[{"year":y,"value":series[y]["value"]} for y in prior_years if y in series]+[{"year":latest,"value":value}],
        "baseline":stats,"status":status,"anomalous":anomaly,
        "modelReviewed":False,"modelDecision":None,"reviewedException":False,
        "source":publisher,"sourceUrl":source_url,"sourceDate":str(latest),
        "evidenceClass":"transfers-not-inventory" if kind=="arms-transfer-volume" else "personnel-not-equipment",
        "notInventoryChange":True,"confidence":"screen-only" if anomaly else "not-assessed",
        "reason":(
            "Historical annual observation only; no current 2026 change inferred." if stale else
            "Statistically unusual annual arms-delivery volume; equipment holdings, readiness and location are not established." if anomaly and kind=="arms-transfer-volume" else
            "Historical personnel estimate outside the annual comparison range; not a current troop deployment." if anomaly else
            "Fewer than eight uninterrupted preceding annual observations; no normal-range estimate." if not consecutive else
            "Latest annual reading is within the screen's historical bounds."),
    }

def validate_holdings(doc):
    if not isinstance(doc,dict) or doc.get("schemaVersion")!=1 or not isinstance(doc.get("observations"),list):
        raise ValueError("Invalid public military-holdings history schema")
    rows=[]
    seen=set()
    for row in doc["observations"]:
        if not isinstance(row,dict):raise ValueError("Invalid holdings row")
        code=row.get("code");year=row.get("year");category=row.get("category")
        label=row.get("equipmentType");count=row.get("count")
        basis=row.get("basis");src=row.get("sourceUrl")
        if not (isinstance(code,str) and re.fullmatch("[A-Z]{2}",code) and
            isinstance(year,int) and 1990<=year<=now().year and
            category in INVENTORY_CATEGORIES and isinstance(label,str) and 3<=len(label)<=90 and
            isinstance(count,int) and not isinstance(count,bool) and count>=0 and
            isinstance(basis,str) and 3<=len(basis)<=140 and https_url(src) and
            row.get("sourceReviewed") is True and isinstance(row.get("publisher"),str)):
            raise ValueError("Unreviewed or malformed official holdings record")
        key=(code,category,label,basis,year)
        if key in seen:raise ValueError("Duplicate national equipment category + year")
        seen.add(key)
        rows.append(row)
    return rows

def assess_holdings(rows,as_of):
    """Only a continuous and normalized series can show unusual inventory change."""
    grouped=defaultdict(dict)
    for row in rows:
        key=(row["code"],row["category"],row["equipmentType"],row["basis"])
        grouped[key][row["year"]]=row
    output=[]
    for (code,category,equipment,basis),years in sorted(grouped.items()):
        latest=max(years)
        current=years[latest]
        last_years=list(range(latest-MIN_HISTORY,latest))
        if any(y not in years for y in last_years):history=[]
        else:history=[years[y]["count"] for y in last_years]
        baseline=robust_change(history,current["count"],"HOLDINGS")
        prev=years.get(latest-1)
        trend=baseline["direction"]
        stale=latest<as_of.year-2
        # Even a pronounced movement in two reports is NOT automatically
        # evidence of actual new inventory; category definitions can change.
        eligible=bool(prev and current["count"]!=prev["count"] and len(history)==MIN_HISTORY
                      and not stale and trend in ("expanding","contracting") and
                      current["sourceUrl"]!=prev["sourceUrl"])
        output.append({"id":"holdings-"+code+"-"+re.sub("[^a-z0-9]+","-",equipment.lower()).strip("-"),
            "code":code,"country":current.get("countryName") or code,"metricId":"HOLDINGS",
            "metric":category+" / "+equipment,"kind":"equipment-holdings","unit":"units",
            "observationYear":latest,"value":current["count"],
            "previousYear":latest-1 if prev else None,
            "previousValue":prev["count"] if prev else None,
            "history":[{"year":y,"value":years[y]["count"]} for y in last_years if y in years]+[{"year":latest,"value":current["count"]}],
            "baseline":baseline,"status":"review" if eligible else "historical" if stale else "data-gap" if len(history)<MIN_HISTORY else "monitor",
            "anomalous":eligible,"modelReviewed":False,"modelDecision":None,"reviewedException":False,
            "source":current["publisher"],"sourceUrl":current["sourceUrl"],
            "sourceDate":str(latest),"evidenceClass":"national-holdings",
            "notInventoryChange":not eligible,"confidence":"screen-only" if eligible else "not-assessed",
            "reason":("Comparable public equipment-holdings reports show an exceptional change; analyst validation pending."
                      if eligible else "Inadequate consistent years or no exceptional change in the official disclosed holdings."),
            "basis":basis,"previousSourceUrl":prev["sourceUrl"] if prev else None})
    return output

def report_from_series(data,holding_doc,inventory_doc,as_of=None,checked_at=None):
    checked_at=checked_at or now()
    as_of=as_of or checked_at
    observations=[]
    states=[]
    for indicator in SERIES:
        countries=data.get(indicator,{})
        if not isinstance(countries,dict):raise ValueError("Missing structured source series")
        for code,annual in sorted(countries.items()):
            if annual:
                year=max(annual)
                observations.append(annual_review(code,annual[year]["country"],indicator,annual,as_of))
        states.append({"id":indicator,"status":"ok","countries":len(countries),
            "url":"https://data.worldbank.org/indicator/"+indicator,
            "publisher":SERIES[indicator][3]})
    holdings=assess_holdings(validate_holdings(holding_doc),as_of)
    observations.extend(holdings)
    if inventory_doc.get("schemaVersion")!=1 or not isinstance(inventory_doc.get("assets"),list):
        raise ValueError("Published military inventory reference unavailable")
    current_assets=inventory_doc["assets"]
    reference_countries=len({r.get("code") for r in current_assets if r.get("code")})
    references=len(current_assets)
    # Inventory reference alone contains no year-over-year comparisons.
    observed=set(x["code"] for x in observations)
    status_count={k:sum(x["status"]==k for x in observations) for k in ("review","monitor","historical","data-gap","assessed")}
    return {
      "schemaVersion":1,"category":"Defense, Security & Cyber","analystName":"Military Asset Change Analyst",
      "generatedAt":timestamp(checked_at),"status":"ok","mode":"annual-public-source-surveillance",
      "method":"Eight uninterrupted historical annual country-specific observations; robust median/MAD screen; latest publication age; original provenance; optional AI review.",
      "summary":{"countries":len(observed),"series":len(observations),
         "reviewCandidates":status_count["review"],"assessedExceptions":status_count["assessed"],
         "historical":status_count["historical"],"monitoring":status_count["monitor"],
         "dataGaps":status_count["data-gap"],
         "confirmedInventoryChanges":0,"existingInventoryReferences":references,
         "inventoryReferenceCountries":reference_countries},
      "ai":{"status":"not-run","reviewed":0,"model":None,"role":"Advisory, never overrides source verification or turns arms transfers into equipment holdings"},
      "sources":states+[{"id":"national-holdings","status":"ok" if holdings else "unpopulated",
        "countries":len({x["code"] for x in holdings}),
        "url":"https://www.unroca.org/","publisher":"UNROCA and official national inventories",
        "note":"Voluntary holdings coverage; indexed only after comparable original records are verified"}],
      "assessments":observations,
      "limitations":[
        "SIPRI arms-transfer TIV is the volume of major conventional arms deliveries, not inventory size, purchase price or military strength.",
        "World Bank military personnel values are historical IISS estimates and exclude reserve personnel; publication lag is not current deployment.",
        "Military assets in the existing Defense inventory are point-in-time estimates; a single year cannot establish abnormal change.",
        "UNROCA national holdings are voluntary, intermittent, and may omit classified systems. Missing records are not zeros.",
        "An abnormal transfer-volume screen is not a confirmed equipment buildup, intent to attack, or a verified shift in battlefield readiness.",
        "Analyst opinions cannot promote unsupported signals. No live unit tracking or tactical targeting.",
      ]
    }

def verified_model_summary(row, decision):
    """Never publish unverified facts, baselines or intent from LLM prose."""
    baseline=row["baseline"]
    kind=("SIPRI arms-transfer volume" if row["kind"]=="arms-transfer-volume" else
          "reported military equipment count" if row["kind"]=="equipment-holdings" else
          "historical military personnel estimate")
    value=row["value"]
    center=baseline.get("median")
    z=baseline.get("robustZ")
    return (f"Local AI recommendation: {decision}. "
            f"The {row['observationYear']} {kind} was {value:,.0f}; "
            f"the median of the eight preceding calendar-year observations was "
            f"{center:,.0f} (robust Z {z}). "
            "This comparison alone does not establish new operational equipment, readiness or intent.")

def review_with_model(report,endpoint,model="qwen2.5:1.5b"):
    """AI can review source-dated candidates but never assert hardware holdings."""
    candidates=[row for row in report["assessments"] if row["status"]=="review"][:25]
    reviewed=0
    for row in candidates:
        prompt=("Assess ONE statistically screened country military data change. "
          "This is historical annual data; SIPRI transfer values are NOT asset inventories. "
          "No claims about unit positions, intent, readiness or specific delivered quantities. "
          "Return JSON with id,decision,rationale. decision=investigate or monitor. "
          "rationale 20-240 characters, grounded ONLY in provided values. "
          "Do not fabricate additional sources. "
          +json.dumps({k:row[k] for k in ("id","country","metric","kind","value","observationYear","baseline","sourceUrl","evidenceClass")}))
        payload=json.dumps({"model":model,"format":"json","stream":False,
                            "options":{"temperature":0,"num_predict":210},"prompt":prompt}).encode()
        req=urllib.request.Request(endpoint.rstrip("/")+"/api/generate",data=payload,
                                   headers={"Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=75) as response:
                output=json.loads(json.load(response).get("response",""))
            if not isinstance(output,dict) or output.get("id")!=row["id"] or output.get("decision") not in ("investigate","monitor"):
                continue
            reason=output.get("rationale")
            if not isinstance(reason,str) or not 20<=len(reason)<=240:continue
        except (OSError,ValueError,TypeError,KeyError):
            continue
        row["modelReviewed"]=True
        row["modelDecision"]=output["decision"]
        row["analystRationale"]=verified_model_summary(row,output["decision"])
        reviewed+=1
        if output["decision"]=="investigate" and row["anomalous"]:
            row["reviewedException"]=True
            row["status"]="assessed"
            row["confidence"]="reviewed-historical-exception-not-threat"
    report["ai"]={"status":"reviewed" if reviewed else "unavailable","reviewed":reviewed,
                  "model":model if reviewed else None,
                  "role":"Advisory over measured historical anomalies; no inference of physical inventory without national holdings"}
    report["summary"]["reviewCandidates"]=sum(x["status"]=="review" for x in report["assessments"])
    report["summary"]["assessedExceptions"]=sum(x["status"]=="assessed" for x in report["assessments"])
    report["summary"]["confirmedInventoryChanges"]=sum(
      x["status"]=="assessed" and x["kind"]=="equipment-holdings" for x in report["assessments"])
    return report

def collect(fetch=get_json,as_of=None):
    as_of=as_of or now()
    country_rows=fetch(WDI+"/country?format=json&per_page=400")
    countries=crosswalk(country_rows)
    series={}
    for indicator in SERIES:
        # Annual report includes only the 2009–2026 source window, not every
        # historical WDI record. Never silently truncate a second page.
        query=urllib.parse.urlencode({"format":"json","date":"2009:2026","per_page":10000})
        url=f"{WDI}/country/all/indicator/{indicator}?{query}"
        records=parse_indicator(fetch(url),countries,indicator,as_of)
        if len(records)<20:raise ValueError("Insufficient country coverage for "+indicator)
        series[indicator]=records
    return series

def write_atomic(out,doc):
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=out.parent,delete=False) as tmp:
        json.dump(doc,tmp,indent=2,ensure_ascii=False)
        tmp.write("\n")
        name=tmp.name
    os.replace(name,out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=OUTPUT)
    p.add_argument("--model-endpoint",default="")
    p.add_argument("--review-only",action="store_true")
    args=p.parse_args()
    if args.review_only:
        if not args.model_endpoint or not args.output.exists():raise SystemExit("Local model and existing source snapshot required")
        report=json.loads(args.output.read_text())
        if report.get("schemaVersion")!=1:raise SystemExit("Invalid existing snapshot")
    else:
        data=collect()
        if not HOLDINGS.exists() or not INVENTORY.exists():raise SystemExit("Military holdings and reference input missing")
        holdings=json.loads(HOLDINGS.read_text())
        inventory=json.loads(INVENTORY.read_text())
        report=report_from_series(data,holdings,inventory)
    if args.model_endpoint:report=review_with_model(report,args.model_endpoint)
    if report["summary"]["series"]<40:raise SystemExit("Suspiciously incomplete global source series")
    write_atomic(args.output,report)
    print("Military asset analyst:",report["summary"],"AI:",report["ai"]["status"])

if __name__=="__main__":
    main()
