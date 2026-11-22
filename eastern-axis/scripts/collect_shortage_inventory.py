#!/usr/bin/env python3
"""Independent U.S. supply-context signals: EIA fuel stocks and Census ratios via FRED.

Source semantics: EIA gasoline stocks are product-family wholesale stocks, NOT
station-level availability. FRED ratios are broad sector measures, NOT product stocks.
Failure is explicitly missing evidence; never carry old data forward as fresh.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, datetime, timezone
from io import StringIO
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"public/analysis/product-inventory-context.json"
WEEKLY_URL="https://ir.eia.gov/wpsr/table5.csv"
EIA_SOURCE="https://www.eia.gov/petroleum/supply/weekly/"
FRED={
  "ISRATIO": ("Total business inventory-to-sales ratio","All US industries; contextual only"),
  "MNFCTRIRSA": ("Manufacturers inventory-to-sales ratio","US manufacturing; contextual only"),
  "RETAILIRSA": ("Retailers inventory-to-sales ratio","US retail; contextual only"),
  "MRTSIR4400AUSS": ("Retail inventory-to-sales ratio excluding motor vehicles","US non-auto retail; contextual only"),
}
MAX_BYTES=900_000

def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def fetch(url,accept="text/csv"):
    req=Request(url,headers={"User-Agent":"EasternAxis/1.0 (open-source public-data monitoring)",
                             "Accept":accept})
    with urlopen(req,timeout=20) as response:
        payload=response.read(MAX_BYTES+1)
        if len(payload)>MAX_BYTES:raise ValueError("Public dataset exceeds limit")
        return payload.decode("utf-8-sig")

def numeric(v):
    try:
        n=float(str(v or "").replace(",",""))
        if not (0<n<1e9):raise ValueError("Out-of-range source observation")
        return n
    except (ValueError,TypeError):
        raise ValueError("Non-positive or missing source reading") from None

def wpsr_date(v):
    return datetime.strptime(str(v).strip(),"%m/%d/%y").date()

def parse_eia(text,today=None):
    """Parse EIA Table 5 labelled U.S. gasoline stocks, never PADD or blendstocks."""
    today=today or datetime.now(timezone.utc).date()
    rows=list(csv.reader(StringIO(text)))
    if len(rows)<2 or len(rows[0])<7:raise ValueError("EIA table5 CSV missing columns")
    header=rows[0]
    current,past,prior_year=(wpsr_date(header[i]) for i in (2,3,5))
    if not (0<=(today-current).days<=16 and 4<=(current-past).days<=10
            and 340<=(current-prior_year).days<=390):
        raise ValueError("EIA observation dates stale or inconsistent")
    found=[row for row in rows[1:] if len(row)>=7 and
           row[0].strip().casefold()=="motor gasoline" and
           row[1].strip().casefold()=="total motor gasoline"]
    if len(found)!=1:raise ValueError("EIA unique U.S. gasoline inventory series not found")
    row=found[0]
    now,week,year=(numeric(row[i]) for i in (2,3,5))
    return {"id":"eia-us-gasoline-stocks","kind":"direct-inventory",
            "label":"U.S. total motor gasoline stocks","scope":"United States; wholesale motor gasoline inventories",
            "productId":"fuel","unit":"million barrels","value":round(now,3),
            "previous":round(week,3),"yearAgo":round(year,3),
            "changeWeekPct":round((now/week-1)*100,2),
            "changeYearPct":round((now/year-1)*100,2),
            "period":current.isoformat(),"previousPeriod":past.isoformat(),
            "yearAgoPeriod":prior_year.isoformat(),"source":"EIA Weekly Petroleum Status Report, Table 5",
            "sourceUrl":EIA_SOURCE,"publicationFrequency":"weekly",
            "limitation":"Aggregate gasoline stocks cannot establish retail station outages, delivery destinations or imminent stockouts"}

def parse_fred(text,series,today=None):
    today=today or datetime.now(timezone.utc).date()
    reader=csv.DictReader(StringIO(text))
    if not reader.fieldnames or series not in reader.fieldnames:
        raise ValueError("FRED CSV does not contain requested inventory ratio")
    dates=[k for k in reader.fieldnames if k in ("DATE","observation_date")]
    if len(dates)!=1:raise ValueError("FRED CSV missing date")
    values=[]
    for row in reader:
        try:
            day=date.fromisoformat(str(row[dates[0]])[:10])
            v=numeric(row[series])
            if day<=today: values.append((day,v))
        except (ValueError,TypeError,KeyError):continue
    values=sorted(dict(values).items())
    if len(values)<13:raise ValueError("FRED inventory ratio lacks baseline history")
    period,value=values[-1]
    if (today-period).days>115:raise ValueError("FRED inventory ratio observations too old")
    prior=values[-2][1]
    prior_year=values[-13][1]
    title,scope=FRED[series]
    return {"id":"fred-"+series,"kind":"sector-inventory-ratio","label":title,
            "scope":scope,"unit":"months of sales (ratio)","value":round(value,4),
            "previous":round(prior,4),"yearAgo":round(prior_year,4),
            "changeMonthPct":round((value/prior-1)*100,2),
            "changeYearPct":round((value/prior_year-1)*100,2),
            "period":period.isoformat(),"previousPeriod":values[-2][0].isoformat(),
            "source":"U.S. Census Bureau via FRED","sourceUrl":"https://fred.stlouisfed.org/series/"+series,
            "publicationFrequency":"monthly","limitation":"Broad inventory-to-sales context is not item-level supply or verified product availability"}

def collect(now=None, downloader=fetch):
    now=now or datetime.now(timezone.utc)
    today=now.date()
    sources=[]
    metrics=[]
    try:
        eia=parse_eia(downloader(WEEKLY_URL),today=today)
        metrics.append(eia)
        sources.append({"id":"eia-wpsr-table5","status":"ok","period":eia["period"],"url":EIA_SOURCE})
    except Exception as e:
        sources.append({"id":"eia-wpsr-table5","status":"unavailable","detail":type(e).__name__+
                        ": EIA stock series could not be source-verified","url":EIA_SOURCE})
    for sid in FRED:
        url="https://fred.stlouisfed.org/graph/fredgraph.csv?"+urlencode({"id":sid,"cosd":"2023-01-01"})
        try:
            m=parse_fred(downloader(url),sid,today=today)
            metrics.append(m)
            sources.append({"id":"fred-"+sid,"status":"ok","period":m["period"],"url":m["sourceUrl"]})
        except Exception as e:
            sources.append({"id":"fred-"+sid,"status":"unavailable","detail":type(e).__name__+
                            ": inventory ratio could not be source-verified","url":"https://fred.stlouisfed.org/series/"+sid})
    return {"schemaVersion":1,"checkedAt":iso_now(),"status":"source-dated" if len(metrics)==len(sources)
            else "partial" if metrics else "unavailable","metrics":metrics,"sources":sources,
            "coverage":{"verified":len(metrics),"requested":len(sources),
              "productSpecificDirectInventory":int(any(m["kind"]=="direct-inventory" for m in metrics)),
              "sectorContext":sum(m["kind"]=="sector-inventory-ratio" for m in metrics)},
            "limitations":["U.S. aggregates cannot be generalized to another country's retail availability.",
                           "Inventory-to-sales ratios have monthly publication lags; high demand can lower ratios even when inventory rises.",
                           "No product-specific food, medicine, semiconductor or local shelf inventory collection is verified."]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=OUT)
    args=parser.parse_args()
    report=collect()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"coverage":report["coverage"],"sources":report["sources"]}))

if __name__=="__main__":
    main()
