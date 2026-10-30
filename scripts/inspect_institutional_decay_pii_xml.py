"""Inspect official OECD PII SDMX-XML series attributes, without exporting data."""
import json
import urllib.request
from xml.etree import ElementTree as ET

URL="https://sdmx.oecd.org/public/rest/data/OECD.GOV.PSI,DSD_PII@DF_PUBLIC_INTEGRITY,/GBR+FRA+POL.A..._T.?startPeriod=2022&endPeriod=2025"

def inspect():
    req=urllib.request.Request(URL,headers={
        "Accept":"application/vnd.sdmx.structurespecificdata+xml",
        "User-Agent":"PowerAtlasPublicEvidenceSchemaAudit/1.0"})
    out={"url":URL,"status":"diagnostic_only","series":[],"observations":[],"tagCounts":{}}
    with urllib.request.urlopen(req,timeout=40) as r:
        out["http"]=r.status
        out["contentType"]=r.headers.get("Content-Type","")
        for ev,el in ET.iterparse(r,events=("start",)):
            tag=el.tag.rsplit("}",1)[-1]
            out["tagCounts"][tag]=out["tagCounts"].get(tag,0)+1
            if tag=="Series" and len(out["series"])<4:
                out["series"].append(dict(el.attrib))
            if tag=="Obs" and len(out["observations"])<9:
                out["observations"].append(dict(el.attrib))
            if len(out["series"])>=4 and len(out["observations"])>=9:
                break
    return out

if __name__=="__main__":
    print(json.dumps(inspect(),indent=2))
