#!/usr/bin/env python3
"""Election-calendar TWFE *architecture* with an explicit empirical release gate.

Use:
  python -m scripts.estimate_electoral_twfe --simulate
  python -m scripts.estimate_electoral_twfe --real --covariates path/to/independently_verified_data.json

The --simulate mode uses fully synthetic data to exercise statsmodels and
says so on stdout. Never publish those coefficients as Power Atlas findings.

The --real mode only accepts complete source-cited, historically verified
election/fiscal windows and pre-budget economic controls. Even when it runs,
TWFE describes a conditional association, not an identified causal effect.
"""
import argparse
import datetime as dt
import json
import math
import random
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
FISCAL=ROOT/"data/fiscal/state-timeseries/aggregate-capital-2012-2024.json"
REAL_REQUIRED_FIELDS=(
    "stateFips","fiscalYear","electionFiscalYear","preElectionFiscalYear",
    "gdpGrowthPriorYear","unemploymentRatePriorYear","federalTransferSharePriorYear",
    "electionDateEvidenceUrl","fiscalBoundaryLawUrl","gdpEvidenceUrl",
    "unemploymentEvidenceUrl","federalTransferEvidenceUrl",
    "historicalFiscalBoundaryVerified","governorElectionDatesVerified",
    "preTreatmentControlsVerified",
)
PRE_TREATMENT_VARS=("gdpGrowthPriorYear","unemploymentRatePriorYear","federalTransferSharePriorYear")
X_VARS=("electionFiscalYear","preElectionFiscalYear")+PRE_TREATMENT_VARS
MIN_STATES=40
CONTROL_SOURCE_STATUS="verified_official_historical"


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _https(url):
    if not isinstance(url,str):
        return False
    z=urlsplit(url)
    return z.scheme=="https" and bool(z.hostname) and not z.username and not z.password


def _finite_number(val):
    # bool is not a valid numerical covariate despite subclassing int
    return type(val) in (int,float) and math.isfinite(val)


