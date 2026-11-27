"""Build a public, versioned HTS reference index from USITC's dated archive.
No private codes, supplier names, or business data leave the browser.
A failed download produces an explicit unavailable manifest; no invented rates.
"""
import argparse, datetime as dt, hashlib, json, re, urllib.request
from pathlib import Path
SOURCE="https://www.usitc.gov/sites/default/files/tata/hts/hts_2026_revision_23_json.json"
RELEASE="2026 HTS Revision 23"
RELEASE_DATE="2026-11-10"
RELEASE_PAGE="https://www.usitc.gov/2026_hts_revision_23"
CURRENT_PAGE="https://www.usitc.gov/harmonized_tariff_information"
MAX_BYTES=24*1024*1024
def read_url(url,limit):
    req=urllib.request.Request(url,headers={"User-Agent":"Eastern Axis business research pilot/1.0","Accept":"application/json, text/html;q=0.8"})
    with urllib.request.urlopen(req,timeout=45) as r:
        if not r.geturl().startswith("https://www.usitc.gov/"): raise ValueError("Unexpected redirect")
        data=r.read(limit+1)
    if len(data)>limit: raise ValueError("Response exceeds maximum size")
    return data
def index_rows(rows):
    if not isinstance(rows,list): raise ValueError("Expected array")
    out={}
    for row in rows:
        if not isinstance(row,dict): raise ValueError("Invalid tariff row")
        code=row.get("htsno")
        if not isinstance(code,str) or not code.strip(): continue
        if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}(?:\.\d{2})?",code.strip()): continue
        key=code.replace(".","")
        fields={}
        for source,target in [("general","general"),("special","special"),("other","column2")]:
            v=row.get(source)
            if v is not None and not isinstance(v,str): raise ValueError("Invalid rate format")
            if isinstance(v,str) and len(v)>2000: raise ValueError("Rate too long")
            fields[target]=v.strip() if v and v.strip() else None
        fields["footnotesPresent"]=bool(row.get("footnotes"))
        fields["additionalDutiesPresent"]=bool(row.get("additionalDuties") or row.get("addiitionalDuties"))
        if key in out and out[key]!=fields: raise ValueError("Conflicting exact code "+key)
        out[key]=fields
    return out
def manifest(status,checked,**fields):
    return {"schemaVersion":1,"status":status,"checkedAt":checked,"release":RELEASE,"releaseDate":RELEASE_DATE,"source":RELEASE_PAGE,"download":SOURCE,"currentSource":CURRENT_PAGE,**fields}
def collect(directory):
    directory.mkdir(parents=True,exist_ok=True)
    checked=dt.datetime.now(dt.timezone.utc).isoformat()
    for path in directory.glob("hts-*.json"): path.unlink()
    try:
        raw=read_url(SOURCE,MAX_BYTES)
        records=index_rows(json.loads(raw))
        chapters=sorted(set(k[:2] for k in records))
        if len(records)<15000 or len(chapters)<90 or "99" not in chapters:
            raise ValueError("Incomplete archive coverage")
        current="unverified"
        try:
            page=read_url(CURRENT_PAGE,2*1024*1024).decode("utf-8","replace")
            matches=re.findall(r"20\d{2}\s+HTS\s+Revision\s+\d+",page)
            if matches:
                current="matches-listed-revision" if matches[0]==RELEASE else "different-listed-revision"
        except Exception: pass
        for ch in chapters:
            (directory/("hts-"+ch+".json")).write_text(json.dumps({k:v for k,v in records.items() if k.startswith(ch)},separators=(",",":")),encoding="utf-8")
        m=manifest("available",checked,recordCount=len(records),chapters=chapters,sha256=hashlib.sha256(raw).hexdigest(),currentCheck=current)
    except Exception as exc:
        for path in directory.glob("hts-*.json"): path.unlink()
        m=manifest("unavailable",checked,recordCount=None,chapters=[],currentCheck="unverified",error=type(exc).__name__)
    (directory/"hts-manifest.json").write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
    print("HTS reference:",m["status"],m.get("recordCount"),m.get("currentCheck"))
    return m
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",default="site/business-intelligence/data");p.add_argument("--require-available",action="store_true")
    a=p.parse_args();result=collect(Path(a.output));raise SystemExit(1 if a.require_available and result["status"]!="available" else 0)
