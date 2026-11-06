"""Audit the official ACS-to-ZCTA observations used in all nine life categories.

This source smoke test uses Census Reporter's documented public, keyless API.
It saves only publicly reported, rounded ZCTA estimates for the fixed sample
ZIP 10001, never a user's selected ZIP. Each category is queried separately
and failure of any required source leaves prior published evidence unchanged.

USPS ZIPs are not exact Census ZCTAs. These are historical observations
from ACS 2020–2024, not current 2026 prices or causal political effects.
"""
from __future__ import annotations
import datetime as dt
import json
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"data/place-impact/local-measures-v1.json"
OUT=ROOT/"data/place-impact/local-source-health-v1.json"
SAMPLE_ZCTA="10001"
GEOID="86000US"+SAMPLE_ZCTA
TIMEOUT=28

def scalar(m, values):
    raw=[values.get(k) for k in m["columns"]]
    if any(x is None or isinstance(x,bool) for x in raw):return None
    try:nums=[float(x) for x in raw]
    except (TypeError,ValueError):return None
    if any(not (-0.001 <= x <= 1e11) for x in nums):return None
    t=m["format"]
    if t=="share":
        if len(nums)!=2 or nums[1]<=0 or nums[0]>nums[1]:return None
        result=100*nums[0]/nums[1]
    elif t=="sumshare":
        top,den=sum(nums[:-1]),nums[-1]
        if den<=0 or top>den:return None
        result=100*top/den
    elif t=="sumcount":result=sum(nums)
    elif t in ("usd","count","years") and len(nums)==1:result=nums[0]
    else:return None
    return round(result,2)

def request(url,fetcher=None):
    if fetcher:return fetcher(url)
    rq=urllib.request.Request(url,headers={"User-Agent":"PowerAtlasResearch/1.0","Accept":"application/json"})
    with urllib.request.urlopen(rq,timeout=TIMEOUT) as r:
        if r.status!=200:raise RuntimeError(f"Source HTTP {r.status}")
        body=r.read(1_000_001)
        if len(body)>1_000_000:raise RuntimeError("Unexpectedly large public response")
        return json.loads(body)

def collect(fetcher=None):
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    result={}
    for topic,config in spec["issues"].items():
        tables=sorted({m["table"] for m in config["measures"]})
        query=urllib.parse.urlencode({
            "table_ids":",".join(tables),
            "geo_ids":GEOID
        })
        url=spec["provider"]["api"]+"?"+query
        d=request(url,fetcher)
        if d.get("release",{}).get("id")!=spec["provider"]["release"]:
            raise ValueError(topic+": unexpected ACS release, refusing to publish")
        if not d.get("data",{}).get(GEOID) or not all(x in d.get("tables",{}) for x in tables):
            raise ValueError(topic+": absent GEOID or source tables")
        measures=[]
        for m in config["measures"]:
            value=scalar(m,d["data"][GEOID][m["table"]].get("estimate",{}))
            measures.append({"id":m["id"],"table":m["table"],"value":value,"format":m["format"],
                            "status":"observed_acs_estimate" if value is not None else "suppressed_or_unavailable"})
        if not any(x["status"]=="observed_acs_estimate" for x in measures):
            raise ValueError(topic+": no usable measures, preserving previous source")
        result[topic]={"sourceURL":url,"measures":measures}
    if len(result)!=9:raise ValueError("All nine categories are required")
    return {"schema":"power-atlas.place-impact.local-source-health.v1",
            "generatedUTC":dt.datetime.now(dt.timezone.utc).isoformat(),
            "sampleZCTA":SAMPLE_ZCTA,"sampleIsNotUserLocation":True,
            "release":spec["provider"]["release"],
            "source":spec["provider"]["api"],
            "sourceType":"Census Reporter public API forwarding Census Bureau ACS data",
            "observations":result,
            "warning":"A passing public-data source smoke test does not confirm browser CORS, ZIP vs ZCTA equivalence or household-level political causation."}

def save(doc):
    if len(doc.get("observations",{}))!=9:raise ValueError("Do not commit incomplete audit")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    p=OUT.with_suffix(".tmp")
    p.write_text(json.dumps(doc,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    p.replace(OUT)

if __name__=="__main__":
    d=collect()
    save(d)
    print(json.dumps({k:{"found":sum(m["value"] is not None for m in v["measures"]),"expected":len(v["measures"])}
                      for k,v in d["observations"].items()}))