def build_real_panel(covariates_path, fiscal_path=FISCAL):
    """Join exact 650 official state-year ratios to genuine, independently verified treatment data."""
    if not Path(covariates_path).exists():
        raise ValueError("NO_ELECTION_CONTROLS: verified historical election/fiscal/BEA/BLS/transfer dataset not yet present")
    f=_read(fiscal_path)
    c=_read(covariates_path)
    if f.get("schema")!="power-atlas.census-state-finance-aggregates.v1":
        raise ValueError("Unrecognized Census panel; cannot infer source amounts")
    expected_sha="888dfbb3f8eeebce01b409e4e86178ac04c596c7fc355047beef2433a9b5be48"
    if f.get("source",{}).get("sha256OriginalBytes")!=expected_sha:
        raise ValueError("Official Census archive SHA changed; independently revalidate")
    records=f.get("records",[])
    if len(records)!=650:
        raise ValueError("Expected 650 official state fiscal rows")
    if c.get("schema")!="power-atlas.verified-governor-fiscal-controls.v1":
        raise ValueError("Unrecognized real covariate schema")
    if c.get("sourceStatus")!=CONTROL_SOURCE_STATUS or c.get("samplingFrame")!="50-states-FY2012-2024":
        raise ValueError("Election and fiscal source must be independently verified, not assumed")
    if c.get("synthetic") is not False:
        raise ValueError("Simulated election data cannot enter real model")
    raw=c.get("records",[])
    if len(raw)!=650:
        raise ValueError("Unverified missing state-year election/covariate observations")
    index={}
    for i,r in enumerate(raw):
        if not isinstance(r,dict) or not all(k in r for k in REAL_REQUIRED_FIELDS):
            raise ValueError(f"Missing required official source, date or covariate in row {i}")
        if not (isinstance(r["stateFips"],str) and len(r["stateFips"])==2 and
                type(r["fiscalYear"]) is int):
            raise ValueError(f"Invalid FIPS or fiscal year row {i}")
        key=(r["stateFips"],r["fiscalYear"])
        if key in index:
            raise ValueError(f"Duplicate state fiscal-year key {key}")
        for v in ("electionFiscalYear","preElectionFiscalYear"):
            if type(r[v]) is not int or r[v] not in (0,1):
                raise ValueError(f"Unverified election exposure {key}:{v}")
        if r["electionFiscalYear"] and r["preElectionFiscalYear"]:
            raise ValueError(f"Mutually exclusive election and pre-election exposures {key}")
        for v in PRE_TREATMENT_VARS:
            if not _finite_number(r[v]):
                raise ValueError(f"Missing/nonfinite macroeconomic control: {key}:{v}")
        if not (-50<r["gdpGrowthPriorYear"]<100 and 0<=r["unemploymentRatePriorYear"]<=50 and
                0<=r["federalTransferSharePriorYear"]<=1):
            raise ValueError(f"Economic control out of reasonable expected scale: {key}")
        for v in ("electionDateEvidenceUrl","fiscalBoundaryLawUrl","gdpEvidenceUrl",
                  "unemploymentEvidenceUrl","federalTransferEvidenceUrl"):
            if not _https(r[v]):
                raise ValueError(f"Independent source URL missing/unsafe: {key}:{v}")
        for v in ("historicalFiscalBoundaryVerified","governorElectionDatesVerified","preTreatmentControlsVerified"):
            if r[v] is not True:
                raise ValueError(f"Unverified historical fiscal/election timing or controls: {key}:{v}")
        index[key]=r
    out=[]
    for row in records:
        key=(row["fipsState"],row["fiscalYear"])
        if key not in index:
            raise ValueError(f"Missing official election/control join for state fiscal year {key}")
        q=index[key]
        v=row["totalsThousandsUSD"]
        direct=v["directExpenditure"]
        capital=v["capitalOutlay"]
        if not direct>0 or not 0<=capital<=direct:
            raise ValueError(f"Invalid official capital/direct totals {key}")
        out.append({
            "state":row["fipsState"],
            "year":row["fiscalYear"],
            # percentage-point units to avoid accidentally interpreting beta as a fraction
            "capitalSharePercent":100*capital/direct,
            **{k:q[k] for k in X_VARS},
        })
    if len(set((x["state"],x["year"]) for x in out))!=650:
        raise ValueError("Real state-year join has duplicates")
    return out


def generate_synthetic(seed=20261029):
    """Construct a synthetic 50x13 panel with known treatment effects for unit tests only."""
    rng=random.Random(seed)
    out=[]
    base={f"S{i:02d}":rng.gauss(0,0.7) for i in range(50)}
    for i in range(50):
        state=f"S{i:02d}"  # NOT actual U.S. state IDs
        phase=i%4
        cycle=2 if i in (0,1) else 4
        for yr in range(2012,2025):
            election=int((yr-2012)%cycle == (phase%cycle))
            pre=int(not election and (yr+1-2012)%cycle == (phase%cycle))
            gdp=2.2+0.03*(yr-2012)+rng.gauss(0,0.75)
            unemployed=5.0+0.2*(yr-2012==8)+rng.gauss(0,0.55)
            transfers=0.2+0.04*(yr-2012 in (8,9))+rng.gauss(0,0.01)
            # Structural beta elected = -1.50 pp, pre = -0.70 pp.
            y=(9.0+base[state]+0.04*(yr-2012)-1.5*election-0.70*pre
               +0.14*gdp-0.08*unemployed+1.8*transfers+rng.gauss(0,0.08))
            out.append({
                "state":state,"year":yr,"capitalSharePercent":y,
                "electionFiscalYear":election,"preElectionFiscalYear":pre,
                "gdpGrowthPriorYear":gdp,"unemploymentRatePriorYear":unemployed,
                "federalTransferSharePriorYear":transfers,
            })
    return out


