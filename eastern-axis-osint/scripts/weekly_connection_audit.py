#!/usr/bin/env python3
"""Weekly Eastern Axis public-feed and API audit. GET/HEAD only; standard library."""
import concurrent.futures as cf
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

BASE=(os.environ.get("EASTERN_AXIS_URL") or pathlib.Path("eastern-axis/public-api-origin.txt").read_text(encoding="utf-8").strip()).rstrip("/")
PAGES="https://jbmeadows26.github.io/Power-Atlas/eastern-axis/"
if not BASE.startswith("https://") or not BASE.endswith(".neon.tech"):
    raise ValueError("Weekly audit requires the configured public Neon API, not the legacy Vercel frontend")
OUT=pathlib.Path(os.environ.get("AUDIT_OUTPUT_DIR","audit-output"))
OUT.mkdir(parents=True,exist_ok=True)
NOW=dt.datetime.now(dt.timezone.utc)
CHECKS=[]
DOC={}
ROUTES=[
"/api/_healthcheck","/api/overview",
"/api/brief/RU","/api/factbook/countries","/api/factbook/RU",
"/api/factbook/compare?codes=RU,CN",
"/api/global-systems/RU","/api/global-systems/WLD",
"/api/energy-supply/RU","/api/allied-sanctions/RU",
"/api/defense-intel","/api/source-monitor","/api/evidence-workbench",
"/api/intelligence","/api/world-signals","/api/supply-chain/RU",
"/api/supply-macro"
]
SOURCES={
"UK FCDO":"https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv",
"Canada sanctions":"https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/sema-lmes.xml",
"OWID energy":"https://catalog.ourworldindata.org/energy/owid_energy/owid_energy.csv",
"OFAC":"https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV",
"DOJ":"https://www.justice.gov/api/v1/press_releases.json?pagesize=2",
"FARA":"https://efile.fara.gov/api/v1/Registrants/json/Active",
"CISA KEV":"https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
"World Bank":"https://api.worldbank.org/v2/country/RU/indicator/NY.GDP.MKTP.CD?format=json&mrv=1&per_page=5",
"USGS":"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson",
"NASA EONET":"https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=14&limit=5",
"US defense RSS":"https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945",
"UK MOD":"https://www.gov.uk/government/organisations/ministry-of-defence.atom",
"UN security":"https://news.un.org/feed/subscribe/en/news/topic/peace-and-security/feed/rss.xml",
"IMF PortWatch":"https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=1%3D1&outFields=date%2Cportname%2Cn_total&resultRecordCount=1&returnGeometry=false&f=json"
}
JSON_SOURCES={"DOJ","FARA","CISA KEV","World Bank","USGS","NASA EONET","IMF PortWatch"}

def get(url,method="GET",limit=5000000,timeout=20):
    headers={"User-Agent":"EasternAxis-Weekly-Audit/1.0 (GitHub Actions; public data research)",
             "Accept":"application/json, text/csv, application/xml, */*",
             "Accept-Encoding":"identity"}
    if url.startswith(BASE+"/api/") or url.startswith(BASE+"/_neon/"):
        headers["Origin"]="https://jbmeadows26.github.io"
    request=urllib.request.Request(url,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=timeout) as r:
            return r.status,r.read(limit) if method=="GET" else b"",r.geturl()
    except urllib.error.HTTPError as ex:
        return ex.code,b"",ex.geturl()

def add(kind,name,state,detail,url):
    CHECKS.append({"kind":str(kind),"name":str(name),"result":str(state),
                   "detail":str(detail)[:340],"url":str(url)})

def age(value):
    if not isinstance(value,str) or not value:return None
    try:
        d=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=dt.timezone.utc)
        return round((NOW-d).total_seconds()/86400,1)
    except ValueError:return None

def freshness(name,stamp,path,max_days=8):
    days=age(stamp)
    state="PASS" if days is not None and days<=max_days else "WARN"
    add("Freshness",name,state,"last success "+str(days)+" days ago" if days is not None else
        "No verifiable last-success timestamp",BASE+path)

def request_api(route):
    url=BASE+route
    try:
        for attempt in range(2):
            status,body,_=get(url)
            if status in (429,500,502,503,504) and attempt==0:
                time.sleep(2)
                continue
            break
        if status!=200:
            add("API",route,"FAIL","HTTP "+str(status),url);return
        try:DOC[route]=json.loads(body)
        except (UnicodeError,ValueError):
            add("API",route,"FAIL","Invalid or truncated JSON",url);return
        add("API",route,"PASS","HTTP 200; valid JSON",url)
    except Exception as exc:add("API",route,"FAIL",type(exc).__name__,url)

