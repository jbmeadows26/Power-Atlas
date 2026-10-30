#!/usr/bin/env python3
"""Observed association between electoral timing and state capital outlay.

NOT causal: gubernatorial election calendars rely partly on secondary sources;
historical fiscal-year boundary backcasts are provisional, and transfer shares
are contemporaneous/post-treatment. Econometric results are conditional
associations, not proof of deliberate electoral short-termism.

Run after generating validated source-linked join and economic controls:
  python -m scripts.analyze_state_election_association
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/fiscal/state-timeseries"
OUT=DATA/"governor-election-fiscal-associations-2012-2024.json"

def read(filename):
    return json.loads((DATA/filename).read_text(encoding="utf-8"))

def source_join():
    fisc=read("aggregate-capital-2012-2024.json")
    elections=read("governor-elections-fiscaljoin-2012-2024.json")
    econ=read("economic-controls-2012-2024.json")
    if len(fisc.get("records",[]))!=650 or len(elections.get("records",[]))!=650 or len(econ.get("records",[]))!=650:
        raise ValueError("All three input datasets must contain 650 real observations")
    if elections.get("dataStatus")!="source_linked_secondary_election_calendar_plus_provisional_fiscal_clock":
        raise ValueError("Expected provisional governor event source disclosure")
    if econ.get("researchReadiness",{}).get("causalModelReady") is not False:
        raise ValueError("Macroeconomic transfer variables cannot be pre-certified causal")
    e={r["id"]:r for r in elections["records"]}
    x={r["id"]:r for r in econ["records"]}
    if len(e)!=650 or len(x)!=650:
        raise ValueError("Duplicate state-year join")
    out=[]
    for row in fisc["records"]:
        key=row["id"]
        if key not in e or key not in x:
            raise ValueError("Unmatched source financial state-year "+key)
        event=e[key]; ctrl=x[key]
        if not (row["fipsState"]==event["fipsState"]==ctrl["fipsState"] and
                row["fiscalYear"]==event["fiscalYear"]==ctrl["fiscalYear"]):
            raise ValueError("Incorrect state or fiscal-year election/economic source join")
        if event.get("causalModelReady") is not False or ctrl["preTreatmentStatus"]["causalControlsVerified"] is not False:
            raise ValueError("Unexpected causal certification of unverified context")
        direct=row["totalsThousandsUSD"]["directExpenditure"]
        capital=row["totalsThousandsUSD"]["capitalOutlay"]
        if direct<=0 or not 0<=capital<=direct:
            raise ValueError("Invalid source official finance ratios")
        out.append({
          "state":row["fipsState"],
          "year":row["fiscalYear"],
          "capitalSharePercent":capital/direct*100,
          "electionFiscalYear":event["electionDuringFiscalYear"],
          "preElectionFiscalYear":event["preElectionFiscalYear"],
          "gdpGrowthLaggedCalendarPct":ctrl["gdpGrowthPriorAvailableCalendarYearPct"],
          "unemploymentLaggedCalendarPct":ctrl["unemploymentPriorAvailableCalendarYearPct"],
          "federalTransferShareCurrentFY":ctrl["federalTransfersShareOfCurrentGeneralRevenue"],
        })
    out.sort(key=lambda r:(r["state"],r["year"]))
    return out,fisc,elections,econ

def model(rows,name,include_macro,include_transfers,window):
    import pandas as pd
    import numpy as np
    import statsmodels.formula.api as smf
    df=pd.DataFrame.from_records(rows)
    df=df.loc[df["year"].isin(window)].copy()
    if df.empty or df["state"].nunique()!=50:
        raise ValueError("Insufficient states for model "+name)
    vars=["electionFiscalYear","preElectionFiscalYear"]
    if include_macro:
        vars+=["gdpGrowthLaggedCalendarPct","unemploymentLaggedCalendarPct"]
    if include_transfers:
        vars+=["federalTransferShareCurrentFY"]
    if not np.isfinite(df[vars+["capitalSharePercent"]].to_numpy(dtype=float)).all():
        raise ValueError("Non-finite observations in "+name)
    form="capitalSharePercent ~ "+" + ".join(vars)+" + C(state) + C(year)"
    reg=smf.ols(form,df)
    if np.linalg.matrix_rank(reg.exog)!=reg.exog.shape[1]:
        raise ValueError("Treatment contrast not identified with fixed effects: "+name)
    fit=reg.fit(cov_type="cluster",cov_kwds={"groups":df["state"],"use_correction":True})
    effects={}
    for term in ("electionFiscalYear","preElectionFiscalYear"):
        ci=fit.conf_int().loc[term]
        effects[term]={
           "associationInPercentagePoints":round(float(fit.params[term]),6),
           "stateClusteredSE":round(float(fit.bse[term]),6),
           "ci95":[round(float(ci.iloc[0]),6),round(float(ci.iloc[1]),6)],
           "twoSidedPValue":round(float(fit.pvalues[term]),8),
           "causalEffect":None
        }
    return {
        "name":name,"sampleYears":sorted(df["year"].unique().tolist()),
        "nObservedStateYears":int(len(df)),"stateCount":int(df["state"].nunique()),
        "hasMacroLaggedControls":include_macro,"hasPotentiallyPostTreatmentFederalTransferShare":include_transfers,
        "formula":form,"standardErrors":"state_clustered_with_small_sample_correction",
        "coefficients":effects,
        "interpretation":"OBSERVATIONAL_ASSOCIATION_ONLY_NO_RANDOM_ASSIGNMENT_NO_INTENT_INFERENCE",
    }

def analyze():
    rows,fisc,election,econ=source_join()
    variants=[
        ("all_fy_unadjusted",False,False,list(range(2012,2025))),
        ("all_fy_lagged_macro",True,False,list(range(2012,2025))),
        ("all_fy_macro_plus_contemporaneous_transfers_sensitivity",True,True,list(range(2012,2025))),
        ("pre_2022_unadjusted",False,False,list(range(2012,2022))),
        ("pre_2022_lagged_macro",True,False,list(range(2012,2022))),
        ("exclude_pandemic_fy2020_2021_macro",True,False,[y for y in range(2012,2025) if y not in (2020,2021)]),
    ]
    results=[model(rows,name,macro,transfer,years) for name,macro,transfer,years in variants]
    years={}
    for yr in range(2012,2025):
        selected=[r for r in rows if r["year"]==yr]
        years[str(yr)]={
            "stateYears":len(selected),
            "governorElectionInFY":sum(r["electionFiscalYear"] for r in selected),
            "preGovernorElectionFY":sum(r["preElectionFiscalYear"] for r in selected),
        }
    return {
        "schema":"power-atlas.observed-state-election-associations.v1",
        "status":"observational_diagnostics_not_verified_causal_effect",
        "sourceScope":"US Census fiscal 2012-2024, source-linked secondary governor election summaries, BEA real GDP and BLS unemployment via FRED",
        "asOf":"2026-10-30",
        "sourceRecordCount":len(rows),
        "sourceLinks":{
            "finance":"data/fiscal/state-timeseries/aggregate-capital-2012-2024.json",
            "governorElections":"data/fiscal/state-timeseries/governor-elections-fiscaljoin-2012-2024.json",
            "economy":"data/fiscal/state-timeseries/economic-controls-2012-2024.json",
        },
        "electionWindowCountsByFiscalYear":years,
        "models":results,
        "causalEffect":None,
        "politicalIntentInference":None,
        "criticalUnresolved":[
            "Historical state fiscal-year dates are a contemporary-rule backcast rather than a state-by-state verified statute for each year",
            "Governor election dates from National Governors Association and Ballotpedia summaries are not state-certified election canvasses",
            "Different treatment contexts: two-year cycles, Oregon 2016 special election, and Wisconsin 2012 recall excluded",
            "National FY2022 Census codebook changes and heterogeneous accounting may bias cross-regime comparisons",
            "Federal transfers recorded in current fiscal year can be mediator/post-treatment",
            "GDP and unemployment lagged calendar year data have not been vintage-pinned to what was public before budget adoption",
            "Within-state calendar variation is not independent of policy timing, incumbent strength, legislative agenda, term limits, and regional shocks",
            "No administrative spending announcements, commitments, obligations or completed infrastructure measures",
            "No validation of pre-event parallel trends, placebos, effective heterogeneous estimates or spillovers",
        ],
        "publicationWarning":"These numerical coefficients are real-data observational associations, not validated election-caused investment changes, and do not establish politician deception.",
    }

def main():
    results=analyze()
    content=json.dumps(results,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=content:
            raise SystemExit("Observed association file missing or stale")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=content:
            OUT.write_text(content,encoding="utf-8")
    print(json.dumps({"status":results["status"],"models":[{"name":m["name"],
        "states":m["stateCount"],"n":m["nObservedStateYears"],
        "coefficients":m["coefficients"]} for m in results["models"]],
        "causalClaim":results["causalEffect"]},indent=2))

if __name__=="__main__":
    main()
