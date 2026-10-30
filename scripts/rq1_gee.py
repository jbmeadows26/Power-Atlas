#!/usr/bin/env python3
"""Run an observational, weighted district-cluster GEE *only* on reviewed survey microdata.

No ZIP+4 linkage, respondent exports, fabricated columns, or automatic human inference.
This GEE is an alternative to mixed-effects logistic regression, not the same estimator.
"""
import argparse,csv,json,math
from pathlib import Path

EXPECTED={"district_id","efficacy_v242200","weight","income_percentile","age",
          "member_sfi","partisan_lean","incumbent_tenure","party_match"}
FORBIDDEN={"zip4","zip_plus4","full_address","street_address","respondent_name","email","phone"}
def check(rows,manifest):
    if manifest.get("status")!="reviewed_licensed_microdata" or manifest.get("congress")!=119:
        raise ValueError("Reviewed access/119th district-year mapping manifest required")
    if manifest.get("geoBasis")!="released_congressional_district":
        raise ValueError("Cannot reconstruct respondent identity from ZIP+4, ZIP, or street address")
    if manifest.get("weightsValidated") is not True or manifest.get("sfiCalibrationApproved") is not True:
        raise ValueError("Survey weights and socioeconomic calibration not approved")
    if len(rows)<400:raise ValueError("Insufficient surveyed respondents for descriptive linkage")
    if not all(EXPECTED<=r.keys() for r in rows):raise ValueError("Missing reviewed required columns")
    if any(FORBIDDEN.intersection(r) for r in rows):raise ValueError("Sensitive personal geography cannot be loaded")
    districts=set()
    valid=[]
    for r in rows:
        if not r["district_id"]:raise ValueError("Missing congressional district")
        try:
            code=int(r["efficacy_v242200"])
            w=float(r["weight"])
            p=float(r["income_percentile"])
            age=float(r["age"])
            sfi=float(r["member_sfi"])
            lean=float(r["partisan_lean"])
            tenure=float(r["incumbent_tenure"])
            match=float(r["party_match"])
        except (ValueError,TypeError) as exc:raise ValueError("Unvalidated survey value") from exc
        if code not in (1,2,3,4,5):
            raise ValueError("Pre-filter ANES nonresponse codes using the actual released codebook")
        if any(not math.isfinite(x) for x in (w,p,age,sfi,lean,tenure,match)):
            raise ValueError("Nonfinite survey input")
        if not (0<w<=10000 and 0<=p<=1 and age>=18 and 0<=sfi<=1 and -1<=lean<=1 and tenure>=0 and match in (0,1)):
            raise ValueError("Invalid range in survey or legislative covariate")
        districts.add(r["district_id"])
        valid.append({"district_id":r["district_id"],"alienated":int(code in (1,2)),
          "weight":w,"income_percentile":p,"age":age,"member_sfi":sfi,
          "partisan_lean":lean,"incumbent_tenure":tenure,"party_match":match})
    if len(districts)<30:raise ValueError("Too few district clusters")
    if len({r["member_sfi"] for r in valid})<5:
        raise ValueError("No adequate between-district SFI variation")
    for d in districts:
        xs={r["member_sfi"] for r in valid if r["district_id"]==d}
        if len(xs)!=1:raise ValueError("SFI member mapping inconsistent within district")
    return valid
def fit(rows):
    import pandas as pd
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    frame=pd.DataFrame(rows)
    model=smf.gee("alienated ~ member_sfi*income_percentile + age + partisan_lean + incumbent_tenure + party_match",
                 groups="district_id",data=frame,family=sm.families.Binomial(),
                 cov_struct=sm.cov_struct.Exchangeable(),weights=frame["weight"])
    result=model.fit()
    return {"model":"observational_weighted_district_GEE_not_multilevel",
      "n":len(rows),"districtClusters":frame["district_id"].nunique(),
      "parameters":{k:float(v) for k,v in result.params.to_dict().items()},
      "standardErrors":{k:float(v) for k,v in result.bse.to_dict().items()},
      "warning":"Associations, not causes. Weight assumptions, survey-design properties, district geography and calibrations require independent review."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text())
    if args.data.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("Do not store respondent microdata in the public repository")
    with args.data.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    valid=check(rows,manifest)
    result=fit(valid)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
