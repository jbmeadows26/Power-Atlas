"""Collect official, **unaltered** 2024 TIGER/Line state legislative polygons.

Store original Census ZIP shapefiles, not generalized API geometry. Validate
all district geometry records using pyshp and persist original-byte SHA256.
Nebraska has a unicameral legislature (upper-chamber TIGER geography only).
This is a geometric baseline, NOT the full legal redistricting plan history.
"""
import hashlib
import json
import time
import urllib.error
import urllib.request
import urllib.parse
import zipfile
import io
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/geography/state-legislative-2024"
BASE="https://www2.census.gov/geo/tiger/TIGER2024"
MAX_COMPRESSED=8_000_000
MAX_EXPANDED=60_000_000

def archive(fips,chamber):
    layer={"upper":"SLDU","lower":"SLDL"}[chamber]
    filename=f"tl_2024_{fips}_{layer.lower()}.zip"
    url=f"{BASE}/{layer}/{filename}"
    req=urllib.request.Request(url,headers={"User-Agent":"PowerAtlasPublicResearch/1.0 official TIGER/Line download","Accept":"application/zip"})
    error=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=65) as response:
                if urllib.parse.urlsplit(response.geturl()).hostname!="www2.census.gov":
                    raise ValueError("Unrecognized redirect host")
                body=response.read(MAX_COMPRESSED+1)
            if len(body)>MAX_COMPRESSED or not body.startswith(b"PK"):
                raise ValueError("Official source changed or ZIP too large")
            return body,url
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
            error=exc
            if attempt<2:time.sleep(1+attempt)
    raise ValueError(f"{fips} {chamber}: official Census source download failed: {error}")

def validate(body,fips,chamber):
    import shapefile
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        members=z.namelist()
        if sum(x.file_size for x in z.infolist())>MAX_EXPANDED:
            raise ValueError("Oversized uncompressed official district source")
        def get(ext):
            matching=[n for n in members if n.lower().endswith(ext)]
            if len(matching)!=1:raise ValueError(f"Missing/duplicated {ext} shapefile component")
            return io.BytesIO(z.read(matching[0]))
        with shapefile.Reader(shp=get(".shp"),shx=get(".shx"),dbf=get(".dbf")) as reader:
            fields=[v[0] for v in reader.fields[1:]]
            if not {"STATEFP","GEOID"}.issubset(set(fields)):
                raise ValueError(f"Unexpected Census TIGER attribute schema: {fields}")
            seen=set()
            count=0
            total_points=0
            for row in reader.iterShapeRecords():
                vals=dict(zip(fields,list(row.record)))
                if str(vals["STATEFP"]).zfill(2)!=fips or not str(vals["GEOID"]).startswith(fips):
                    raise ValueError("Foreign state boundary found in ZIP")
                geoid=str(vals["GEOID"])
                if geoid in seen:raise ValueError("Repeated district identifier")
                seen.add(geoid)
                if row.shape.shapeType not in (5,15,25) or len(row.shape.points)<3:
                    raise ValueError("Geometry missing / not a polygon")
                total_points+=len(row.shape.points)
                count+=1
            if count==0:raise ValueError("No polygon features in official file")
    return {"features":count,"vertices":total_points,"distinctGEOIDs":len(seen)}

def build():
    states=[s for s in json.loads((ROOT/"data/geography/states.json").read_text())["states"] if s["postal"] not in ("DC","PR")]
    if len(states)!=50:raise ValueError("Expected 50-state geography inventory")
    OUT.mkdir(parents=True,exist_ok=True)
    collected=[]
    for state in states:
        for chamber in ("upper","lower"):
            if state["postal"]=="NE" and chamber=="lower":
                collected.append({"state":"NE","fips":state["fips"],"chamber":chamber,"status":"not_applicable_unicameral_state","features":0,"source":None,"path":None})
                continue
            body,url=archive(state["fips"],chamber)
            info=validate(body,state["fips"],chamber)
            name=f'{state["postal"]}-{chamber}.zip'
            (OUT/name).write_bytes(body)
            collected.append({"state":state["postal"],"fips":state["fips"],"chamber":chamber,
                "status":"official_exact_original_zip_2024_geometries_ingested",
                "source":url,"path":f"data/geography/state-legislative-2024/{name}",
                "sha256OriginalZIP":hashlib.sha256(body).hexdigest(),
                "sourceBytes":len(body),**info})
            print(state["postal"],chamber,info["features"],len(body),flush=True)
            time.sleep(.04)
    counts=Counter(x["state"] for x in collected)
    if len(collected)!=100 or set(counts.values())!={2}:raise ValueError("Missing state/chamber statuses")
    ready=[r for r in collected if r["status"].startswith("official_")]
    if len(ready)!=99:raise ValueError("Expected 99 operational legislative chambers")
    if len({(x["state"],x["chamber"]) for x in collected})!=100:
        raise ValueError("Duplicate state/chamber entries")
    result={"schema":"power-atlas.state-legislative-boundary.v2",
       "publicationStatus":"2024_official_geometry_ingested_historical_legal_plan_lineage_incomplete",
       "year":2024,"sourceAuthority":"US_Census_Bureau_TIGER2024_SLDU_SLDL",
       "states":50,"chamberGeometriesDownloaded":len(ready),
       "upperChambers":50,"lowerChambers":49,
       "notApplicable":1,
       "distinctGEOIDFeatures":sum(x["features"] for x in ready),
       "vertices":sum(x["vertices"] for x in ready),
       "sourceZIPBytes":sum(x["sourceBytes"] for x in ready),
       "legalPlanHistoryComplete":False,
       "warnings":["Source ZIPs are original official shapefiles, no simplification. 2024 mapping is not complete past plan lineage or court-order provenance.",
                   "Nebraska's unicameral legislature has only upper-chamber district geographies.",
                   "TIGER may encode ZZZ undefined areas, which are not seats and must be filtered downstream."],
       "records":collected}
    (OUT/"index.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in ("states","chamberGeometriesDownloaded","distinctGEOIDFeatures","sourceZIPBytes")},indent=2))
if __name__=="__main__":
    build()
