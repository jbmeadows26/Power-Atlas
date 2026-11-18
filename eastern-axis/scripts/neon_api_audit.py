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
  ("/api/global-systems/RU", ()),
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
    print(f"{route}: HTTP {item['code']} keys={item['keys'][:8]}",flush=True)
    report["routes"].append(item)
os.makedirs("audit-output",exist_ok=True)
Path("audit-output/eastern-axis-neon-api.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
if report["problems"]:
    print("Problems (may include explicit upstream source outages):")
    for problem in report["problems"]: print(" - " + problem)
    sys.exit(1)
print("All public Neon API contracts passed.")
