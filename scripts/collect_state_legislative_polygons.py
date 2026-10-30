"""Ingest official state legislative district geometry from Census TIGERweb.

State-by-state 2024 upper/lower boundaries; no plan enactment/court history
is invented. State code coverage is checked, and polygons are preserved as
native Esri rings to avoid silently transforming geometry topology.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/geography/state-legislative-2024"
BASE="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
LAYERS={"upper":5,"lower":6}
MAX_BYTES=14_000_000

def download(layer,fips):
    url=BASE+f"/{layer}/query?"+urllib.parse.urlencode({
       "where":f"STATE='{fips}'","outFields":"*","returnGeometry":"true",
       "outSR":"4326","f":"json","returnM":"false","returnZ":"false"})
    request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"PowerAtlasResearch/1.0 (official public geographic dataset)"})
    with urllib.request.urlopen(request,timeout=75) as r:
        if urllib.parse.urlsplit(r.geturl()).hostname!="tigerweb.geo.census.gov":
            raise ValueError("Unexpected boundary data host redirect")
        raw=r.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError(f"{fips}: oversized state geometry")
    d=json.loads(raw)
    if "error" in d or d.get("exceededTransferLimit"):
        raise ValueError(f"{fips} layer {layer}: truncated/API error: {str(d.get('error',''))[:240]}")
    features=d.get("features")
    if not isinstance(features,list) or len(features)==0:
        raise ValueError(f"{fips} layer {layer}: no usable features")
    keys=("STATE","GEOID","NAME")
    for feature in features:
        a=feature.get("attributes",{})
        if a.get("STATE")!=fips or not a.get("GEOID"):
            raise ValueError(f"{fips}: incorrect state/district identity")
        geo=feature.get("geometry",{})
        if not isinstance(geo.get("rings"),list) or not geo["rings"]:
            raise ValueError(f"{fips}: feature lacks polygon rings")
    return {"stateFIPS":fips,"chamber":layer,"features":features,
       "source":url,"publicationStatus":"official_2024_geometric_baseline_not_legal_plan_history"}

def build():
    states=[s for s in json.loads((ROOT/"data/geography/states.json").read_text())["states"] if s["postal"] not in ("DC","PR")]
    if len(states)!=50:raise ValueError("Expected 50 state geography jurisdictions")
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[]
    for state in states:
        for chamber,layer in LAYERS.items():
            doc=download(layer,state["fips"])
            doc["chamber"]=chamber
            doc["year"]=2024
            target=OUT/f'{state["postal"]}-{chamber}.json'
            target.write_text(json.dumps(doc,separators=(",",":"),ensure_ascii=False),encoding="utf8")
            summary.append({"state":state["postal"],"fips":state["fips"],
                "chamber":chamber,"features":len(doc["features"]),
                "path":str(target.relative_to(ROOT)),
                "source":doc["source"],"status":"source_geometry_downloaded_not_boundary_history_adjudicated"})
            print(state["postal"],chamber,len(doc["features"]),flush=True)
            time.sleep(.09)
    counts=Counter(r["state"] for r in summary)
    if len(summary)!=100 or set(counts.values())!={2}:raise ValueError("Incomplete state/chamber inventory")
    idx={"schema":"power-atlas.state-legislative-geometry.v1",
      "sourceAuthority":"US_Census_Bureau_TIGERweb",
      "year":2024,"statesWithBothChambers":len(counts),
      "stateChamberDownloads":len(summary),
      "districtGeometryFeatures":sum(x["features"] for x in summary),
      "boundaryLegalHistoryComplete":False,
      "warnings":["The 2024 Census geographic baseline is not a complete plan enactment, court decision or effective-date history.",
                  "Some unicameral or unusual jurisdictions may require an explicit source-domain normalization; geometry presence alone is not a legal determination."],
      "records":summary}
    (OUT/"index.json").write_text(json.dumps(idx,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({k:idx[k] for k in ("statesWithBothChambers","districtGeometryFeatures","stateChamberDownloads")},indent=2))
if __name__=="__main__":
    build()
