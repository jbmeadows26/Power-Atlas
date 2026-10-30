"""Source-only Washington Legislature 2023–24 GetRollCalls ingestion pilot.

Uses free official WA Legislative Web Services XML via HTTP GET. This is a
targeted source-verified *sample* of bills in one biennium, not a census of
all Washington roll calls or all other 49 state legislatures.
"""
import datetime as dt
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"data/legislation/wa-2023-24-rollcalls"
BASE="https://wslwebservices.leg.wa.gov/LegislationService.asmx/GetRollCalls"
BIENNIUM="2023-24"
# HB 1200–1219, 1240, SB 5001–5020 and 5599. Includes both chambers,
# some passed/failed/motionless bills, and a documented policy example.
BILLS=list(range(1200,1220))+[1240]+list(range(5001,5021))+[5599]
MAX_RESPONSE_BYTES=2_000_000
NS={"ws":"http://WSLWebServices.leg.wa.gov/"}
VALID_VOTES={"Yea","Nay","Absent","Excused","Not Voting","Abstain","Present"}

def get_text(parent,tag):
    return (parent.findtext("ws:"+tag,default="",namespaces=NS) or "").strip()

def download(number):
    url=BASE+"?"+urllib.parse.urlencode({"biennium":BIENNIUM,"billNumber":number})
    req=urllib.request.Request(url,headers={"Accept":"application/xml, text/xml","User-Agent":"PowerAtlasPublicResearch/1.0 official noncommercial rollcall source"})
    with urllib.request.urlopen(req,timeout=40) as r:
        if urllib.parse.urlsplit(r.geturl()).hostname!="wslwebservices.leg.wa.gov":
            raise ValueError("WA legislature redirected to untrusted source")
        body=r.read(MAX_RESPONSE_BYTES+1)
    if len(body)>MAX_RESPONSE_BYTES:raise ValueError(f"Official rollcall response >2MB for {number}")
    return body,url

def parse(number,xml,url):
    try: root=ET.fromstring(xml)
    except ET.ParseError as exc:raise ValueError("Non-XML WA legislature response") from exc
    if not root.tag.endswith("ArrayOfRollCall"):
        raise ValueError("Unexpected WA GetRollCalls wrapper tag "+root.tag)
    out=[]
    for vote in root.findall("ws:RollCall",NS):
        billid=get_text(vote,"BillId")
        agency=get_text(vote,"Agency")
        motion=get_text(vote,"Motion")
        sequence=get_text(vote,"SequenceNumber")
        vdate=get_text(vote,"VoteDate")
        if not all((billid,agency,sequence,vdate)):
            raise ValueError("Missing official rollcall identity")
        summary={}
        for side in ("YeaVotes","NayVotes","AbsentVotes","ExcusedVotes"):
            element=vote.find("ws:"+side,NS)
            if element is None:raise ValueError("Missing official voting summary "+side)
            count=element.findtext("ws:Count",default="",namespaces=NS)
            if not count.isdigit():raise ValueError("Bad vote summary count")
            summary[side]=int(count)
        ballots=[]
        seen=set()
        vParent=vote.find("ws:Votes",NS)
        if vParent is None:raise ValueError("No member votes in official source")
        for individual in vParent.findall("ws:Vote",NS):
            member=get_text(individual,"MemberId")
            name=get_text(individual,"Name")
            value=get_text(individual,"VOte") or get_text(individual,"Vote")
            if not member.isdigit() or not name or value not in VALID_VOTES:
                raise ValueError(f"Unknown WA member vote status {number}/{name}/{value}")
            if member in seen:raise ValueError("Duplicate member in one rollcall")
            seen.add(member)
            ballots.append({"memberId":member,"memberName":name,"vote":value})
        sums=Counter(x["vote"] for x in ballots)
        for summaryField,state in (("YeaVotes","Yea"),("NayVotes","Nay"),
                                   ("AbsentVotes","Absent"),("ExcusedVotes","Excused")):
            if summary[summaryField]!=sums[state]:
                raise ValueError(f"Member vs official tally disagreement {number}/{sequence}/{state}: {summary[summaryField]} vs {sums[state]}")
        key=f"WA-{BIENNIUM}-{billid}-{agency}-{sequence}"
        out.append({
            "id":key,"billNumberRequested":number,"billId":billid,"agency":agency,
            "motion":motion,"sequenceNumber":int(sequence),"voteDate":vdate,
            "summary":summary,"memberVotes":ballots,
            "sourceOfficialURL":url,
            "sha256OriginalResponse":hashlib.sha256(xml).hexdigest(),
            "sourceStatus":"official_WA_member_level_rollcall_sample_verified_not_statewide_census",
        })
    return out

def build():
    records=[];missing=[]
    seen=set()
    for n in BILLS:
        body,url=download(n)
        hits=parse(n,body,url)
        if not hits:
            missing.append(n)
        for hit in hits:
            if hit["id"] in seen:raise ValueError("Duplicate vote ID across official bill requests")
            seen.add(hit["id"])
            records.append(hit)
        print(n,len(hits),flush=True)
        time.sleep(.07)
    if len(records)<10:
        raise ValueError("Official state rollcall sample has implausibly few votes")
    if not any("Senate" in x["agency"] for x in records) or not any("House" in x["agency"] for x in records):
        # Published source agencies sometimes encoded H/S, not literal. Check actual.
        agencies=sorted({x["agency"] for x in records})
        if not (any(x.upper().startswith("H") for x in agencies) and any(x.upper().startswith("S") for x in agencies)):
            raise ValueError("Source did not include both chambers: "+repr(agencies))
    rows=sum(len(x["memberVotes"]) for x in records)
    if rows<250:raise ValueError("Insufficient member-level vote evidence")
    DIR.mkdir(parents=True,exist_ok=True)
    meta={
      "schema":"power-atlas.wa-official-rollcall-sample.v1",
      "state":"WA","biennium":BIENNIUM,
      "publicationStatus":"official_original_member_rollcall_sample_not_full_biennium",
      "officialSourceService":BASE,
      "billsRequested":len(BILLS),
      "billsWithAnyRollCalls":len(BILLS)-len(missing),
      "billsWithoutRollCalls":missing,
      "rollCalls":len(records),
      "memberVoteRows":rows,
      "officialDataIntegrity":"member-Yea/Nay/Absent/Excused tallies exactly reconcile to source totals",
      "historicalSessionComplete":False,
      "allStateRollCallsComplete":False,
      "records":records,
    }
    (DIR/"source-rollcalls.json").write_text(json.dumps(meta,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({k:meta[k] for k in ("billsRequested","billsWithAnyRollCalls","rollCalls","memberVoteRows")},indent=2))
if __name__=="__main__":
    build()