def fit_twfe(rows, *, source_kind):
    """Fit a conventional TWFE conditional association with state-clustered SE."""
    if source_kind not in ("synthetic_architecture_test","source_verified_observational"):
        raise ValueError("Refuse unlabeled/fabricated empirical source")
    # Import only on regression paths, not when validating other repository files.
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf
    frame=pd.DataFrame.from_records(rows)
    required={"state","year","capitalSharePercent",*X_VARS}
    if len(frame)<100 or not required.issubset(frame.columns):
        raise ValueError("Missing panel observations or model regressors")
    if frame[["state","year"]].duplicated().any():
        raise ValueError("Duplicate panel state/year")
    states=frame["state"].nunique()
    years=frame["year"].nunique()
    if states<MIN_STATES or years<8:
        raise ValueError("Insufficient state/year variation for clustered panel model")
    if frame[list(required-{"state","year"})].isna().any().any():
        raise ValueError("No missing covariates allowed: explicit complete-case selection needed")
    for field in ("electionFiscalYear","preElectionFiscalYear"):
        if not frame[field].isin((0,1)).all():
            raise ValueError("Exposure indicators must be binary")
        if not 0<frame[field].sum()<len(frame):
            raise ValueError("No comparison group for election/pre-election indicator")
        if frame.groupby("state")[field].nunique().min()<2:
            raise ValueError("Insufficient within-state variation to identify election timing")
    if (frame["electionFiscalYear"]+frame["preElectionFiscalYear"]>1).any():
        raise ValueError("Mutually exclusive election windows violated")
    if not np.isfinite(frame[list(X_VARS)+["capitalSharePercent"]].to_numpy(dtype=float)).all():
        raise ValueError("Non-finite inputs")
    formula=("capitalSharePercent ~ electionFiscalYear + preElectionFiscalYear"
             " + gdpGrowthPriorYear + unemploymentRatePriorYear + federalTransferSharePriorYear"
             " + C(state) + C(year)")
    raw=smf.ols(formula,frame)
    if np.linalg.matrix_rank(raw.exog)<raw.exog.shape[1]:
        raise ValueError("TWFE design matrix rank-deficient: treatment or control not identified")
    fit=raw.fit(cov_type="cluster",cov_kwds={"groups":frame["state"],"use_correction":True})
    out={}
    for field in ("electionFiscalYear","preElectionFiscalYear"):
        ci=fit.conf_int().loc[field]
        out[field]={
            "estimatePercentagePoints":round(float(fit.params[field]),6),
            "clusteredStdError":round(float(fit.bse[field]),6),
            "ci95":[round(float(ci.iloc[0]),6),round(float(ci.iloc[1]),6)],
            "pValue":round(float(fit.pvalues[field]),8),
        }
    return {
        "schema":"power-atlas.electoral-twfe-architecture-result.v1",
        "dataProvenance":source_kind,
        "sourceObservations":len(frame),
        "states":states,
        "fiscalYears":years,
        "formula":formula,
        "errors":"clustered_by_state_with_small_sample_correction",
        "effects":out,
        "causalIdentification":"NOT_ESTABLISHED",
        "disclosure":("SIMULATION — estimates recover deliberately inserted coefficients and cannot be "
                      "generalized to real elections." if source_kind=="synthetic_architecture_test"
                      else "REAL CENSUS + VERIFIED CALENDAR: conditional association only; timing endogeneity, "
                           "fiscal classification and pre-trend diagnostics still prevent automatic causal claims."),
        "noSimulatedDataInResearchFeed":True,
    }


def main(argv=None):
    args=argparse.ArgumentParser()
    mode=args.add_mutually_exclusive_group(required=True)
    mode.add_argument("--simulate",action="store_true")
    mode.add_argument("--real",action="store_true")
    args.add_argument("--covariates",type=Path,default=ROOT/"data/fiscal/state-timeseries/verified-election-controls.json")
    opt=args.parse_args(argv)
    try:
        if opt.simulate:
            result=fit_twfe(generate_synthetic(),source_kind="synthetic_architecture_test")
        else:
            result=fit_twfe(build_real_panel(opt.covariates),source_kind="source_verified_observational")
    except (ValueError,FileNotFoundError) as exc:
        print("RELEASE_GATE_BLOCKED: "+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    sys.exit(main())
