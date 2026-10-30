#!/usr/bin/env python3
"""Build a SOURCE-BACKED gubernatorial election schedule and *provisional* FY join.

Uses National Governors Association / Ballotpedia's historical regular state
governor election cohort lists (not the 50-state fiscal-year labeling guessed
from calendar year). State-specific electoral dates are secondary-source
assertions and fiscal-year boundary backcast is UNVERIFIED historically.
This is therefore descriptive only; the strict verified causal TWFE gate is
NOT satisfied. Simultaneous 2012 WI recall is separately noted, not silently
treated as a scheduled governor-election event.
"""
import calendar
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIN=ROOT/"data/fiscal/state-timeseries"
OUT=FIN/"governor-elections-fiscaljoin-2012-2024.json"
SOURCE_NGA="https://www.nga.org/governors/elections/"
SOURCE_HISTORY="https://ballotpedia.org/Governor"
SOURCE_OFF="https://www.ncsl.org/elections-and-campaigns/consolidating-election-dates"
SOURCE_2016="https://ballotpedia.org/Gubernatorial_elections,_2016"
SOURCE_OR="https://ballotpedia.org/Oregon_gubernatorial_special_election,_2016"
SOURCE_WI="https://ballotpedia.org/Wisconsin_gubernatorial_recall_election,_2012"

# Exact modern FIPS state IDs grouped by documented regular gubernatorial cycles.
# 36 class-A states elect in 2014/2018/2022; NH & VT additionally in every even year.
CLASS_A={
 "01":"Alabama","02":"Alaska","04":"Arizona","05":"Arkansas","06":"California",
 "08":"Colorado","09":"Connecticut","12":"Florida","13":"Georgia","15":"Hawaii",
 "16":"Idaho","17":"Illinois","19":"Iowa","20":"Kansas","23":"Maine","24":"Maryland",
 "25":"Massachusetts","26":"Michigan","27":"Minnesota","31":"Nebraska","32":"Nevada",
 "33":"New Hampshire","35":"New Mexico","36":"New York","39":"Ohio","40":"Oklahoma",
 "41":"Oregon","42":"Pennsylvania","44":"Rhode Island","45":"South Carolina",
 "46":"South Dakota","47":"Tennessee","48":"Texas","50":"Vermont","55":"Wisconsin",
 "56":"Wyoming",
}
CLASS_B={
 "10":"Delaware","18":"Indiana","29":"Missouri","30":"Montana",
 "37":"North Carolina","38":"North Dakota","49":"Utah","53":"Washington",
 "54":"West Virginia",
}
OFF_NJ_VA={"34":"New Jersey","51":"Virginia"}
OFF_KY_LA_MS={"21":"Kentucky","22":"Louisiana","28":"Mississippi"}
SPECIAL_2016={"41"}
REGULAR_2Y={"33","50"}
ALL_STATES={**CLASS_A,**CLASS_B,**OFF_NJ_VA,**OFF_KY_LA_MS}

def first_tuesday_after_first_monday(year, month=11):
    d=dt.date(year,month,1)
    monday_offset=(0-d.weekday())%7
    return d+dt.timedelta(days=monday_offset+1)

def schedule():
    assert len(CLASS_A)==36 and len(CLASS_B)==9 and len(ALL_STATES)==50
    events=[]
    for year in range(2011,2025):
        selected={}
        if year%4==2: # 2014/2018/2022: 36
            selected.update(CLASS_A)
        elif year%4==0: # 2012/2016/2020/2024: 11 (9 + NH/VT)
            selected.update(CLASS_B)
            selected.update({i:CLASS_A[i] for i in REGULAR_2Y})
        if year%4==1: # 2013/2017/2021
            selected.update(OFF_NJ_VA)
        if year%4==3: # 2011/2015/2019/2023
            selected.update(OFF_KY_LA_MS)
        if year==2016:
            selected["41"]=CLASS_A["41"]
        for fips,name in selected.items():
            date=first_tuesday_after_first_monday(year)
            phase="regular_general_election"
            if fips=="22": # LA jungle primary and, as necessary, runoff
                if year==2011:
                    date=dt.date(2011,10,22)
                    phase="louisiana_jungle_primary_winner"
                elif year==2015:
                    date=dt.date(2015,11,21)
                    phase="louisiana_runoff_decisive"
                elif year==2019:
                    date=dt.date(2019,11,16)
                    phase="louisiana_runoff_decisive"
                elif year==2023:
                    date=dt.date(2023,10,14)
                    phase="louisiana_jungle_primary_winner"
            if fips=="41" and year==2016:
                phase="special_general_election_not_regular_cycle"
            source=SOURCE_HISTORY
            if year>=2018:
                source=SOURCE_NGA
            if year==2016:
                source=SOURCE_2016
            if fips=="41" and year==2016:
                source=SOURCE_OR
            if fips=="22":
                source="https://ballotpedia.org/Louisiana_gubernatorial_election,_"+str(year)
            events.append({
                "id":f"{fips}-{year}",
                "fipsState":fips,"state":name,"electionCalendarYear":year,
                "governorElectionDay":date.isoformat(),
                "electionDayRole":phase,
                "sourceURL":source,
                "sourceStatus":"documented_secondary_historical_summary_not_certified_by_state_canvass",
            })
    assert len(events)==sum([3,11,2,36,3,12,2,36,3,11,2,36,3,11])
    return sorted(events,key=lambda e:(e["governorElectionDay"],e["fipsState"]))

