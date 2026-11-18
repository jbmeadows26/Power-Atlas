#!/usr/bin/env python3
"""Public, bounded adapters. No sensitive networks, private logs, or causal claims.

Each read is an independent observation at one specific geography or endpoint.
A working public status/directory endpoint is not equivalent to a healthy grid,
a reachable submarine cable, working IXP capacity, or valid OCSP/CRL signatures.
"""
from __future__ import annotations

import datetime as dt
import time
import urllib.error
import urllib.request
import urllib.parse

UTC = dt.timezone.utc
GB_FREQUENCY = "https://data.elexon.co.uk/bmrs/api/v1/system/frequency"
PEERINGDB_IX = "https://www.peeringdb.com/api/ix"
GOOGLE_ROOT_CRL = "http://crl.pki.goog/gtsr1/gtsr1.crl"

def stamp():
    return dt.datetime.now(UTC).isoformat().replace("+00:00", "Z")

def parse_utc(value):
    if not isinstance(value,str): return None
    try:
        t=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
        return t.astimezone(UTC) if t.tzinfo is not None else None
    except (ValueError,OverflowError):return None

def grid_from_payload(payload, checked_at):
    """Turn official 1-Hz UK grid readings into one correctly scoped observation."""
    base={
        "id":"elexon-gb-frequency","title":"Great Britain transmission grid frequency",
        "category":"grid_frequency","provider":"elexon",
        "status":"unavailable","checkedAt":checked_at,"source":"Elexon BMRS / National Energy System Operator",
        "sourceUrl":"https://bmrs.elexon.co.uk/rolling-system-frequency",
        "scope":"Great Britain only. Frequency is not UPS availability, load shedding or worldwide grid state.",
        "unit":"Hz","expectedHz":50.0,
    }
    rows=payload.get("data",[]) if isinstance(payload,dict) else []
    if not isinstance(rows,list):return dict(base,detail="Unexpected grid data schema")
    good=[]
    for row in rows[:3000]:
        if not isinstance(row,dict):continue
        t=parse_utc(row.get("measurementTime"))
        v=row.get("frequency")
        if t is None or isinstance(v,bool) or not isinstance(v,(int,float)) or not (45<=v<=55):continue
        good.append((t,float(v)))
    if not good:return dict(base,detail="No valid frequency readings in requested observation interval")
    at,frequency=max(good,key=lambda t:t[0])
    ref=parse_utc(checked_at)
    if ref is None:return dict(base,detail="Invalid collector time")
    age=(ref-at).total_seconds()
    result=dict(base,frequencyHz=round(frequency,4),deviationHz=round(frequency-50.0,4),
        sourceTime=at.isoformat().replace("+00:00","Z"),
        sampleCount=len(good),sampleAgeSeconds=round(age),
        status="observed")
    # Delayed, future or stale reports must never masquerade as current grid health.
    if age < -60 or age > 900:
        result["status"]="stale"
        result["detail"]="Latest official reading is outside 15-minute freshness gate"
    elif abs(frequency-50.0)>=0.5:
        result["status"]="warning"
        result["detail"]="Sample crosses GB statutory 49.5–50.5 Hz bounds. Verify before describing an incident."
    return result

def probe_gb_frequency(read, current=None):
    at=current or stamp()
    start=(parse_utc(at) or dt.datetime.now(UTC))-dt.timedelta(minutes=20)
    # API limit and time range deliberately bounded to 20 minutes.
    url=GB_FREQUENCY+"?"+urllib.parse.urlencode({
        "from":start.isoformat(timespec="seconds").replace("+00:00","Z"),
        "to":at,"format":"json"})
    try:
        return grid_from_payload(read(url,timeout=10),at)
    except Exception as exc:
        return {"id":"elexon-gb-frequency","title":"Great Britain transmission grid frequency",
            "category":"grid_frequency","provider":"elexon","checkedAt":at,"status":"unavailable",
            "source":"Elexon BMRS","sourceUrl":"https://bmrs.elexon.co.uk/rolling-system-frequency",
            "scope":"Great Britain only. No global grid inference.",
            "detail":type(exc).__name__+": "+str(exc)[:110]}

