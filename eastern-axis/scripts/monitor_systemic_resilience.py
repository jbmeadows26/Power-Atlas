#!/usr/bin/env python3
"""Bounded, source-attributed public early-warning collection for Eastern Axis.

No vendor status page is considered independent proof of health. Public HTTP/TLS
checks do not authenticate users, validate OCSP signatures, read private agent logs,
or see submarine fiber DAS or internal control-plane state.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from pathlib import Path
import socket
import ssl
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "telemetry" / "resilience.json"
UTC = dt.timezone.utc
USER_AGENT = "EasternAxis-Resilience-Monitor/1.0 (public low-volume research)"
PROBES = [
    ("microsoft-identity", "login.microsoftonline.com", "Microsoft Entra public entry"),
    ("google-identity", "accounts.google.com", "Google account public entry"),
    ("cloudflare-edge", "www.cloudflare.com", "Cloudflare public edge"),
    ("github-web", "github.com", "GitHub public web"),
]
ROUTES = [
    ("cloudflare", "1.1.1.0/24", "AS13335"),
    ("google", "8.8.8.0/24", "AS15169"),
]
REGIONS = ("US", "DE", "SG")
METRICS = {
    "automation_remediations_per_hour": ("AIOps policy churn", "automation", "events/hour"),
    "metadata_propagation_ms": ("Cross-region metadata lag", "control-plane", "ms"),
    "deployment_events_per_hour": ("Deployment velocity", "deployment", "events/hour"),
    "post_deploy_check_failures": ("Post-deploy verification failures", "deployment", "count"),
    "quota_utilization_pct": ("API quota utilization", "capacity", "%"),
    "cdn_ruleset_utilization_pct": ("CDN ruleset capacity", "capacity", "%"),
    "ixp_utilization_pct": ("IXP interface load", "routing", "%"),
    "grid_frequency_hz": ("Grid frequency", "physical", "Hz"),
    "ups_transfer_failures": ("UPS / transfer-switch failures", "physical", "count"),
    "edr_buffer_age_seconds": ("Out-of-band EDR buffer age", "endpoint", "seconds"),
    "trace_error_rate_pct": ("Distributed trace error rate", "tracing", "%"),
    "ocsp_p95_ms": ("OCSP responder latency", "pki", "ms"),
    "crl_p95_ms": ("CRL retrieval latency", "pki", "ms"),
    "das_acoustic_alerts": ("Operator DAS alarms", "physical", "count"),
}
CAPABILITIES = [
    ("regional_http", "Regional unauthenticated HTTP probes", "Globalping community probes", "public"),
    ("dns_tls", "DNS, TLS handshake and certificate expiry", "Independent GitHub runner", "public"),
    ("bgp_rpki", "Sampled BGP and RPKI", "RIPE RIS / RIPEstat", "public"),
    ("traffic", "Regional internet traffic anomalies", "Cloudflare Radar API", "optional-token"),
    ("transactions", "Authenticated client-side MAPI/EAS, mail and calendar", "Authorized synthetic tenant", "operator"),
    ("dependencies", "Nth-party hosting and identity dependency graph", "Verified ownership / vendor contracts", "operator"),
    ("aiops", "Autonomous remediation loops and circuit breakers", "Authorized controller logs", "operator"),
    ("power", "Grid frequency, UPS and transfer telemetry", "Regional grid / facility telemetry", "operator"),
    ("cables", "Submarine faults, DAS acoustic strain and fiber telemetry", "Cable-operator feeds / verified advisories", "operator"),
    ("ixp", "IXP congestion and multi-homed validation", "IXP / router operator data", "operator"),
    ("melt", "Cross-region distributed traces and exception sequences", "Authorized OpenTelemetry exporters", "operator"),
    ("deploy", "Deployment velocity and post-deployment checks", "Authorized CI/CD logs", "operator"),
    ("state", "Control-plane metadata race and propagation lag", "Authorized regional state checks", "operator"),
    ("quotas", "API limits and CDN ruleset size", "Authorized provider quotas", "operator"),
    ("endpoint", "Out-of-band endpoint security event buffering", "Authorized endpoint agents", "operator"),
    ("pki", "OCSP / CRL latency and revocation storm volume", "PKI operators / approved monitors", "operator"),
    ("threat", "Threat-actor claims / underground corroboration", "Lawfully obtained verified intelligence", "analyst"),
]
METRIC_TO_CAP = {
    "automation_remediations_per_hour":"aiops", "metadata_propagation_ms":"state",
    "deployment_events_per_hour":"deploy","post_deploy_check_failures":"deploy",
    "quota_utilization_pct":"quotas","cdn_ruleset_utilization_pct":"quotas",
    "ixp_utilization_pct":"ixp","grid_frequency_hz":"power",
    "ups_transfer_failures":"power","edr_buffer_age_seconds":"endpoint",
    "trace_error_rate_pct":"melt","ocsp_p95_ms":"pki",
    "crl_p95_ms":"pki","das_acoustic_alerts":"cables"
}

def now():
    return dt.datetime.now(UTC).isoformat().replace("+00:00", "Z")

def json_http(url, payload=None, headers=None, timeout=9):
    data = json.dumps(payload).encode() if payload is not None else None
    hd = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if data is not None: hd["Content-Type"] = "application/json"
    hd.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hd, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(2_000_001)
        if len(raw) > 2_000_000: raise ValueError("Response exceeded 2 MB bound")
        return json.loads(raw)

def tls_probe(probe_id, host, title):
    started = time.monotonic()
    entry = {"id":probe_id, "title":title,"category":"dns_tls","provider":probe_id.split("-")[0],
             "source":"Independent GitHub Actions runner", "sourceUrl":"https://docs.github.com/en/actions",
             "checkedAt":now(), "status":"unavailable","scope":"one GitHub-hosted runner, not worldwide"}
    try:
        socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        entry["dnsMs"]=round((time.monotonic()-started)*1000,1)
        started_tls=time.monotonic()
        context=ssl.create_default_context()
        with socket.create_connection((host,443),timeout=6) as raw:
            raw.settimeout(6)
            with context.wrap_socket(raw,server_hostname=host) as conn:
                cert=conn.getpeercert()
                entry["handshakeMs"]=round((time.monotonic()-started_tls)*1000,1)
                expiry=cert.get("notAfter")
                if expiry:
                    expired=dt.datetime.strptime(expiry,"%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
                    entry["certDaysRemaining"]=round((expired-dt.datetime.now(UTC)).total_seconds()/86400,1)
        entry["status"]="observed"
        if entry.get("certDaysRemaining",999) < 7: entry["status"]="warning"
    except Exception as exc:
        entry["status"]="error"
        entry["detail"]=type(exc).__name__ + ": " + str(exc)[:120]
    return entry

def region_probe(host, provider):
    """Unauthenticated external probe; non-2xx login-page responses may be expected."""
    base={"id":"globalping-"+provider,"category":"regional_http","provider":provider,
          "title":host + " external HTTP reachability", "source":"Globalping community probes",
          "sourceUrl":"https://globalping.io/","checkedAt":now(),
          "scope":"Unauthenticated HEAD across US, DE and SG; not login / MAPI / EAS success",
          "status":"unavailable","regions":[]}
    try:
        job=json_http("https://api.globalping.io/v1/measurements",
          {"type":"http","target":host,
           "locations":[{"country":r,"limit":1} for r in REGIONS],
           "measurementOptions":{"request":{"method":"HEAD"}}},timeout=9)
        job_id=job.get("id")
        if not isinstance(job_id,str) or not job_id.isalnum(): raise ValueError("No valid probe id")
        for attempt in range(5):
            data=json_http("https://api.globalping.io/v1/measurements/"+job_id,timeout=8)
            if data.get("status")!="in-progress": break
            if attempt<4: time.sleep(1.5)
        if data.get("status")!="finished": raise ValueError("External measurement not finished")
        for item in data.get("results",[])[:6]:
            probe=item.get("probe",{}) or {}
            result=item.get("result",{}) or {}
            if not isinstance(result,dict): continue
            code=result.get("statusCode")
            timing=result.get("timings",{}) or {}
            rstatus=result.get("status")
            # 401/403/405 can mean the endpoint exists but denies a HEAD request.
            state="reachable" if isinstance(code,int) and 200<=code<500 else (
                "failure" if isinstance(code,int) and code>=500 else "unknown")
            base["regions"].append({"country":str(probe.get("country",""))[:2],
                "asn":probe.get("asn"),"httpStatus":code if isinstance(code,int) else None,
                "latencyMs":timing.get("total") if isinstance(timing,dict) else None,
                "state":state, "probeStatus":rstatus})
        if base["regions"]:
            base["status"]="warning" if sum(r["state"]=="failure" for r in base["regions"])>=2 else "observed"
            base["failedRegions"]=sum(r["state"]=="failure" for r in base["regions"])
        else: base["detail"]="No probe results returned"
    except Exception as exc:
        base["detail"]=type(exc).__name__+": "+str(exc)[:120]
    return base

def route_probe(label, prefix, origin):
    base={"id":"ripe-"+label, "title":label+" BGP/RPKI sample","category":"bgp_rpki",
          "provider":label,"checkedAt":now(),"source":"RIPE RIS / RIPEstat",
          "sourceUrl":"https://stat.ripe.net/","scope":"One selected IP prefix; not global IXP utilization",
          "prefix":prefix,"expectedOrigin":origin,"status":"unavailable"}
    url="https://stat.ripe.net/data/rpki-validation/data.json?"+urllib.parse.urlencode(
        {"resource":origin,"prefix":prefix,"sourceapp":"eastern-axis"})
    try:
        obj=json_http(url,timeout=9)
        if obj.get("status")!="ok" and obj.get("data_call_status")!="supported":
            raise ValueError("RIPE data call not successful")
        value=(obj.get("data") or {}).get("status")
        if isinstance(value,str) and value.lower() in ("valid","invalid_asn","invalid_length","unknown"):
            base["rpkiState"]=value.lower()
            base["status"]="warning" if value.lower().startswith("invalid") else "observed"
        else: raise ValueError("Unexpected RPKI status")
        try:
            activity_url="https://stat.ripe.net/data/bgp-update-activity/data.json?"+urllib.parse.urlencode(
                {"resource":prefix,"num_hours":1,"max_samples":12,"sourceapp":"eastern-axis"})
            activity=json_http(activity_url,timeout=9)
            records=(activity.get("data") or {}).get("updates",[])
            if isinstance(records,list):
                # Counts reflect observations at RIPE route collectors, not internet-wide events.
                base["bgpUpdateCount"]=sum(int(sample.get("announcements") or 0)+int(sample.get("withdrawals") or 0)
                    for sample in records if isinstance(sample,dict))
                base["bgpWindowHours"]=1
        except Exception:
            base["bgpActivityStatus"]="unavailable"
    except Exception as exc:
        base["detail"]=type(exc).__name__+": "+str(exc)[:120]
    return base

def radar_probe():
    result={"id":"radar-traffic","title":"Cloudflare Radar latest traffic anomalies",
            "category":"traffic","provider":"cloudflare","status":"not_configured",
            "source":"Cloudflare Radar","sourceUrl":"https://radar.cloudflare.com/",
            "checkedAt":now(),"scope":"Radar observational coverage, not global exhaustive coverage"}
    token=os.environ.get("CLOUDFLARE_API_TOKEN","").strip()
    if not token: return result
    try:
        obj=json_http("https://api.cloudflare.com/client/v4/radar/traffic_anomalies",
          headers={"Authorization":"Bearer "+token},timeout=9)
        if obj.get("success") is not True: raise ValueError("Radar API unsuccessful")
        data=(obj.get("result") or {}).get("trafficAnomalies")
        if not isinstance(data,list): raise ValueError("Radar anomalies schema changed")
        result["status"]="observed"
        result["reportedAnomalies"]=len(data)
        result["note"]="Traffic anomalies require source confirmation; number is not an attack count."
    except Exception as exc:
        result["status"]="unavailable"
        result["detail"]=type(exc).__name__+": "+str(exc)[:120]
    return result

def private_operator_metrics():
    """Optional aggregated authorized metrics from an Actions secret, never raw logs."""
    raw=os.environ.get("RESILIENCE_METRICS_JSON","")
    if not raw.strip(): return []
    try:
        rows=json.loads(raw)
        if not isinstance(rows,list): return []
        result=[]
        for item in rows[:30]:
            if not isinstance(item,dict):continue
            k=item.get("metric")
            if k not in METRICS:continue
            value=item.get("value")
            if isinstance(value,bool) or not isinstance(value,(int,float)) or abs(value)>1e12:continue
            when=item.get("observedAt")
            try:
                age=(dt.datetime.now(UTC)-dt.datetime.fromisoformat(when.replace("Z","+00:00"))).total_seconds()
                if not 0<=age<=3600:continue
            except (ValueError,AttributeError,TypeError):continue
            name,kind,unit=METRICS[k]
            result.append({"id":"operator-"+k,"title":name,"category":kind,
                "source":"Authorized operator aggregate","sourceUrl":None,
                "checkedAt":when,"metric":k,"unit":unit,"value":value,
                "scope":str(item.get("scope","Unspecified authorized scope"))[:100],
                "status":"observed","provider":"operator",
                "note":"Not a public-global measurement. Authorized aggregate, not independently verified."})
        return result
    except (ValueError,TypeError):return []

def correlate(observations):
    """Do not infer attack or systemic outage from individual errors."""
    by_provider={}
    for o in observations:
        if o.get("category")!="regional_http":continue
        if o.get("status")=="warning" and o.get("failedRegions",0)>=2:
            by_provider[o.get("provider")]=o
    sources=sorted(by_provider)
    incidents=[]
    if len(sources)>=2:
        incidents.append({"id":"multi-provider-http", "severity":"watch",
            "title":"Multi-provider regional HTTP failures",
            "evidenceIds":[by_provider[k]["id"] for k in sources],
            "explanation":"Two independent provider endpoints each returned server errors in at least two sampled regions. Investigate shared dependencies, but root cause and malicious intent are unknown.",
            "confidence":"screening-only"})
    return incidents

def build_snapshot(observations, previous=None, when=None):
    previous=previous if isinstance(previous,dict) else {}
    history=[i for i in previous.get("history",[]) if isinstance(i,dict)][-47:]
    incidents=correlate(observations)
    used_caps={"regional_http":any(o.get("category")=="regional_http" and o.get("status") in ("observed","warning") for o in observations),
        "dns_tls":any(o.get("category")=="dns_tls" and o.get("status") in ("observed","warning") for o in observations),
        "bgp_rpki":any(o.get("category")=="bgp_rpki" and o.get("status") in ("observed","warning") for o in observations),
        "traffic":any(o.get("category")=="traffic" and o.get("status")=="observed" for o in observations)}
    used_caps.update({METRIC_TO_CAP[o["metric"]]:True for o in observations if o.get("metric") in METRIC_TO_CAP})
    caps=[{"id":i,"title":name,"source":source,
        "status":"sampled" if used_caps.get(i) else ("not configured" if kind=="optional-token" else
        "requires operator access" if kind=="operator" else "analyst review" if kind=="analyst" else "unavailable")}
        for i,name,source,kind in CAPABILITIES]
    observed=sum(o.get("status") in ("observed","warning") for o in observations)
    status="watch" if incidents else ("sampled-no-correlated-alert" if observed else "unavailable")
    date=when or now()
    history.append({"checkedAt":date,"observed":observed,"alerts":len(incidents),
                    "errors":sum(o.get("status")=="error" for o in observations)})
    return {"schemaVersion":1,"checkedAt":date,"status":status,
       "summary":"No corroborated anomaly among sampled indicators" if status=="sampled-no-correlated-alert" else
       "Correlated anomaly in sampled endpoints; root cause unverified" if status=="watch" else
       "Independent monitoring data unavailable",
       "sampledCount":observed,"incidents":incidents,"observations":observations,
       "capabilities":caps,"history":history[-48:],
       "limitations":[
           "Not a continuous global sensor network: GitHub Actions schedules may be delayed or paused.",
           "Public HTTP HEAD probes are not authenticated transactions; an HTTP response does not prove login, mail or meeting success.",
           "One runner and a small set of community probes do not independently verify all regions or physical infrastructure.",
           "RIPE RPKI examples assess only sampled prefixes; they do not measure global RPKI invalid-route rates or IXP congestion.",
           "Unauthorised internal telemetry, deep-web channels and submarine DAS data are never claimed as ingested.",
           "Radar traffic anomalies, if connected, are third-party observations rather than proof of attack.",
           "Missing telemetry stays unknown; this dashboard never treats absence of reports as system health."
       ]}

def main():
    try: previous=json.loads(OUTPUT.read_text(encoding="utf-8"))
    except (OSError,ValueError):previous={}
    observations=[]
    for probe_id,host,title in PROBES:
        observations.append(tls_probe(probe_id,host,title))
    for provider,host in (("microsoft","login.microsoftonline.com"),("google","accounts.google.com")):
        observations.append(region_probe(host,provider))
    for label,prefix,origin in ROUTES: observations.append(route_probe(label,prefix,origin))
    observations.append(radar_probe())
    observations.extend(private_operator_metrics())
    payload=build_snapshot(observations,previous)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"checkedAt":payload["checkedAt"],"status":payload["status"],
       "sampled":payload["sampledCount"],"alerts":len(payload["incidents"]),
       "unavailable":sum(o.get("status") in ("error","unavailable") for o in observations)}))
    return 0

if __name__=="__main__": raise SystemExit(main())
