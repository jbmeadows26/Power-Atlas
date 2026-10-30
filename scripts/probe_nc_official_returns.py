"""Probe 2024 NCSBE official precinct returns and identify original data schema.

The distinct published NCSBE 'precinct sorted' data contains privacy noise and
MUST NOT be used to reconcile certified vote totals. This script probes only
the official original 2024-11-05 results download linked by NCSBE.
"""
import csv,io,json,zipfile,hashlib,urllib.request,urllib.parse
URL="https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2024_11_05/results_pct_20241105.zip"
PUBLISHER="https://www.ncsbe.gov/results-data/election-results/historical-election-results-data"
def probe():
    req=urllib.request.Request(URL,headers={"User-Agent":"PowerAtlasResearch/1.0 source-only election return inspection"})
    with urllib.request.urlopen(req,timeout=90) as r:
        if urllib.parse.urlsplit(r.geturl()).hostname!="s3.amazonaws.com":raise ValueError("Unexpected NC archive redirect")
        body=r.read(70_000_001)
    if not body.startswith(b"PK") or len(body)>70_000_000:raise ValueError("NC source ZIP missing/oversized")
    results=[]
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        for i in z.infolist():
            result={"file":i.filename,"bytes":i.file_size,"compressed":i.compress_size}
            if i.filename.lower().endswith((".txt",".csv")):
                if i.file_size>400_000_000:raise ValueError("Oversized expanded official return CSV")
                with z.open(i) as src:
                    txt=io.TextIOWrapper(src,encoding="utf-8-sig",errors="replace",newline="")
                    lines=[next(txt,"").rstrip("\r\n")[:300] for _ in range(5)]
                    result["sampleLines"]=lines
                    result["fieldOptions"]=[",".join(lines[:1]).count(",")+1,lines[0].count("\t")+1]
            results.append(result)
    return {"publisher":PUBLISHER,"url":URL,"sha256Zip":hashlib.sha256(body).hexdigest(),
            "archiveBytes":len(body),"members":results,
            "certificationStatus":"downloaded_state_board_precinct_returns_NOT_YET_matched_to_certified_canvass"}
if __name__=="__main__":
    print(json.dumps(probe(),indent=2))