def ixp_from_payload(payload,checked_at):
    """PeeringDB is a DIRECTORY, not utilization telemetry."""
    base={"id":"peeringdb-amsix","title":"AMS-IX published exchange directory",
          "category":"ixp_directory","provider":"peeringdb","status":"unavailable",
          "checkedAt":checked_at,"source":"PeeringDB",
          "sourceUrl":"https://www.peeringdb.com/","scope":"Exchange registry metadata; no live congestion, capacity utilization, packet loss, or outage determination."}
    rows=payload.get("data") if isinstance(payload,dict) else None
    if not isinstance(rows,list):return dict(base,detail="PeeringDB response schema mismatch")
    found=next((r for r in rows if isinstance(r,dict) and str(r.get("name","")).upper()=="AMS-IX"),None)
    if not found:return dict(base,detail="AMS-IX not present in returned directory sample")
    rid=found.get("id")
    if not isinstance(rid,int) or rid<=0:return dict(base,detail="Exchange id missing")
    return dict(base,status="observed",exchange=found.get("name"),exchangeId=rid,
        sourceUrl="https://www.peeringdb.com/ix/"+str(rid))

def probe_ixp_directory(read,current=None):
    at=current or stamp()
    url=PEERINGDB_IX+"?"+urllib.parse.urlencode({"name__contains":"AMS-IX","limit":10})
    try:return ixp_from_payload(read(url,timeout=10),at)
    except Exception as exc:
        return {"id":"peeringdb-amsix","title":"AMS-IX published exchange directory",
                "category":"ixp_directory","provider":"peeringdb","status":"unavailable",
                "checkedAt":at,"source":"PeeringDB","sourceUrl":"https://www.peeringdb.com/",
                "scope":"Registry metadata only, not live traffic.","detail":type(exc).__name__+": "+str(exc)[:110]}

def crl_transport_from_result(status_code,elapsed_ms,checked_at):
    """A HEAD to a named CA CRL endpoint tests reachability, NOT CRL freshness or validity."""
    base={"id":"gts-crl-transport","title":"Google Trust Services CRL transport",
          "category":"pki_transport","provider":"google-trust-services",
          "checkedAt":checked_at,"source":"Google Trust Services",
          "sourceUrl":"https://pki.goog/","scope":
            "HTTP HEAD to a pinned official root CRL distribution point. No OCSP query, signature validation, revocation decision, or CA request-volume monitoring.",
          "requestMethod":"HEAD","httpStatus":status_code,"latencyMs":round(elapsed_ms,1)}
    if isinstance(status_code,int) and 200<=status_code<400:
        base["status"]="observed"
    elif isinstance(status_code,int) and 400<=status_code<500:
        base["status"]="unavailable"
        base["detail"]="Responder rejected HEAD; does not establish a PKI outage."
    else:
        base["status"]="unavailable"
        base["detail"]="CRL transport could not be validated."
    return base

def probe_crl_transport(current=None):
    at=current or stamp()
    start=time.monotonic()
    req=urllib.request.Request(GOOGLE_ROOT_CRL,headers={
        "User-Agent":"EasternAxis-Resilience-Monitor/1.1","Accept":"*/*"},method="HEAD")
    try:
        with urllib.request.urlopen(req,timeout=8) as response:
            code=response.status
    except urllib.error.HTTPError as exc:
        code=exc.code
    except Exception as exc:
        return {"id":"gts-crl-transport","title":"Google Trust Services CRL transport",
            "category":"pki_transport","provider":"google-trust-services",
            "checkedAt":at,"status":"unavailable","source":"Google Trust Services",
            "sourceUrl":"https://pki.goog/",
            "scope":"Single CRL endpoint HEAD; cannot validate revocation.",
            "detail":type(exc).__name__+": "+str(exc)[:100]}
    return crl_transport_from_result(code,(time.monotonic()-start)*1000,at)

def collect_extra(read):
    """Keep each individual failure isolated and visible to the dashboard."""
    return [probe_gb_frequency(read),probe_ixp_directory(read),probe_crl_transport()]