def make():
    doc=json.loads((FIN/"fiscal-calendar-template-2012-2024.json").read_text(encoding="utf-8"))
    if len(doc.get("records",[]))!=650:
        raise ValueError("Missing 650 source-matched state fiscal-year boundaries")
    events=schedule()
    indexed={fips:[] for fips in ALL_STATES}
    for ev in events:
        indexed[ev["fipsState"]].append(ev)
    rows=[]
    for fy in doc["records"]:
        fips=fy["fipsState"]
        start=dt.date.fromisoformat(fy["fiscalStartDate"])
        end=dt.date.fromisoformat(fy["fiscalEndDate"])
        in_this=[ev for ev in indexed[fips] if start<=dt.date.fromisoformat(ev["governorElectionDay"])<=end]
        next_end=end+dt.timedelta(days=365)
        future=[ev for ev in indexed[fips] if end<dt.date.fromisoformat(ev["governorElectionDay"])<=next_end]
        if len(in_this)>1:
            raise ValueError(f"Unexpected multiple decisive governor elections in FY: {fips}, {fy['fiscalYearLabel']}")
        rows.append({
            "id":fy["id"],"fipsState":fips,"state":fy["state"],"fiscalYear":fy["fiscalYearLabel"],
            "fiscalStartDate":fy["fiscalStartDate"],"fiscalEndDate":fy["fiscalEndDate"],
            "electionDuringFiscalYear":int(bool(in_this)),
            "preElectionFiscalYear":int(not in_this and bool(future)),
            "matchedGovernorElectionId":in_this[0]["id"] if in_this else None,
            "scheduledUpcomingElectionId":future[0]["id"] if future else None,
            "fiscalStartEndVerification":"CURRENT_CONVENTION_BACKCAST_NOT_INDIVIDUALLY_VERIFIED",
            "exactElectionDateVerification":"SECONDARY_HISTORICAL_SUMMARY_NOT_STATE_CERTIFIED",
            "causalModelReady":False,
        })
    if len(rows)!=650 or len({(r["fipsState"],r["fiscalYear"]) for r in rows})!=650:
        raise ValueError("Duplicate or missing state fiscal rows")
    counts=Counter(e["electionCalendarYear"] for e in events)
    expected={2011:3,2012:11,2013:2,2014:36,2015:3,2016:12,2017:2,
              2018:36,2019:3,2020:11,2021:2,2022:36,2023:3,2024:11}
    if counts!=expected:
        raise ValueError(f"Historical governor election cohort counts differ {counts}")
    return {
        "schema":"power-atlas.gubernatorial-election-fiscal-join.v1",
        "dataStatus":"source_linked_secondary_election_calendar_plus_provisional_fiscal_clock",
        "analysisApproval":"descriptive_association_sensitivity_only_no_causal_identification",
        "sourceReferences":{"nga":SOURCE_NGA,"historicalElections":SOURCE_HISTORY,
                            "offcycle":SOURCE_OFF,"2016SpecialOregon":SOURCE_OR,
                            "2012WisconsinRecall":SOURCE_WI},
        "scope":{
            "calendarYearsDocumented":list(range(2011,2025)),
            "actualElectionEvents":len(events),
            "stateFiscalYears":len(rows),
            "2012WisconsinRecallNotRegularlyScheduled":True,
            "2016OregonSpecialExplicit":True,
            "louisianaPrimaryRunoffDatesRequireOfficialCanvassCrossCheck":True,
        },
        "treatmentInterpretation":{
            "electionDuringFiscalYear":"Decisive general election lies within current provisional FY start/end",
            "preElectionFiscalYear":"No election in current FY; a decisive election falls within the following 365 days",
            "notTheSameAsCalendarYear":"2024 November elections generally occur in FY2025, outside current FY2024 source panel",
            "louisiana":"Jungle-primary winner in 2011/2023; November runoff in 2015/2019",
            "incumbentStatusAndUnexpectedElections":"Not independently coded; no causal classification",
        },
        "elections":events,
        "records":sorted(rows,key=lambda r:(r["fipsState"],r["fiscalYear"])),
        "causalEstimates":None,
        "controlsLinked":False,
        "warnings":[
            "Historical election dates derive from independent secondary summaries, not 50 state official certified canvasses.",
            "Fiscal date boundaries remain contemporary-rule backcasts that require historical legal verification.",
            "2012 Wisconsin recall is an exceptional June election, not encoded in regular gubernatorial cycle.",
            "Inserting these indicators in a regression does not create exogenous treatment or establish intent.",
        ],
    }

def main():
    d=make()
    content=json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=content:
            raise SystemExit("Election calendar join is absent or stale")
    else:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=content:
            OUT.write_text(content,encoding="utf-8")
    print(json.dumps({"status":d["dataStatus"],"calendarEvents":len(d["elections"]),
                      "stateFiscalYears":len(d["records"]),
                      "electionFYCount":sum(r["electionDuringFiscalYear"] for r in d["records"]),
                      "preFYCount":sum(r["preElectionFiscalYear"] for r in d["records"]),
                      "causalApproved":False},indent=2))

if __name__=="__main__":
    main()
