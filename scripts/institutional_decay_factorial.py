"""Pre-registered 2x2 factorial analysis for REAL de-identified survey outcomes.

No respondents have been recruited and this script contains NO observed results.
Expected CSV: impunity,high_burden,trust_score (0/1 factors; trust 1..7).
The saturated 2x2 OLS interaction equals (mean11-mean10)-(mean01-mean00).
HC3 SE is computed using cell-specific leverages 1/n; normal CI is descriptive
unless a valid design, actual randomization and attrition assumptions are met.
"""
import argparse
import csv
import json
import math
from pathlib import Path

TARGET_N = 3000


def analyze(rows):
    cells = {(a,b): [] for a in (0,1) for b in (0,1)}
    assigned = {k:0 for k in cells}
    for row in rows:
        try:
            a = int(row["impunity"]); b = int(row["high_burden"])
        except (KeyError,TypeError,ValueError) as e:
            raise ValueError("Both treatment factors must be recorded as 0/1") from e
        if (a,b) not in cells:
            raise ValueError("Treatments must be 0 or 1")
        assigned[(a,b)] += 1
        v = row.get("trust_score", "")
        if v is None or str(v).strip()=="":
            continue
        try:
            score=float(v)
        except ValueError as e:
            raise ValueError("trust_score must be numeric") from e
        if not math.isfinite(score) or not 1<=score<=7:
            raise ValueError("Trust score outside 1–7 scale")
        cells[(a,b)].append(score)
    if min(len(v) for v in cells.values())<10:
        raise ValueError("Insufficient completed responses in one or more cells")
    mu={k:sum(v)/len(v) for k,v in cells.items()}
    b0=mu[(0,0)]
    b1=mu[(1,0)]-mu[(0,0)]
    b2=mu[(0,1)]-mu[(0,0)]
    b3=mu[(1,1)]-mu[(1,0)]-mu[(0,1)]+mu[(0,0)]
    # The exact HC3 sandwich variance for a saturated 2x2 OLS interaction:
    # sum of squared within-cell deviations / (n_cell - 1)^2.
    var_hc3=sum(sum((v-mu[k])**2 for v in arr)/(len(arr)-1)**2
                for k,arr in cells.items())
    se=math.sqrt(var_hc3)
    z=b3/se if se>0 else None
    p=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None
    report={
        "schema":"power-atlas.institutional-decay.factorial-analysis.v1",
        "status":"observed_input_analysis_requires_fieldwork_and_randomization_verification",
        "treatmentCoding":{"impunity":1,"highBurden":1,"accountable":0,"lowBurden":0},
        "cells":{
            str(k[0])+str(k[1]):{
                "assigned":assigned[k],"completed":len(cells[k]),
                "missing":assigned[k]-len(cells[k]),"meanTrust":round(mu[k],6)
            } for k in cells
        },
        "olsCoefficients":{"intercept":b0,"impunityMainEffect":b1,
                           "burdenMainEffect":b2,"compoundingInteraction":b3},
        "hc3InteractionSE":se,"interaction95PctNormalCI":[b3-1.96*se,b3+1.96*se],
        "interactionTwoSidedNormalP":p,
        "assignedTotal":sum(assigned.values()),
        "completeTotal":sum(len(v) for v in cells.values()),
        "plannedSample":TARGET_N,
        "interpretation":"Negative interaction supports a stronger burden effect in impunity condition under randomized assignment; no claim beyond vignette, fielded sample or follow-up time.",
        "limitations":"No covariate adjustment, weights, cluster structure, attrition correction or actual representative sampling is assumed. A significant p-value alone is not proof of external validity.",
    }
    return report


def run_file(path):
    with Path(path).open(encoding="utf-8",newline="") as f:
        return analyze(list(csv.DictReader(f)))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,help="Actual de-identified survey CSV")
    args=parser.parse_args()
    if not args.input:
        print(json.dumps({"status":"not_fielded","plannedSample":TARGET_N,
                          "message":"Supply independently recruited and randomized 2x2 data with --input. No experiment results exist."},indent=2))
    else:
        print(json.dumps(run_file(args.input),indent=2))
