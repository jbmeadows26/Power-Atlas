#!/usr/bin/env python3
"""Bounded ingestion of official House roll-call XML; NOT a voter-preference study."""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib import request, error
from xml.etree import ElementTree as ET

BASE="https://clerk.house.gov/evs"
VALID_VOTES={"Yea","Nay","Present","Not Voting"}
def parse_roll(xml_bytes, source, year, number):
    root=ET.fromstring(xml_bytes)
    meta=root.find("vote-metadata")
    if meta is None: raise ValueError("Missing official vote metadata")
    def field(tag):
        node=meta.find(tag)
        return "".join(node.itertext()).strip() if node is not None else ""
    question=field("vote-question")
    if not question: raise ValueError("Missing roll-call question")
    votes={}
    for vote in root.findall(".//vote-data/recorded-vote"):
        person=vote.find("legislator")
        val=vote.findtext("vote","").strip()
        identity=person.get("name-id","") if person is not None else ""
        if not re.fullmatch(r"[A-Z][0-9]{6}",identity) or val not in VALID_VOTES:
            continue
        if identity in votes: raise ValueError("Duplicate member recorded on same roll")
        votes[identity]=val
    if len(votes)<200: raise ValueError("Unexpectedly incomplete House roll call")
    return {"id":f"house-{year}-{number:03d}","congress":119,"year":year,
      "rollCall":number,"date":field("action-date"),"question":question,
      "description":field("vote-desc"),"result":field("vote-result"),
      "source":source,"sourceSha256":hashlib.sha256(xml_bytes).hexdigest(),
      "votes":votes,"memberVotes":len(votes),"reviewStatus":"official_house_rollcall_not_dyadic_policy_responsiveness"}
def fetch(year,number,seconds=18):
    url=f"{BASE}/{year}/roll{number:03d}.xml"
    req=request.Request(url,headers={"User-Agent":"PowerAtlasPublicResearch/1.0 (official public evidence)"})
    for attempt in range(3):
        try:
            with request.urlopen(req,timeout=seconds) as response:
                raw=response.read(450000)
                if len(raw)>=450000: raise ValueError("Unexpectedly large XML")
                return parse_roll(raw,url,year,number)
        except error.HTTPError as exc:
            if exc.code==404: return None
            if exc.code in (429,500,502,503,504) and attempt<2:
                time.sleep(1+attempt*2)
                continue
            raise
    return None
def run(year,first,last):
    if year not in (2025,2026) or not (1<=first<=last<=500):
        raise ValueError("Unsupported year / bounded roll-call window")
    rows=[]
    errors=[]
    for number in range(first,last+1):
        try:
            item=fetch(year,number)
            if item: rows.append(item)
        except (ValueError,error.URLError,ET.ParseError,TimeoutError) as exc:
            errors.append({"rollCall":number,"errorType":type(exc).__name__})
        time.sleep(0.09)
    if not rows: raise ValueError("No official roll calls retrieved; refuse empty overwrite")
    return {"schema":"power-atlas.house-official-rollcalls.v1","year":year,
        "requestedRange":[first,last],"retrieved":len(rows),
        "requestErrors":errors,"records":rows,
        "status":"primary_source_records_no_issue_preference_join",
        "note":"First-numbered roll calls are NOT preselected key policy votes; absent votes are not Nay."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--year",type=int,default=2025)
    p.add_argument("--first",type=int,default=1)
    p.add_argument("--last",type=int,default=150)
    p.add_argument("--output",type=Path,default=Path("data/research/political-authenticity/house-rollcalls-2025.json"))
    args=p.parse_args()
    data=run(args.year,args.first,args.last)
    if args.output.exists():
        previous=json.loads(args.output.read_text(encoding="utf-8"))
        if previous.get("year")==args.year and previous.get("schema")==data["schema"]:
            retained={r["rollCall"]:r for r in previous.get("records",[]) if args.first<=r["rollCall"]<=args.last}
            retained.update({r["rollCall"]:r for r in data["records"]})
            data["records"]=sorted(retained.values(),key=lambda r:r["rollCall"])
            data["retrieved"]=len(data["records"])
    requested=args.last-args.first+1
    data["coverageStatus"]="complete_window" if data["retrieved"]==requested else "partial_window"
    observed={r["rollCall"] for r in data["records"]}
    data["missingRollNumbers"]=[n for n in range(args.first,args.last+1) if n not in observed]
    data["completionNote"]="Partial coverage preserved; missing roll numbers are not Nay votes or proof a vote did not happen."
    args.output.parent.mkdir(parents=True,exist_ok=True)
    rendered=json.dumps(data,sort_keys=True,separators=(",",":"))+"\n"
    if not args.output.exists() or args.output.read_text(encoding="utf-8")!=rendered:
        args.output.write_text(rendered,encoding="utf-8")
    print(json.dumps({"retrieved":data["retrieved"],"errors":len(data["requestErrors"]),
        "memberVotes":sum(len(r["votes"]) for r in data["records"])}))
if __name__=="__main__": main()
