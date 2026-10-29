#!/usr/bin/env python3
"""Attach a documented *provisional* fiscal-year clock to official Census data.

The NCSL/KFF cited fiscal-year start conventions are current as of 2025/2026.
Their historical constancy for EACH FY2012–2024 has NOT been individually
verified. Therefore this derived crosswalk is not a confirmed treatment-
assignment dataset; it cannot be used for causal election-cycle estimation.
"""
import calendar
import datetime as dt
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/fiscal/state-timeseries/aggregate-capital-2012-2024.json"
OUT=ROOT/"data/fiscal/state-timeseries/fiscal-calendar-template-2012-2024.json"
EXCEPTIONS={
    "01":10, # Alabama
    "26":10, # Michigan
    "36":4,  # New York
    "48":9,  # Texas
}
SOURCE={
 "ncsl":"https://www.ncsl.org/fiscal/fy-2026-state-budget-status",
 "kff":"https://www.kff.org/state-health-policy-data/state-indicator/total-state-spending/",
}
def read():
    return json.loads(SRC.read_text(encoding="utf-8"))

def make():
    d=read()
    if d["coverage"].get("stateYearObservations")!=650 or d.get("electionClockAttached") is not False:
        raise ValueError("Modern state-finance source incomplete or already modified")
    output=[]
    seen=set()
    for r in d["records"]:
        fips=r["fipsState"]
        year=r["fiscalYear"]
        if not (isinstance(year,int) and 2012<=year<=2024 and isinstance(fips,str) and len(fips)==2):
            raise ValueError("Invalid source identity or year")
        key=(fips,year)
        if key in seen:
            raise ValueError("Duplicated state fiscal year")
        seen.add(key)
        start_month=EXCEPTIONS.get(fips,7)
        start=dt.date(year-1,start_month,1)
        end_month=(start_month-2)%12+1
        end_year=year if end_month<start_month else year-1
        end_day=calendar.monthrange(end_year,end_month)[1]
        end=dt.date(end_year,end_month,end_day)
        if (end-start).days not in (364,365):
            raise ValueError(f"Unexpected fiscal-year span for {key}")
        output.append({
            "id":r["id"],"state":r["state"],"fipsState":fips,"fiscalYearLabel":year,
            "fiscalStartDate":start.isoformat(),"fiscalEndDate":end.isoformat(),
            "fiscalStartMonth":start_month,"sourceDataId":r["id"],
            "historicalVerification":"provisional_calendar_template_not_independently_confirmed_for_this_fiscal_year",
            "electionDate":None,"electionExposureFraction":None,
            "electoralTreatmentAssignmentStatus":"not_approved",
        })
    output.sort(key=lambda x:(x["fipsState"],x["fiscalYearLabel"]))
    return {
        "schema":"power-atlas.us-state-fiscal-calendar-template.v1",
        "publicationStatus":"provisional_current_convention_backcast_not_historical_election_clock",
        "sourceCoverage":{"observations":len(output),"years":list(range(2012,2025)),"statesPerYear":50},
        "conventions":{
            "defaultMonth":7,
            "exceptionStartMonthsByFIPS":EXCEPTIONS,
            "references":SOURCE,
            "historicalCoverageWarning":"Current 2025/2026 fiscal-year conventions backcast to earlier fiscal-year labels; confirm state legal fiscal boundaries historically and detect exceptions before causal modeling.",
        },
        "electionDateData":None,
        "modelReadiness":"blocked_pending_historical_fiscal_start_validation_and_election_date_join",
        "records":output,
    }

def main():
    doc=make()
    encoded=json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+"\n"
    if "--check" in sys.argv[1:]:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=encoded:
            raise SystemExit("Fiscal-year clock template stale or missing")
    else:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=encoded:
            OUT.write_text(encoded,encoding="utf-8")
    print(json.dumps({"status":doc["publicationStatus"],"rows":len(doc["records"]),
                      "electionDateData":doc["electionDateData"]},indent=2))

if __name__=="__main__":
    main()