def inspect_data():
    overview=DOC.get("/api/overview") or {}
    if isinstance(overview,dict):
        catalog=overview.get("sources") or []
        add("Data","Source catalog","PASS" if len(catalog)>=30 else "WARN",
            str(len(catalog))+" entries; many reference-only, not ingested",BASE+"/api/overview")
        snapshot=overview.get("snapshot")
        if snapshot is None:
            add("Data","Scheduled World Bank snapshot","WARN",
                "Missing stored snapshot; on-demand country metrics may still work",BASE+"/api/overview")
        else:freshness("Scheduled World Bank",snapshot.get("updatedAt"),"/api/overview",10)
    for code in ("RU","ALL"):
        path="/api/energy-supply/"+code
        d=DOC.get(path)
        if not isinstance(d,dict):continue
        target="reported" if code=="RU" else "global-coverage"
        ok=d.get("status")==target and (d.get("countryCount") or 0)>=160
        add("Data","OWID energy "+code,"PASS" if ok else "WARN",
            "status="+str(d.get("status"))+" countries="+str(d.get("countryCount")),BASE+path)
        freshness("OWID energy "+code,d.get("checkedAt"),path,10)
    d=DOC.get("/api/intelligence")
    if isinstance(d,dict):
        for source in d.get("sources",[]):
            h=source.get("health") or {}
            status=h.get("status")
            name=source.get("id","unknown")
            add("Data","Collector "+name,"PASS" if status=="ok" else "FAIL" if status=="error" else "WARN",
                "status="+str(status)+" error="+str(h.get("lastError") or "")[:80],
                BASE+"/api/intelligence")
            freshness("Collector "+name,h.get("lastSuccessAt"),"/api/intelligence")
        fara=d.get("faraSnapshot") or {}
        if fara:
            valid=(fara.get("indexed") or 0)>=300 and fara.get("indexed")==fara.get("total")
            add("Data","FARA registrations","PASS" if valid else "WARN",
                str(fara.get("indexed"))+" of "+str(fara.get("total")),BASE+"/api/intelligence")
            freshness("FARA snapshot",fara.get("retrievedAt"),"/api/intelligence")
    d=DOC.get("/api/allied-sanctions/ALL")
    if isinstance(d,dict):
        for source in d.get("sources",[]):
            status=source.get("status")
            name=source.get("name") or source.get("id") or "unknown"
            add("Data","Sanctions "+name,"PASS" if status=="snapshot" else "WARN",
                "status="+str(status),BASE+"/api/allied-sanctions/ALL")
            freshness("Sanctions "+name,source.get("checkedAt"),"/api/allied-sanctions/ALL",10)
    d=DOC.get("/api/source-monitor")
    if isinstance(d,dict):
        for source in d.get("feeds",[]):
            h=source.get("health") or {}
            state=h.get("status")
            name=source.get("id","unknown")
            add("Data","Gov monitor "+name,"PASS" if state=="ok" else "WARN",
                "status="+str(state),BASE+"/api/source-monitor")
            freshness("Gov monitor "+name,h.get("lastSuccessAt"),"/api/source-monitor")
    d=DOC.get("/api/world-signals")
    if isinstance(d,dict):
        for source in ("usgs","nasa"):
            state=d.get(source+"Status")
            add("Data",source.upper()+" hazards","PASS" if state=="ok" else "WARN",
                "status="+str(state)+" error="+str(d.get(source+"Error")),BASE+"/api/world-signals")
    for code in ("ALL","RU","IR"):
        path="/api/supply-chain/"+code
        d=DOC.get(path)
        if isinstance(d,dict):
            state=d.get("sourceStatus")
            add("Data","PortWatch "+code,"PASS" if state=="observed" else "WARN",
                "status="+str(state)+" sourceDate="+str(d.get("sourceDate"))+
                " corridors="+str(len(d.get("corridors") or [])),BASE+path)
    for code in ("RU","WLD"):
        path="/api/global-systems/"+code
        d=DOC.get(path)
        if isinstance(d,dict):
            fields=d.get("indicators") or d.get("observations") or []
            count=sum(isinstance(x,dict) and x.get("value") is not None for x in fields)
            add("Data","World Bank indicators "+code,"PASS" if count>=10 else "WARN",
                str(count)+" observed of "+str(len(fields)),BASE+path)
    d=DOC.get("/api/evidence-workbench")
    if isinstance(d,dict):
        m=d.get("metrics") or {}
        if isinstance(m,dict) and not (m.get("immutableArchives") or m.get("immutableArchivesCount")):
            add("Data","Immutable evidence","WARN","No verified immutable archive count",
                BASE+"/api/evidence-workbench")

