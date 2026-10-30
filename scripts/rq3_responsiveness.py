#!/usr/bin/env python3
"""RQ3 observed-vote association pipeline: reject unverifiable income preferences.

Vote 1/0 means Yea/Nay on a RECORDED House roll call, not enactment or loyalty.
Terciles, not quartiles. A coefficient difference is association, NOT causal favoritism.
"""
import argparse,csv,datetime,json,math
from pathlib import Path
EXPECTED={"member_id","district_id","roll_id","vote_date","yea","issue",
          "p_bottom","p_middle","p_top","n_bottom","n_middle","n_top","preferences_as_of","source"}
def validate(rows,manifest):
    if manifest.get("status")!="preregistered_verified_issue_preferences" or manifest.get("congress")!=119:
        raise ValueError("Issue-specific district-income survey and preregistered selection required")
    allowed=set(manifest.get("preselectedRollIds",[]))
    if len(allowed)!=150:raise ValueError("Exactly 150 preselected votes required")
    if len(rows)<1000:raise ValueError("Insufficient observed legislator/issue data")
    if not all(EXPECTED<=r.keys() for r in rows):raise ValueError("Incomplete dyadic data")
    clean=[]; seen=set(); rollids=set(); members=set()
    for row in rows:
        if row["roll_id"] not in allowed:raise ValueError("Post hoc selected vote")
        if not row["source"].startswith("https://clerk.house.gov/evs/"):
            raise ValueError("Only verified official House XML vote sources allowed")
        vote=int(row["yea"])
        if vote not in (0,1):raise ValueError("Present/absent must be excluded, never treated as Nay")
        vote_date=datetime.date.fromisoformat(row["vote_date"])
        pref_date=datetime.date.fromisoformat(row["preferences_as_of"])
        if pref_date>vote_date:raise ValueError("Preferences measured after legislator's vote")
        key=(row["member_id"],row["roll_id"])
        if key in seen:raise ValueError("Duplicate legislator-roll pair")
        seen.add(key); members.add(row["member_id"]);rollids.add(row["roll_id"])
        p=[float(row[x]) for x in ("p_bottom","p_middle","p_top")]
        n=[int(row[x]) for x in ("n_bottom","n_middle","n_top")]
        if any(not math.isfinite(v) or not (0<=v<=1) for v in p) or min(n)<30:
            raise ValueError("Invalid preference share or insufficient subgroup effective n")
        clean.append({"member_id":row["member_id"],"district_id":row["district_id"],
                      "roll_id":row["roll_id"],"issue":row["issue"],"yea":vote,
                      "p_bottom":p[0],"p_middle":p[1],"p_top":p[2]})
    if len(rollids)!=150 or len(members)<20:
        raise ValueError("Incomplete roll-call or congressional member coverage")
    return clean

def fit(rows):
    import pandas as pd
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    df=pd.DataFrame(rows)
    result=smf.gee("yea ~ p_bottom + p_middle + p_top + C(issue)",
                    groups="member_id",data=df,family=sm.families.Binomial()).fit()
    b=result.params; covariance=result.cov_params()
    delta=float(b["p_top"]-b["p_bottom"])
    variance=float(covariance.loc["p_top","p_top"]+covariance.loc["p_bottom","p_bottom"]-2*covariance.loc["p_bottom","p_top"])
    se=math.sqrt(max(0,variance))
    return {"status":"observational_analysis_not_causal","n":len(df),"rolls":int(df["roll_id"].nunique()),
      "memberClusters":int(df["member_id"].nunique()),
      "deltaBetaTopMinusBottom":delta,"standardError":se,
      "approx95CI":[delta-1.96*se,delta+1.96*se],
      "warning":"Roll-call agenda selection, group preference collinearity and nonrandom issue inclusion prevent interpreting positive delta as proof of high-wealth preference or individual misconduct."}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--observations",type=Path,required=True)
    parser.add_argument("--selection-manifest",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if args.observations.resolve().is_relative_to(root):
        raise ValueError("Aggregate modeled output only; do not upload sensitive survey observations")
    manifest=json.loads(args.selection_manifest.read_text())
    with args.observations.open(newline="",encoding="utf-8") as stream:
        rows=list(csv.DictReader(stream))
    out=fit(validate(rows,manifest))
    args.output.write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__":main()
