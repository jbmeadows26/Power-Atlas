"""Organization-only reference from official OFAC SDN and consolidated XML.
Not compliance clearance; identity must be independently verified.
Public source data only; supplier inputs are never used for retrieval.
"""
import datetime as dt, hashlib, json, re, urllib.request, urllib.error, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
BASE="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/"
SOURCES={"SDN":BASE+"SDN.XML","Consolidated":BASE+"CONSOLIDATED.XML"}
OFFICIAL="https://ofac.treasury.gov/sanctions-list-service"
MAX_BYTES=120*1024*1024
NS="{https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML}"
def get(node,name):
    return (node.findtext(NS+name) or "").strip()
# Observed on both official PublicationPreview XML endpoints. Never accept
# arbitrary Amazon buckets or replay previously issued signed URLs.
PUBLISHED_HOST="wc2h-sls-prod-public-published.s3.us-gov-west-1.amazonaws.com"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
def permitted_redirect(target,filename):
    try:
        u=urllib.parse.urlsplit(target)
        if u.scheme!="https" or u.netloc!=PUBLISHED_HOST or u.fragment or not u.query: return False
        guid=r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}"
        return bool(re.fullmatch(r"/Published/"+guid+r"/\d{4}-\d{2}-\d{2}/"+guid+"/"+re.escape(filename),u.path))
    except ValueError: return False
def read(url):
    if url not in SOURCES.values(): raise ValueError("Unapproved source")
    filename=url.rsplit("/",1)[-1]
    headers={"User-Agent":"Eastern Axis business research pilot/1.0","Accept":"application/xml"}
    opener=urllib.request.build_opener(NoRedirect())
    def download(response):
        with response:
            raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError("Source too large")
        return raw
    try:
        return download(opener.open(urllib.request.Request(url,headers=headers),timeout=70))
    except urllib.error.HTTPError as e:
        code=e.code;target=e.headers.get("Location","");e.close()
        if code not in (301,302,303,307,308): raise ValueError("Official source HTTP "+str(code)) from None
        if not permitted_redirect(target,filename): raise ValueError("Unapproved OFAC publication redirect") from None
    # Only a freshly issued HTTPS URL from the official endpoint, exact observed
    # publication bucket/path and requested filename. No subsequent redirects.
    try:
        return download(opener.open(urllib.request.Request(target,headers=headers),timeout=70))
    except urllib.error.HTTPError as e:
        code=e.code;e.close();raise ValueError("Publication download HTTP "+str(code)) from None
    except (urllib.error.URLError,TimeoutError,ValueError):
        raise ValueError("Publication download unavailable") from None
def parse(raw,kind,now):
    if re.search(br"<!DOCTYPE|<!ENTITY",raw,re.I): raise ValueError("DTD prohibited")
    root=ET.fromstring(raw)
    if root.tag!=NS+"sdnList": raise ValueError("Unexpected XML namespace or root")
    info=root.find(NS+"publshInformation")
    if info is None: raise ValueError("Missing publication information")
    published=dt.datetime.strptime(get(info,"Publish_Date"),"%m/%d/%Y").date()
    if published>now: raise ValueError("Future source date")
    count=int(get(info,"Record_Count"))
    entries=root.findall(NS+"sdnEntry")
    if count!=len(entries) or count<(10000 if kind=="SDN" else 50): raise ValueError("Incomplete record coverage")
    seen=set(); result=[]
    for e in entries:
        uid=get(e,"uid")
        if not re.fullmatch(r"\d{1,12}",uid) or uid in seen: raise ValueError("Invalid or repeated UID")
        seen.add(uid)
        typ=get(e,"sdnType")
        if typ not in ("Entity","Individual","Vessel","Aircraft"): raise ValueError("Unknown entry type")
        if typ!="Entity": continue
        name=get(e,"lastName")
        if not name or len(name)>500: raise ValueError("Missing organization name")
        aliases=[]
        for a in e.findall(NS+"akaList/"+NS+"aka"):
            if get(a,"category").lower()!="strong":continue
            alias=" ".join(x for x in [get(a,"firstName"),get(a,"lastName")] if x)
            if alias and len(alias)<=500 and alias not in aliases and alias!=name: aliases.append(alias)
        programs=[(p.text or "").strip() for p in e.findall(NS+"programList/"+NS+"program")]
        countries=sorted(set(get(a,"country") for a in e.findall(NS+"addressList/"+NS+"address") if get(a,"country")))
        result.append({"uid":uid,"name":name,"aliases":aliases,"programs":programs,"countries":countries})
    if len(result)<(5000 if kind=="SDN" else 10): raise ValueError("Organization coverage too small")
    return {"source":SOURCES[kind],"published":published.isoformat(),"totalEntries":count,"organizationEntries":len(result),"sha256":hashlib.sha256(raw).hexdigest(),"entries":result}
def collect(directory):
    directory.mkdir(parents=True,exist_ok=True)
    checked=dt.datetime.now(dt.timezone.utc)
    data={"schemaVersion":1,"checkedAt":checked.isoformat(),"official":OFFICIAL,"sources":{}}
    for kind,url in SOURCES.items():
        try:
            data["sources"][kind]={"status":"available",**parse(read(url),kind,checked.date())}
        except Exception as e:
            data["sources"][kind]={"status":"unavailable","source":url,"error":type(e).__name__}
            # Public source diagnostics only; no payload, private query, or credentials.
            print(kind, "collection error:", type(e).__name__, str(e)[:180] if type(e) is ValueError else "source request or parsing failed")
        print(kind,data["sources"][kind]["status"],data["sources"][kind].get("organizationEntries"))
    (directory/"ofac-organizations.json").write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    return data
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="site/business-intelligence/data");p.add_argument("--require-available",action="store_true");a=p.parse_args()
    data=collect(Path(a.output));raise SystemExit(1 if a.require_available and any(x["status"]!="available" for x in data["sources"].values()) else 0)