def probe_link(item):
    name=item.get("id") or item.get("name") or "unknown"
    url=item.get("url") or ""
    mode=str(item.get("mode","")).lower()
    kind="reference-only" if any(x in mode for x in
        ("linked","reference","directory","not ingested","not yet ingested","tool")) else "on-demand/scheduled"
    if not isinstance(url,str) or not url.startswith("https://"):
        return ("Link",name,"FAIL","Missing or non-HTTPS URL ("+kind+")",str(url))
    try:
        code,_,final=get(url,method="HEAD",timeout=12)
        if code in (403,404,405,429):code,_,final=get(url,limit=4096,timeout=12)
        status="PASS" if 200<=code<400 else "WARN" if code in (401,403,429,500,502,503,504) else "FAIL"
        return ("Link",name,status,"HTTP "+str(code)+"; "+kind+
                "; final host="+urllib.parse.urlparse(final).netloc,url)
    except Exception as e:
        return ("Link",name,"WARN","Inconclusive "+type(e).__name__+"; "+kind,url)

def probe_upstream(pair):
    name,url=pair
    try:
        code,body,final=get(url,limit=12000,timeout=18)
        status="PASS" if code in (200,206) and body else "WARN" if code in (401,403,429,500,502,503,504) else "FAIL"
        if status=="PASS" and name in JSON_SOURCES and not body.lstrip(b"\xef\xbb\xbf \t\n\r").startswith((b"{",b"[")):
            status="WARN"
        return ("Upstream",name,status,"HTTP "+str(code)+" sampled="+str(len(body))+
                " bytes final="+urllib.parse.urlparse(final).netloc,url)
    except Exception as e:return ("Upstream",name,"WARN","Inconclusive "+type(e).__name__,url)

def main():
    try:
        code,body,_=get(PAGES,limit=30000)
        add("UI","Dashboard root","PASS" if code==200 and b"<html" in body.lower() else "FAIL",
            "HTTP "+str(code)+"; interactive checks are separate",PAGES)
    except Exception as e:add("UI","Dashboard root","FAIL",type(e).__name__,PAGES)
    with cf.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(request_api,ROUTES))
    for route,expected in (("/api/cron/doj",401),("/api/does-not-exist",404)):
        try:
            code,_,_=get(BASE+route,limit=2000)
            add("Security",route,"PASS" if code==expected else "FAIL",
                "HTTP "+str(code)+" expected "+str(expected)+"; cron not triggered",BASE+route)
        except Exception as e:add("Security",route,"FAIL",type(e).__name__,BASE+route)
    inspect_data()
    sources=(DOC.get("/api/overview") or {}).get("sources",[])
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(probe_link,x) for x in sources if isinstance(x,dict)]
        futures += [pool.submit(probe_upstream,x) for x in SOURCES.items()]
        for f in cf.as_completed(futures):
            try:add(*f.result())
            except Exception as e:add("Audit","Probe","WARN",type(e).__name__,"")
    CHECKS.sort(key=lambda x:(x["kind"],x["name"]))
    counts=Counter(x["result"] for x in CHECKS)
    (OUT/"connections.json").write_text(json.dumps(
        {"checkedAt":NOW.isoformat(),"base":BASE,"counts":dict(counts),"checks":CHECKS},
        indent=2,ensure_ascii=False)+"\n")
    lines=["# Eastern Axis weekly connections audit","",
        "**Checked:** "+NOW.strftime("%Y-%m-%d %H:%M UTC")+"  ",
        "**Public site:** "+PAGES+"  ",
        "**API origin:** "+BASE+"  ",
        "**Summary:** "+str(counts["PASS"])+" PASS · "+str(counts["WARN"])+" WARN · "+str(counts["FAIL"])+" FAIL","",
        "A successful HTTP response is not proof of fresh data. Reference-only source URLs are not ingested feeds. "
        "403/429 may indicate bot protection. Protected ingestion crons are never triggered in this read-only audit.","",
        "| Category | Source/check | Status | Evidence |","|---|---|---|---|"]
    for x in CHECKS:
        name=x["name"].replace("|","\\|")
        link="["+name+"]("+x["url"]+")" if x["url"].startswith("https://") else name
        lines.append("| "+x["kind"]+" | "+link+" | "+x["result"]+" | "+
                     x["detail"].replace("|","\\|").replace("\n"," ")+" |")
    (OUT/"connections.md").write_text("\n".join(lines)+"\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as s:
            s.write("\n".join(lines[:10])+"\n\n")
            for x in CHECKS:
                if x["result"]!="PASS":s.write("- **"+x["result"]+"** "+x["name"]+": "+x["detail"]+"\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as out:
            out.write("fail_count="+str(counts["FAIL"])+"\n")
            out.write("warn_count="+str(counts["WARN"])+"\n")
    print("Audit counts",dict(counts))
    return 1 if counts["FAIL"] else 0
if __name__=="__main__":sys.exit(main())
