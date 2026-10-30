"""Bounded alternative OECD SDMX format probe; no implicit data ingestion."""
import json
import urllib.request
import urllib.error

ROOT="https://sdmx.oecd.org/public/rest/data/OECD.GOV.PSI,DSD_PII@DF_PUBLIC_INTEGRITY,"
CANDIDATES=[
    ("sdmx_csv",ROOT+"/GBR.A..._T.?startPeriod=2023&endPeriod=2025","application/vnd.sdmx.csv"),
    ("sdmx_default",ROOT+"/GBR.A..._T.?startPeriod=2023&endPeriod=2025","application/vnd.sdmx.structurespecificdata+xml"),
    ("sdmx_legacy","https://sdmx.oecd.org/public/rest/v1/data/OECD.GOV.PSI,DSD_PII@DF_PUBLIC_INTEGRITY,1.5/GBR.A..._T.?startPeriod=2023&endPeriod=2025","text/csv")
]


def probe():
    attempts=[]
    for name,url,accept in CANDIDATES:
        obj={"candidate":name,"url":url,"accept":accept,"sampleOnly":True}
        try:
            req=urllib.request.Request(url,headers={"Accept":accept,"User-Agent":"PowerAtlasPublicDataAudit/1.0"})
            with urllib.request.urlopen(req,timeout=15) as r:
                sample=r.read(20000).decode("utf-8-sig",errors="replace")
                obj.update(status="response_unverified",http=r.status,
                           contentType=r.headers.get("Content-Type",""),
                           sampleBytes=len(sample),sampleStart=sample[:180],
                           hasREF_AREA="REF_AREA" in sample)
        except urllib.error.HTTPError as e:
            obj.update(status="http_error",http=e.code,reason=str(e.reason))
        except Exception as e:
            obj.update(status="unreachable",reason=type(e).__name__+": "+str(e)[:150])
        attempts.append(obj)
        if obj["status"]=="response_unverified":
            break
    return {"source":"OECD Public Integrity Indicators","status":"diagnostic_only",
            "completePanelValidated":False,"attempts":attempts}


if __name__=="__main__":
    print(json.dumps(probe(),indent=2))
