#!/usr/bin/env python3
"""No-key source discovery: BEA/BLS FRED downloadable CSV and Census state revenue categories.

Does not publish data or infer values. Source selection happens only after
actual live response shapes have been verified in GitHub Actions.
"""
import csv
import io
import json
import urllib.request
import zipfile
from collections import Counter
from scripts.probe_census_state_timeseries_zip import download

def csv_probe(code):
    url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}"
    request=urllib.request.Request(url,headers={"User-Agent":"PowerAtlasResearch/1.0 (noncommercial public research source discovery)","Accept":"text/csv"})
    with urllib.request.urlopen(request,timeout=30) as response:
        body=response.read(700000)
        final=response.geturl()
    if len(body)>=700000:raise ValueError("FRED source unexpected size")
    rows=list(csv.reader(io.StringIO(body.decode("utf-8-sig"))))
    return {"series":code,"uri":url,"finalURI":final,"header":rows[0],
            "count":len(rows)-1,"first":rows[1:4],
            "years2010to2024Sample":[r for r in rows[1:] if r[0].startswith(("2010-01","2012-01","2020-01","2024-01"))][:8]}

def census_probe():
    body=download()
    with zipfile.ZipFile(io.BytesIO(body)) as z, z.open("GOVSSTATEFINTIMESERIES.dat") as src:
        r=csv.DictReader(io.TextIOWrapper(src,encoding="utf-8-sig"),delimiter="|")
        found={}
        for row in r:
            desc=row["AGG_DESC_LABEL"]
            if row["GEOTYPE"]!="02" or row["GOVTYPE"]!="002" or row["ST"]!="01" or row["YEAR"]!="2022":
                continue
            if ("revenue" in desc.lower() or "federal" in desc.lower()) and row["ITEM_CODE"]=="AGG":
                code=row["AGG_DESC"]
                found[code]={"label":desc,"category":row["CATEGORY"],"item":row["ITEM_CODE"],"amountFlag":row["AMOUNT_F"]}
        return sorted(found.items())

if __name__=="__main__":
    print(json.dumps({"fred":[csv_probe("ALRGSP"),csv_probe("ALUR")],"census2022AlabamaRevenueAggregateCodes":census_probe()},indent=2))
