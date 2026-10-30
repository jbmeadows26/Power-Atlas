"""Audit the feasibility of joining OECD PII to OECD trust without claiming causation.

A code-level PII observation is not a corruption conviction, impunity treatment or
administrative burden experience. This script does not fit regression models or
interpolate source years. It reports *observed* country/year/indicator coverage,
scale, missingness and the risk of outcome contamination.
"""
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PII=ROOT/"data/institutional-decay/oecd-pii-raw-2020-2025.json"
LABELS=ROOT/"data/institutional-decay/oecd-pii-measure-labels.json"
TRUST=ROOT/"data/institutional-decay/trust-country-waves-2023-2025.json"
OUT=ROOT/"data/institutional-decay/indicator-join-readiness-2026-10-30.json"

# Outcomes that are already survey trust questions MUST NOT be treated as
# independent explanations for the same outcome. This is leakage and circular.
OUTCOME_CODES={"PII_31314","PII_31315"}
SUGGESTED_RELEVANT_CODES={
    "PII_3113","PII_3116","PII_3135","PII_3137","PII_3106",
    "PII_3132","PII_3136","PII_3114","PII_3115"
}


def audit():
    pii=json.loads(PII.read_text(encoding="utf-8"))
    labeldata=json.loads(LABELS.read_text(encoding="utf-8"))
    trust=json.loads(TRUST.read_text(encoding="utf-8"))
    labels={x["code"]:x["englishLabel"] for x in labeldata["measureLabels"]}
    assert len(labels)==44
    source_rows=pii["rows"]
    distinct={r["measureCode"] for r in source_rows}
    assert set(labels)==distinct
    countries={r["countryCode"]:r for r in trust["rows"]}
    oecd2025={r["countryCode"] for r in trust["rows"]
              if r["group"]=="oecd_member" and r["nationalGovernment2025"] is not None}
    pair={r["countryCode"] for r in trust["rows"]
          if r["group"]=="oecd_member" and
          r["nationalGovernment2023"] is not None and
          r["nationalGovernment2025"] is not None}
    assert len(oecd2025)==33 and len(pair)==28
    bycode=defaultdict(list)
    for r in source_rows:
        assert r["countryIso3"] in countries
        bycode[r["measureCode"]].append(r)
    table=[]
    for code in sorted(distinct):
        rows=bycode[code]
        yearly=[]
        for year in (2020,2021,2022,2023,2024,2025):
            yr=[r for r in rows if r["referenceYear"]==year]
            year_keys={
                "year":year,
                "allRows":len(yr),
                "decimal":sum(r["valueKind"]=="numeric" for r in yr),
                "fraction":sum(r["valueKind"]=="reported_fraction" for r in yr),
                "sourceMissing":sum(r["valueKind"]=="source_missing" for r in yr),
                "observedCountries":len({r["countryIso3"] for r in yr if r["valueKind"]!="source_missing"}),
                "sameYearOECD25TrustEligibleCountries":len({r["countryIso3"] for r in yr
                    if r["valueKind"]!="source_missing" and r["countryIso3"] in oecd2025}),
                "sameYearPairedTrustEligibleCountries":len({r["countryIso3"] for r in yr
                    if r["valueKind"]!="source_missing" and r["countryIso3"] in pair}),
            }
            yearly.append(year_keys)
        item={
            "code":code,
            "officialEnglishLabel":labels[code],
            "totalRawObservations":len(rows),
            "units":sorted({str(r["unitMeasureCode"]) for r in rows}),
            "yearsWithAnyObservedValue":sorted({r["referenceYear"] for r in rows
                                                if r["valueKind"]!="source_missing"}),
            "yearCoverage":yearly,
            "containsSurveyTrustOutcome":code in OUTCOME_CODES,
            "relatedButNotDirectMeasureOfImpunity":code in SUGGESTED_RELEVANT_CODES,
            "comparableAnnualPanelEstablished":False,
            "canEnterCausalRegression":False,
        }
        table.append(item)
    if len(table)!=44:
        raise ValueError("Unexpected measure code coverage")
    result={
        "schema":"power-atlas.institutional-decay.indicator-join-readiness.v1",
        "asOf":"2026-10-30",
        "sourcePII":"data/institutional-decay/oecd-pii-raw-2020-2025.json",
        "sourceLabels":"data/institutional-decay/oecd-pii-measure-labels.json",
        "sourceTrust":"data/institutional-decay/trust-country-waves-2023-2025.json",
        "analysisGrain":"country + exact PII measure code + source reference year + unit/dimension; no imputation",
        "trustCountriesWith2025Observation":len(oecd2025),
        "trustCountriesWith2023And2025Pairs":len(pair),
        "sourceRows":len(source_rows),
        "fullyLabeledIndicators":len(table),
        "summary":{
           "indicatorsWithAny2025Observed":sum(any(x["year"]==2025 and x["observedCountries"]>0
                   for x in item["yearCoverage"]) for item in table),
           "indicatorsWithSameYear2025OECDTrustMatch":sum(any(x["year"]==2025 and
                     x["sameYearOECD25TrustEligibleCountries"]>0 for x in item["yearCoverage"])
                     for item in table),
           "indicatorsWithSameYear2023PairedTrustMatch":sum(any(x["year"]==2023 and
                     x["sameYearPairedTrustEligibleCountries"]>0 for x in item["yearCoverage"])
                     for item in table),
           "sourceReportedMissing":sum(r["valueKind"]=="source_missing" for r in source_rows),
           "sourceReportedFractions":sum(r["valueKind"]=="reported_fraction" for r in source_rows),
           "sourceNumericValues":sum(r["valueKind"]=="numeric" for r in source_rows),
           "outcomeLeakageCodes":sorted(OUTCOME_CODES),
        },
        "conclusion":"source_data_harmonization_audit_only_no_causal_model_identified",
        "cautions":[
            "OECD integrity source indicator PII_31314 (Trust in government) and PII_31315 (Trust in parliament) are themselves trust outcomes; never treat them as independent accountability predictors in trust regressions.",
            "PII indicator values represent official criterion scores or counts, not observations of a sanction after a substantiated personal violation.",
            "No administrative burden observations of individual repeated filings, elapsed case time, appeals or agency errors are included.",
            "Values for 2020/2022/2023/2024/2025 do not form a complete annual series for any arbitrary source measure; no carried-forward values.",
            "Overlapping countries and source years alone do not identify the interaction or the reverse causal feedback cycle.",
            "Reported fractions retain official numerators and denominators. Scale harmonization requires official unit definitions; ratios are not automatically 0–100 percentages.",
            "No confidence intervals, significance or causal coefficients can be inferred from this coverage report."
        ],
        "indicators":table
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result


if __name__=="__main__":
    r=audit()
    print(json.dumps({k:r[k] for k in
        ("conclusion","trustCountriesWith2025Observation",
         "trustCountriesWith2023And2025Pairs","sourceRows","fullyLabeledIndicators",
         "summary")},indent=2))
