#!/usr/bin/env python3
"""Free-source, evidence-labelled Congressional age snapshot. No inferred wealth or class."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "data/people/congress-members.json"
OUT = ROOT / "data/research/political-authenticity"
SOURCE = "https://raw.githubusercontent.com/unitedstates/congress-legislators/gh-pages/legislators-current.json"
STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())

def age_at(birth, day):
    b = dt.date.fromisoformat(birth)
    return day.year-b.year-((day.month,day.day)<(b.month,b.day))

def valid_term(member, biography, day):
    kind = "rep" if member["chamber"] == "House" else "sen"
    for t in biography.get("terms",[]):
        if t.get("type") != kind or t.get("state") != member["state"]:
            continue
        try:
            valid_dates = dt.date.fromisoformat(t["start"]) <= day < dt.date.fromisoformat(t["end"])
        except (KeyError,ValueError):
            continue
        if not valid_dates:
            continue
        if kind=="rep" and t.get("district") is not None and str(t["district"]) != str(member.get("district")):
            continue
        return True
    return False

def collect(roster, biographies, day, digest):
    current = {b["id"]["bioguide"]:b for b in biographies if isinstance(b,dict) and isinstance(b.get("id"),dict) and b["id"].get("bioguide")}
    rows=[]
    seen=set()
    for m in roster["records"]:
        key=m.get("bioguideId")
        if not isinstance(key,str) or not re.fullmatch(r"[A-Z][0-9]{6}",key) or key in seen:
            raise ValueError("Malformed/duplicate Bioguide ID")
        if m.get("chamber") not in ("House","Senate"): raise ValueError("Invalid chamber")
        seen.add(key)
        b=current.get(key)
        birthday=b.get("bio",{}).get("birthday") if b and valid_term(m,b,day) else None
        try:
            years=age_at(birthday,day) if birthday else None
            if years is not None and not (25<=years<=110):
                birthday=None
                years=None
        except ValueError:
            birthday=None
            years=None
        rows.append({
            "bioguideId":key,"name":m.get("name"),"chamber":m["chamber"],"state":m["state"],
            "district":m.get("district") if m["chamber"]=="House" else None,
            "party":m.get("party"),"votingMember":m["chamber"]=="Senate" or m["state"] in STATES,
            "birthDate":birthday,"ageYears":years,
            "occupationBeforePolitics":None,"education":None,"wealthIntervalUsd":None,
            "raceEthnicitySelfReported":None,"constituentResponsiveness":None,
            "ageSourceStatus":"CC0_secondary_term_matched_unverified" if birthday else "not_available",
            "sourceRoster":m.get("source"),"biographySource":SOURCE if birthday else None
        })
    rows.sort(key=lambda r:r["bioguideId"])
    n=len(rows)
    joined=sum(r["birthDate"] is not None for r in rows)
    if n<500 or joined==0: raise ValueError("Insufficient source coverage; keep previous snapshot")
    coverage={
      "schema":"power-atlas.representation-coverage.v1","asOf":day.isoformat(),
      "rosterTotal":n,"houseIncludingDelegates":sum(r["chamber"]=="House" for r in rows),
      "senators":sum(r["chamber"]=="Senate" for r in rows),
      "nonVotingHouse":sum(r["chamber"]=="House" and not r["votingMember"] for r in rows),
      "ageKnown":joined,"ageUnknown":n-joined,"ageCoverageFraction":round(joined/n,4),
      "occupationKnown":0,"educationKnown":0,"wealthKnown":0,"raceEthnicityKnown":0,
      "notMeasured":["political_alienation","perceived_authenticity","substantive_policy_responsiveness"],
      "status":"secondary_CC0_source_unverified_primary_Bioguide_crosscheck_pending",
      "warning":"Roster reference date differs from CRS Jan 2025 membership cohort. Exclude delegates from voting-seat comparisons. Unknown is not zero.",
      "carnes2012Correction":{"published":"2026-04-26","doi":"10.1111/lsq.70066","scope":"Appendix B coefficients; author reports unchanged substantive interpretation"}
    }
    snapshot={"schema":"power-atlas.representation-members.v1","asOf":day.isoformat(),
              "source":SOURCE,"sourceSha256":digest,"license":"CC0-1.0",
              "reviewStatus":"unverified_secondary_data_not_policy_influence_findings","records":rows}
    return snapshot,coverage

def write_changed(path,document):
    path.parent.mkdir(parents=True,exist_ok=True)
    output=json.dumps(document,ensure_ascii=False,indent=2)+"\n"
    if not path.exists() or path.read_text(encoding="utf-8")!=output:
        path.write_text(output,encoding="utf-8")
        return True
    return False

def main():
    roster=json.loads(ROSTER.read_text(encoding="utf-8"))
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"PowerAtlasPublicResearch/1.0"})
    with urllib.request.urlopen(req,timeout=25) as response:
        raw=response.read(15_000_001)
    if len(raw)>15_000_000: raise ValueError("Source unexpectedly large")
    day=dt.date.today()
    snapshot,coverage=collect(roster,json.loads(raw),day,hashlib.sha256(raw).hexdigest())
    a=write_changed(OUT/"members.json",snapshot)
    b=write_changed(OUT/"coverage.json",coverage)
    print(json.dumps({"members":coverage["rosterTotal"],"birthDatesKnown":coverage["ageKnown"],"changed":a or b}))
if __name__=="__main__":main()
