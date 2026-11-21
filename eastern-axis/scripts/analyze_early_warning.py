#!/usr/bin/env python3
"""Evidence-gated early-warning analyst: scheduled, attributable, fail-closed.
An ephemeral Ollama model may recommend review; it cannot fabricate corroboration
or override source freshness, historical baselines, or official alert status.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
from statistics import median
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"public/analysis/physical-early-warning.json"
OUTPUT=ROOT/"public/analysis/early-warning-triage.json"

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def age_days(when, today=None):
    try:
        raw=str(when or "")
        # Monthly agency series publish YYYY-MM. Interpret that period by its
        # first calendar day; never fabricate an observation on the month end.
        if len(raw)==7 and raw[4]=="-":
            stamp=date.fromisoformat(raw+"-01")
        else:
            stamp=date.fromisoformat(raw[:10])
        return ((today or datetime.now(timezone.utc).date())-stamp).days
    except (ValueError, TypeError):
        return None

def metric_delta(m, a, b):
    mode=m.get("compareMode")
    try:
        a,b=float(a),float(b)
        if not all(map(math.isfinite,(a,b))):return None
        if mode=="basis-points":return (a-b)*100
        if mode=="percentage-points":return a-b
        if b==0:return None
        return (a/b-1)*100
    except (ValueError,TypeError,ZeroDivisionError):
        return None

def base_screen(m):
    mode=m.get("compareMode")
    value=m.get("changeBps") if mode=="basis-points" else m.get("changePp") if mode=="percentage-points" else m.get("changePct")
    try:
        v=float(value)
        return math.isfinite(v) and abs(v)>=(20 if mode=="basis-points" else 5 if mode=="percentage-points" else 10)
    except (TypeError,ValueError):return False

def historical_anomaly(m):
    # Eight *distinct, dated* historical changes minimum. Two-point movement is not a norm.
    history=m.get("history",[])
    if not isinstance(history,list):return {"status":"insufficient","sampleSize":0,"robustZ":None}
    points={}
    for row in history:
        if isinstance(row,dict) and isinstance(row.get("period"),str):
            try:
                value=float(row.get("value"))
                if math.isfinite(value) and abs(value)<1e12:
                    points[row["period"]]=value
            except (ValueError,TypeError):pass
    ordered=sorted(points.items())
    deltas=[metric_delta(m,ordered[i][1],ordered[i-1][1]) for i in range(1,len(ordered))]
    deltas=[x for x in deltas if x is not None]
    if len(deltas)<8:return {"status":"insufficient","sampleSize":len(deltas),"robustZ":None}
    # Leave the latest observation OUT of the reference distribution.
    baseline=deltas[:-1]
    if len(baseline)<8:return {"status":"insufficient","sampleSize":len(baseline),"robustZ":None}
    center=median(baseline)
    spread=median([abs(x-center) for x in baseline])
    if spread<1e-6:
        return {"status":"flat-baseline","sampleSize":len(baseline),"robustZ":None}
    latest=metric_delta(m,m.get("value"),m.get("previous"))
    if latest is None:return {"status":"invalid","sampleSize":len(baseline),"robustZ":None}
    z=round((latest-center)/(1.4826*spread),2)
    return {"status":"assessable","sampleSize":len(baseline),"robustZ":z,
            "medianChange":round(center,3),"medianAbsoluteDeviation":round(spread,3)}

def guard_source(m,checked):
    age=age_days(m.get("period"))
    collect=age_days(checked)
    if age is None or age<0 or collect is None or collect<0 or collect>3:return False
    return age<=(65 if m.get("interval")=="monthly" else 5)

def sector(metric_id):
    if metric_id in ("fao-cereals","worldbank-wheat","worldbank-maize","worldbank-rice"):return "grain-prices"
    if metric_id in ("fao-oils","worldbank-palm-oil","worldbank-soybeans"):return "oilseed-prices"
    return None

def screen(snapshot):
    result=[]
    checked=snapshot.get("checkedAt")
    for m in snapshot.get("metrics",[]):
        if not isinstance(m,dict) or not isinstance(m.get("id"),str):continue
        history=historical_anomaly(m)
        trigger=base_screen(m)
        fresh=guard_source(m,checked)
        anomaly=history.get("status")=="assessable" and abs(history.get("robustZ") or 0)>=3
        result.append({
            "id":m["id"],"kind":"metric","title":m.get("label","Untitled measurement"),
            "group":m.get("group","unassigned"),"source":m.get("source",""),"sourceUrl":m.get("sourceUrl",""),
            "observedAt":m.get("period"),"changePct":m.get("changePct"),
            "screened":bool(trigger),"fresh":fresh,"baseline":history,
            "anomalous":bool(anomaly),"needsReview":bool(trigger and fresh),
            "sector":sector(m["id"]),"corroborated":False,
            "direction":1 if metric_delta(m,m.get("value"),m.get("previous")) and metric_delta(m,m.get("value"),m.get("previous"))>0 else -1,
            "status":"monitor","reason":"Pending analyst evaluation" if trigger and fresh else (
                "Older observation; retained for historical monitoring" if not fresh else
                "Movement below review threshold" if not trigger else "No publishable elevated finding"),
            "confidence":"unassessed","modelReviewed":False,"evidence":[m.get("sourceUrl","")],
            "gate":"historical-anomaly-needs-independent-corroboration"
        })
    # Corroboration requires two DIFFERENT publishers, compatible geographic
    # measurement coverage, same dated month and direction, and independently
    # robust abnormal movement. A collection of World Bank price series does
    # not count as multi-source validation.
    for r in result:
        if not (r["needsReview"] and r["anomalous"] and r.get("sector")):continue
        peers=[p for p in result if p["id"]!=r["id"] and p.get("sector")==r["sector"]
               and p["group"]==r["group"] and p["source"]!=r["source"]
               and p["fresh"] and p["needsReview"] and p["anomalous"]
               and p.get("direction")==r.get("direction")
               and abs((age_days(p["observedAt"]) or 0)-(age_days(r["observedAt"]) or 0))<=45]
        if peers:
            r["corroborated"]=True
            r["corroboration"]=[{"id":p["id"],"source":p["source"],
                               "observedAt":p["observedAt"],"sourceUrl":p["sourceUrl"]} for p in peers[:5]]
            r["evidence"].extend(p["sourceUrl"] for p in peers[:5])
    for item in snapshot.get("eventFeeds",[]):
        if not isinstance(item,dict):continue
        for ev in item.get("events",[])[:35]:
            if not isinstance(ev,dict) or not isinstance(ev.get("id"),str):continue
            fresh=guard_source({"period":ev.get("observedAt"),"interval":"daily"},checked)
            # Publisher publication date is not enough: the alert must remain
            # unexpired at the instant this analyst review is generated.
            expiry=ev.get("expiresAt")
            active=False
            if isinstance(expiry,str):
                try:
                    active=datetime.fromisoformat(expiry.replace("Z","+00:00"))>datetime.now(timezone.utc)
                except (ValueError,TypeError):pass
            official=bool(ev.get("officialAlert") and ev.get("severity") in ("Extreme","Severe")
                          and fresh and active)
            result.append({
                "id":ev["id"],"kind":"advisory" if official else "event",
                "title":ev.get("title","Official source observation"),"group":ev.get("group","global"),
                "source":item.get("publisher",""),"sourceUrl":ev.get("sourceUrl",""),
                "observedAt":ev.get("observedAt"),"screened":official,"fresh":fresh,
                "baseline":{"status":"not-applicable","sampleSize":0,"robustZ":None},
                "anomalous":False,"needsReview":official,"status":"monitor",
                "sector":None,"corroborated":False,
                "reason":"Official adverse-condition advisory awaiting analyst review" if official else "Official event lead; significance is not established",
                "confidence":"unassessed","modelReviewed":False,
                "evidence":[ev.get("sourceUrl","")],"gate":"official-advisory-only",
                "officialAlert":official,"severity":ev.get("severity","Unknown")
            })
    return result

def model_assess(candidates,endpoint,model):
    """Isolate each AI review, retry malformed items once, and fail closed.
    Successful reviews are never discarded when a different response fails.
    An AI output is only advice; evaluate() enforces the independent gates.
    """
    if not candidates:return {}, "not-needed"
    if not endpoint:return {}, "unavailable"
    findings={}
    for record in candidates[:30]:
        item={"id":record["id"],"title":record["title"],"source":record["source"],
              "group":record["group"],"observedAt":record["observedAt"],
              "historical":record["baseline"],"anomalous":record.get("anomalous",False),
              "corroborated":record.get("corroborated",False),
              "corroboration":record.get("corroboration",[]),
              "officialAlert":record.get("officialAlert",False),
              "severity":record.get("severity"),"sourceUrl":record["sourceUrl"]}
        directions=("Review exactly ONE source-dated early-warning observation. Be conservative. "
            "Use only this record. ELEVATE only for a currently active official Severe/Extreme "
            "advisory or fresh robust-z >=3 movement with same-scope, same-direction evidence "
            "from an independent publisher. Otherwise MONITOR. Never infer hostile causes. ")
        example=('Return exactly one JSON object containing: '
            '{"id":"record-id","decision":"monitor","confidence":"low",'
            '"rationale":"Source-linked evidence and its limitations."}. '
            'Use the supplied id verbatim; decision=monitor|elevate, confidence=low|medium|high, '
            'rationale 6-500 characters. Record: ')
        for attempt in range(2):
            prompt=(directions if attempt==0 else
                "RETRY: Your prior reply was invalid JSON. No prose, arrays or Markdown. "
                "Return just the JSON object. When unsure, MONITOR. ")+example+json.dumps(item,ensure_ascii=False)
            payload=json.dumps({"model":model,"stream":False,"format":"json",
                  "options":{"temperature":0,"num_predict":260},"prompt":prompt}).encode()
            try:
                req=urllib.request.Request(endpoint.rstrip("/")+"/api/generate",data=payload,
                      headers={"Content-Type":"application/json"},method="POST")
                with urllib.request.urlopen(req,timeout=90) as response:
                    raw=json.load(response)
                parsed=json.loads(raw.get("response",""))
                if isinstance(parsed,dict) and isinstance(parsed.get("findings"),list) and len(parsed["findings"])==1:
                    parsed=parsed["findings"][0]
                if not isinstance(parsed,dict) or parsed.get("id")!=record["id"]:
                    raise ValueError("Missing or mismatched record identifier")
                if parsed.get("decision") not in ("monitor","elevate") or parsed.get("confidence") not in ("low","medium","high"):
                    raise ValueError("Invalid model decision or confidence")
                rationale=parsed.get("rationale")
                if not isinstance(rationale,str) or not (6<=len(rationale)<=500):
                    raise ValueError("Missing auditable rationale")
                findings[record["id"]]={"decision":parsed["decision"],
                          "confidence":parsed["confidence"],"rationale":rationale}
                break
            except (OSError,ValueError,KeyError,TypeError) as e:
                print("Model review rejected for",record["id"],"attempt",attempt+1,
                      type(e).__name__,flush=True)
    if not findings:return {},"unavailable"
    return findings, ("available" if len(findings)==len(candidates[:30]) else "partial")

def evaluate(snapshot, model_endpoint="", model="qwen2.5:1.5b",today=None):
    if snapshot.get("schemaVersion")!=1 or not isinstance(snapshot.get("metrics"),list) or not isinstance(snapshot.get("sources"),list):
        raise ValueError("Unverified source snapshot; refusing to issue decisions")
    rows=screen(snapshot)
    candidates=[r for r in rows if r["needsReview"]][:30]
    findings,model_status=model_assess(candidates,model_endpoint,model)
    alerts=[]
    for r in rows:
        finding=findings.get(r["id"])
        if not finding:
            if r["needsReview"]:r["reason"]="Awaiting a valid AI review; not escalated" if model_status in ("unavailable","partial") else "Review capacity limited; not escalated"
            continue
        r["modelReviewed"]=True
        r["confidence"]=finding["confidence"]
        r["reason"]=finding["rationale"]
        # A direct, fresh severe official advisory OR a fresh, statistically
        # abnormal cross-publisher metric pair may reach Command. Model opinion
        # without these independent hard gates is always vetoed.
        eligible=(r["fresh"] and finding["decision"]=="elevate"
                  and finding["confidence"] in ("medium","high") and (
                    r.get("officialAlert",False) or
                    (r.get("kind")=="metric" and r["anomalous"] and r.get("corroborated",False))))
        if eligible:
            r["status"]="elevated"
            alerts.append({key:r[key] for key in ("id","title","group","source","sourceUrl","observedAt","confidence","reason","kind","evidence")})
        elif finding["decision"]=="elevate":
            r["reason"]="Analyst proposal withheld: independent verification gate not met. "+r["reason"][:240]
    return {
        "schemaVersion":1,"generatedAt":utcnow(),"sourceCheckedAt":snapshot.get("checkedAt"),
        "model":{"status":model_status,"name":model if model_status=="available" else None,
                 "role":"advisory reasoning; deterministic evidence rules veto unsupported promotion"},
        "policy":"Command accepts fresh severe/extreme official advisories or statistically exceptional same-scope market movements corroborated by a separate publisher and reviewed by AI. Other outliers remain monitored.",
        "summary":{"observed":len(rows),"screened":sum(r["screened"] for r in rows),
                   "reviewed":sum(r["modelReviewed"] for r in rows),
                   "monitoring":len(rows)-len(alerts),"elevated":len(alerts),
                   "historyReady":sum(r["baseline"]["status"]=="assessable" for r in rows)},
        "reviews":rows,"alerts":alerts
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=INPUT)
    p.add_argument("--output",type=Path,default=OUTPUT)
    p.add_argument("--model-endpoint",default="")
    p.add_argument("--model",default="qwen2.5:1.5b")
    args=p.parse_args()
    source=json.loads(args.input.read_text())
    evaluated=evaluate(source,args.model_endpoint,args.model)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(evaluated,indent=2,ensure_ascii=False)+"\n")
    print("Triage:",evaluated["summary"],"model:",evaluated["model"]["status"])

if __name__=="__main__":main()
