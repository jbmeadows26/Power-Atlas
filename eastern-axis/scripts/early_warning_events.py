"""Keyless official-source event leads. Leads are NOT automatically attributed threats.
Every record is source dated, geographically scoped and bounded in size.
"""
from __future__ import annotations
from datetime import datetime,timezone,date
import json
import math
import re
from urllib.parse import urlparse

USGS="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"
CISA="https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
SWPC="https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
NWS=("https://api.weather.gov/alerts/active",)
CISA_PAGE="https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
SWPC_PAGE="https://www.swpc.noaa.gov/products/planetary-k-index"

def day(value):
    try:return date.fromisoformat(str(value)[:10]).isoformat()
    except (ValueError,TypeError):return None

def safe_url(value,host):
    if not isinstance(value,str):return None
    parsed=urlparse(value)
    if parsed.scheme!="https" or parsed.hostname!=host or parsed.username or parsed.password:return None
    return value

def read_usgs(raw):
    data=json.loads(raw)
    if data.get("type")!="FeatureCollection" or not isinstance(data.get("features"),list):raise ValueError("Invalid USGS feed")
    events=[]
    for row in data["features"][:60]:
        if not isinstance(row,dict):continue
        p=row.get("properties")
        if not isinstance(p,dict):continue
        url=safe_url(p.get("url"),"earthquake.usgs.gov")
        magnitude=p.get("mag")
        stamp=p.get("time")
        if not url or not isinstance(magnitude,(float,int)) or not isinstance(stamp,(float,int)):continue
        if not math.isfinite(float(magnitude)) or not 0<=magnitude<=10:continue
        try:
            observed=datetime.fromtimestamp(stamp/1000,timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
        except (OSError,OverflowError,ValueError):continue
        if not day(observed):continue
        title=str(p.get("title") or "Significant earthquake")[:160]
        events.append({"id":"usgs-"+str(row.get("id") or observed)[:90],
                       "title":title,"observedAt":observed,"group":"global",
                       "severity":"Observed","sourceUrl":url,"officialAlert":False,
                       "note":"USGS earthquake observation; not evidence of a deliberate act."})
    return {"id":"usgs-significant","publisher":"USGS Earthquake Hazards Program",
            "sourceUrl":USGS,"scope":"Worldwide; significant earthquakes in a rolling seven-day feed",
            "events":events}

def read_kev(raw):
    data=json.loads(raw)
    rows=data.get("vulnerabilities")
    if not isinstance(rows,list) or not isinstance(data.get("catalogVersion"),str):raise ValueError("Invalid CISA KEV catalog")
    ordered=sorted((r for r in rows if isinstance(r,dict) and day(r.get("dateAdded"))),key=lambda r:r["dateAdded"],reverse=True)
    events=[]
    for r in ordered[:15]:
        cve=str(r.get("cveID",""))
        if not re.fullmatch(r"CVE-\d{4}-\d{4,}",cve):continue
        title=(str(r.get("vendorProject",""))+" "+str(r.get("product",""))+" — "+cve).strip()[:180]
        events.append({"id":"cisa-kev-"+cve,"title":title,"observedAt":r["dateAdded"],
                       "group":"global","severity":"Known exploited vulnerability",
                       "sourceUrl":CISA_PAGE,"officialAlert":False,
                       "note":"CISA KEV listing confirms exploitation in the wild, not a breach of a particular organization."})
    return {"id":"cisa-kev","publisher":"CISA Known Exploited Vulnerabilities",
            "sourceUrl":CISA_PAGE,"scope":"Worldwide vulnerability context, not country incident attribution",
            "events":events}

def read_swpc(raw):
    rows=json.loads(raw)
    if not isinstance(rows,list) or not rows:raise ValueError("Invalid SWPC Kp JSON")
    # NOAA currently publishes JSON objects; accept the older header-row form too.
    if isinstance(rows[0],dict):
        points=[(str(row.get("time_tag","")),row.get("Kp"))
                for row in rows if isinstance(row,dict)]
    elif isinstance(rows[0],list):
        header=[str(x).lower().strip() for x in rows[0]]
        dt=next((i for i,h in enumerate(header) if h in ("time_tag","time_tag_iso","time")),None)
        kp=next((i for i,h in enumerate(header) if h in ("kp","estimated_kp","k-index")),None)
        if dt is None or kp is None:raise ValueError("SWPC observation columns missing")
        points=[(str(row[dt]),row[kp]) for row in rows[1:]
                if isinstance(row,list) and max(dt,kp)<len(row)]
    else:raise ValueError("SWPC unknown row schema")
    good=[]
    for stamp,raw_value in points:
        if not day(stamp):continue
        try:
            val=float(raw_value)
            if math.isfinite(val) and 0<=val<=9:good.append((stamp,val))
        except (ValueError,TypeError):continue
    if not good:raise ValueError("No dated SWPC Kp observations")
    stamp,val=max(good,key=lambda x:x[0])
    event={"id":"noaa-kp-"+stamp[:16].replace(" ","T"),"title":"Observed planetary geomagnetic Kp "+str(round(val,2)),
           "observedAt":stamp,"group":"global","severity":"Observed",
           "sourceUrl":SWPC_PAGE,"officialAlert":False,
           "note":"Observed Kp index, not a specific grid outage or predicted disruption."}
    return {"id":"noaa-space-weather","publisher":"NOAA Space Weather Prediction Center",
            "sourceUrl":SWPC_PAGE,"scope":"Planetary Kp observations; not localized outage evidence",
            "events":[event]}

def read_nws(raw):
    data=json.loads(raw)
    if data.get("type")!="FeatureCollection" or not isinstance(data.get("features"),list):raise ValueError("Invalid NWS GeoJSON")
    events=[]
    for row in data["features"][:100]:
        if not isinstance(row,dict) or not isinstance(row.get("properties"),dict):continue
        p=row["properties"]
        severity=p.get("severity")
        if severity not in ("Extreme","Severe"):continue
        if p.get("status") not in ("Actual",None):continue
        observed=p.get("effective") or p.get("sent")
        if not day(observed):continue
        expiry=p.get("expires") or p.get("ends")
        if not expiry:continue
        try:
            if datetime.fromisoformat(str(expiry).replace("Z","+00:00"))<=datetime.now(timezone.utc):continue
        except ValueError:continue
        alert_id=safe_url(p.get("@id") or p.get("id") or row.get("id"),"api.weather.gov")
        if not alert_id:continue
        kind=str(p.get("event") or "NWS warning")[:95]
        area=str(p.get("areaDesc") or "U.S. region")[:100]
        events.append({"id":"nws-"+re.sub(r"[^a-zA-Z0-9-]","-",alert_id.rsplit("/",1)[-1])[:88],
                       "title":kind+" — "+area,"observedAt":observed,"group":"US",
                       "severity":severity,"sourceUrl":alert_id,"officialAlert":True,
                       "expiresAt":expiry,
                       "note":"Active NWS advisory with local area, expiry and direct official record; not global coverage."})
    return {"id":"nws-severe","publisher":"NOAA National Weather Service",
            "sourceUrl":"https://www.weather.gov/documentation/services-web-alerts",
            "scope":"U.S. active severe/extreme advisories; bounded first 100 per severity; not complete coverage",
            "events":events}
