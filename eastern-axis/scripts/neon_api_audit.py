#!/usr/bin/env python3
"""Public, read-only Eastern Axis Neon API contract audit. No credentials needed."""
from __future__ import annotations
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = Path(os.environ.get("EA_API_BASE_FILE","eastern-axis/public-api-origin.txt")).read_text().strip().rstrip("/")
ORIGIN = "https://jbmeadows26.github.io"
ROUTES = [
  ("/api/_healthcheck", ("message", "service")),
  ("/api/overview", ("countries", "cases", "sources")),
  ("/api/intelligence", ("records", "sources")),
  ("/api/world-signals", ("status", "events", "usgsStatus")),
  ("/api/allied-sanctions/RU", ()),
  ("/api/energy-supply/RU", ()),
  ("/api/supply-macro", ()),
  ("/api/supply-trade/RU/27", ()),
  ("/api/supply-chain/RU", ()),
  ("/api/global-systems/RU", ("indicators","covered","requested")),
  ("/api/global-systems/WLD", ("indicators","covered","requested")),
  ("/api/global-systems/US", ("indicators","covered","requested")),
  ("/api/global-systems/CN", ("indicators","covered","requested")),
  ("/api/global-systems/IR", ("indicators","covered","requested")),
  ("/api/defense-intel", ()),
  ("/api/source-monitor", ()),
  ("/api/evidence-workbench", ()),
  ("/api/factbook/countries", ("countries", "baseline")),
  ("/api/factbook/compare?codes=RU,CN", ("rows",)),
  ("/api/brief/RU", ("code", "metrics")),
  ("/api/factbook/RU", ()),
]
assert API.startswith("https://") and API.endswith(".neon.tech"), "Invalid public backend URL"
report = {"api": API, "checkedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()), "routes":[], "problems":[]}
for route, keys in ROUTES:
    item = {"route":route}
    request = urllib.request.Request(API + route, headers={"Accept":"application/json","Origin":ORIGIN})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            item["code"] = response.status
            item["cors"] = response.headers.get("access-control-allow-origin","")
            raw = response.read(3_000_000)
    except urllib.error.HTTPError as e:
        item["code"] = e.code
        item["cors"] = e.headers.get("access-control-allow-origin","")
        raw = e.read(3000)
    except Exception as e:
        item["code"] = -1
        item["transportError"] = type(e).__name__ + ": " + str(e)[:180]
        raw = b""
    try: payload=json.loads(raw)
    except Exception: payload=None
    item["keys"] = sorted(payload.keys())[:25] if isinstance(payload,dict) else []
    if isinstance(payload,dict) and isinstance(payload.get("records"),list):
        item["recordCount"]=len(payload["records"])
    if isinstance(payload,dict):
        for name in ("status","usgsStatus","nasaStatus","updatedAt","checkedAt"):
            if isinstance(payload.get(name),(str,int,float,bool)):
                item[name]=payload[name]
    if item["code"] != 200:
        report["problems"].append(f"{route}: HTTP {item['code']} {item.get('transportError','')}")
    if item["cors"] != ORIGIN:
        report["problems"].append(f"{route}: Pages origin not permitted")
    for key in keys:
        if key not in item["keys"]:
            report["problems"].append(f"{route}: missing {key}")
    # Country completeness is a release gate; 200 OK with 1/12 is still broken.
    minima={"WLD":10,"US":10,"CN":8,"IR":7}
    if route.startswith("/api/global-systems/") and isinstance(payload,dict):
        country=route.rsplit("/",1)[-1]
        indicators=payload.get("indicators")
        if not isinstance(indicators,list) or len(indicators)!=12:
            report["problems"].append(f"{route}: expected 12 defined indicators")
        else:
            supported=sum(1 for indicator in indicators
                if isinstance(indicator,dict) and isinstance(indicator.get("value"),(int,float)))
            item["supportedIndicators"]=supported
            item["totalIndicators"]=len(indicators)
            if country in minima and supported<minima[country]:
                report["problems"].append(f"{route}: only {supported}/12 observed (minimum {minima[country]})")
            for indicator in indicators:
                if not isinstance(indicator,dict): continue
                value=indicator.get("value")
                if value is not None and (not indicator.get("year") or not indicator.get("sourceUrl")):
                    report["problems"].append(f"{route}: undated or unsourced {indicator.get('code')}")
    print(f"{route}: HTTP {item['code']} keys={item['keys'][:8]}",flush=True)
    report["routes"].append(item)
# Negative security checks: public Pages traffic must not trigger ingestion.
for route, method, claimed_origin, expected in (
    ("/api/cron/doj", "GET", ORIGIN, 401),
    ("/_neon/cron/doj", "POST", ORIGIN, 401),
    ("/api/_healthcheck", "GET", "https://untrusted.invalid", 403),
    ("/api/does-not-exist", "GET", ORIGIN, 404),
):
    request=urllib.request.Request(API+route,method=method,
        headers={"Accept":"application/json","Origin":claimed_origin,"Content-Type":"application/json"},
        data=b"{}" if method=="POST" else None)
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            status=response.status
    except urllib.error.HTTPError as exc:
        status=exc.code
    except Exception as exc:
        report["problems"].append(f"{route}: security check transport failed: {type(exc).__name__}")
        continue
    report["routes"].append({"route":route,"method":method,"httpStatus":status,"expected":expected,"securityCheck":True})
    print(f"{route} ({method}): HTTP {status}, expected {expected}",flush=True)
    if status!=expected:
        report["problems"].append(f"{route} ({method}): expected {expected}, got {status}")

os.makedirs("audit-output",exist_ok=True)
Path("audit-output/eastern-axis-neon-api.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
if report["problems"]:
    print("Problems (may include explicit upstream source outages):")
    for problem in report["problems"]: print(" - " + problem)
    sys.exit(1)
print("All public Neon API contracts passed.")
