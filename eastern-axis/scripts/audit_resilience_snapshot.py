#!/usr/bin/env python3
"""Weekly public resilience snapshot integrity gate.

Independent of the application's vendor status display, and conservative about
GitHub Actions schedule jitter. Does not treat individual probe errors as an outage.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from pathlib import Path
import sys
import urllib.request

URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json"
REQUIRED={"regional_http","dns_tls","bgp_rpki"}
UTC=dt.timezone.utc

def verify(payload,now):
    failures=[]
    if not isinstance(payload,dict) or payload.get("schemaVersion")!=1:
        return ["Telemetry snapshot schema invalid"]
    when=payload.get("checkedAt")
    try:
        checked=dt.datetime.fromisoformat(when.replace("Z","+00:00"))
        if checked.tzinfo is None:raise ValueError("missing timezone")
        age=(now-checked).total_seconds()
        if age < -60:failures.append("Snapshot timestamp ahead of audit clock")
        elif age > 4*3600:failures.append("Snapshot age exceeded 4h (scheduled collector may be broken)")
    except (ValueError,TypeError,AttributeError):
        failures.append("Snapshot checkedAt missing or unparseable")
    obs=payload.get("observations")
    if not isinstance(obs,list):return failures+["Observations array missing"]
    ids=[x.get("id") for x in obs if isinstance(x,dict)]
    if len(ids)!=len(set(ids)):failures.append("Duplicate observation identifiers")
    available={x.get("category") for x in obs if isinstance(x,dict) and x.get("status") in ("observed","warning")}
    missing=REQUIRED-available
    if missing:failures.append("No usable sample from "+", ".join(sorted(missing)))
    if len([x for x in obs if isinstance(x,dict) and x.get("status") in ("observed","warning")])<5:
        failures.append("Fewer than 5 sampled independent source checks")
    if not isinstance(payload.get("capabilities"),list):
        failures.append("Capability coverage status absent")
    return failures

def main():
    path=Path(os.environ.get("AUDIT_OUTPUT_DIR","audit-output"))/"resilience-telemetry-audit.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    now=dt.datetime.now(UTC)
    try:
        req=urllib.request.Request(URL,headers={
            "User-Agent":"EasternAxis-Weekly-Resilience-Audit/1.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=15) as res:
            payload=json.loads(res.read(300000))
        errors=verify(payload,now)
        summary={"checkedAt":now.isoformat(),"snapshotAt":payload.get("checkedAt"),
            "status":"failed" if errors else "ok","observed":payload.get("sampledCount"),
            "sourceGroups":sorted({str(o.get("category")) for o in payload.get("observations",[]) if isinstance(o,dict)}),
            "errors":errors,"sourceUrl":URL}
    except Exception as exc:
        summary={"checkedAt":now.isoformat(),"status":"failed",
             "errors":[type(exc).__name__+": "+str(exc)[:140]],"sourceUrl":URL}
    path.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as report:
            report.write("\\n### Independent resilience telemetry: "+summary["status"]+"\\n")
            for error in summary["errors"]:
                report.write("- "+error+"\\n")
    return 1 if summary["status"]=="failed" else 0

if __name__=="__main__":
    raise SystemExit(main())
