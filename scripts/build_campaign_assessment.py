#!/usr/bin/env python3
"""Publish the final *evidence assessment*, not unsupported causal estimates.

The assessment is complete as an audit; the underlying promise census and
election-cycle causal estimation remain research-incomplete. It reads only
previously published official, provenance-tracked source-derived files.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROMISES=ROOT/"data/promises"
FISCAL=ROOT/"data/fiscal"
OUT=PROMISES/"assessment-2026-10-29.json"
AS_OF="2026-10-29"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check(expr, message):
    if not expr:
        raise ValueError(message)

def make():
    pilot=read(PROMISES/"us-2020-pilot.json")
    extra=read(PROMISES/"us-2020-source-verified-expansion.json")
    queue=read(PROMISES/"us-2020-review-queue.json")
    registry=read(PROMISES/"source-registry.json")
    modern=read(FISCAL/"state-timeseries/aggregate-capital-2012-2024.json")
    historical=read(FISCAL/"state-legacy/quality-audit.json")
    clock=read(FISCAL/"state-timeseries/fiscal-calendar-template-2012-2024.json")
    feed=read(PROMISES/"research-feed.json")

    cases=pilot["records"]+extra["records"]
    check(len(cases)==8 and len({c["id"] for c in cases})==8, "Expected exactly 8 unique pilot cases")
    check(all(c["codingStatus"]=="provisional_source_checked" and c["reviewerCount"]==1 for c in cases),
          "Provisional singly reviewed pledge cases must not be presented as adjudicated")
    check(len(queue["records"])==24 and all(c.get("outcome") is None for c in queue["records"]),
          "Unreviewed queue missing, changed, or falsely adjudicated")
    check(queue.get("denominatorFrozen") is False,"The study does not yet have a frozen pledge denominator")
    check(len(set(c["id"] for c in cases+queue["records"]))==32,"Duplicate cases in pledged and queued sets")
    check(feed["inference"].get("promiseFulfillmentRate") is None,
          "Live promise feed unexpectedly publishes a nonrepresentative rate")
    check(modern["coverage"]["stateYearObservations"]==650 and len(modern["records"])==650,
          "Modern state fiscal coverage must contain precisely 650 observations")
    check(modern["coverage"]["officialAggregateRowsRetained"]==3250,
          "Expected 3,250 officially defined finance aggregates")
    check(modern["source"]["units"]=="thousands_of_USD","Reported monetary units changed")
    check(historical["totalRawCapitalFamilyRecords"]==65554,"Historical raw code rows no longer match audit")
    check(historical["totalPublishedMissingValueMarkers"]==66,"Historical missingness changed")
    check(historical["nonadditiveCharacterCodes"]["forbidNaiveFPlusGPlusK"] is True,
          "Nested historical equipment category must never be added twice")
    check(modern["causalEstimates"] is None and modern["electoralShortTermismModel"] is None,
          "Unadjudicated causal model is unexpectedly reported")
    check(len(clock["records"])==650 and clock["electionDateData"] is None
          and all(r["electoralTreatmentAssignmentStatus"]=="not_approved" for r in clock["records"]),
          "Election calendar remains provisional and cannot support treatment assignment")
    check(len(registry["sources"])==19 and registry["sourceCount"]==19,"Source catalog size changed")
    statuses=Counter(c["outcome"] for c in cases)
    check(statuses=={"fully_enacted":7,"attempted_not_enacted":1},
          "Pilot case statuses changed; independently adjudicate before reassessment")

    year_stats=[]
    for year in range(2012,2025):
        annual=[r for r in modern["records"] if r["fiscalYear"]==year]
        check(len(annual)==50 and len({r["fipsState"] for r in annual})==50,
              f"2012–24 state-year sample incomplete at {year}")
        bps=[r["capitalOutlayShareOfDirectExpenditureBasisPoints"] for r in annual]
        direct=sum(r["totalsThousandsUSD"]["directExpenditure"] for r in annual)
        capital=sum(r["totalsThousandsUSD"]["capitalOutlay"] for r in annual)
        check(direct>0 and capital>=0 and all(0<=x<=10000 for x in bps),
              f"Invalid state finance year {year}")
        year_stats.append({
            "fiscalYear":year,
            "observations":50,
            "meanOf50StateCapitalOutlaySharesPct":round(sum(bps)/len(bps)/100,2),
            "pooledCapitalOutlaySharePct":round(capital/direct*100,2),
            "regime":"pre_2022" if year<=2021 else "post_2022_reclassified",
            "interpretation":"descriptive_ratio_not_election_effect"
        })

    by_year={row["fiscalYear"]:row for row in year_stats}
    check(by_year[2012]["meanOf50StateCapitalOutlaySharesPct"]==8.67
          and by_year[2021]["meanOf50StateCapitalOutlaySharesPct"]==6.83
          and by_year[2022]["meanOf50StateCapitalOutlaySharesPct"]==7.81
          and by_year[2024]["meanOf50StateCapitalOutlaySharesPct"]==9.22,
          "Recomputed annual fiscal summaries diverge from previously verified research")
    old_cycle=feed["coverage"].get("fiscalSeriesObservations")
    historical_breaks={b["year"]:b["status"] for b in historical["knownBreaks"]}
    check(historical_breaks.get(2022)=="verified_documented_break","2022 coding break missing")
    stale_registry=any(s["id"]=="US-CENSUS-ASFIN-BULK" and s["recordCountIngested"]==0 for s in registry["sources"])
    return {
        "schema":"power-atlas.campaign-promises-final-evidence-assessment.v1",
        "assessmentDate":AS_OF,
        "completionStatus":"evidence_assessment_complete_primary_research_not_ready_for_causal_claims",
        "researchQuestions":{
            "pledgeFulfillment":{
                "verdict":"not_estimable_from_local_nonrandom_provisional_pilot",
                "observedProvisionalPilotCases":len(cases),
                "provisionalFullyEnactedCases":statuses["fully_enacted"],
                "provisionalAttemptedNotEnactedCases":statuses["attempted_not_enacted"],
                "provisionalOutcomeCounts":dict(sorted(statuses.items())),
                "unscoredCandidateRows":len(queue["records"]),
                "independentlyDualAdjudicatedCases":sum(1 for r in cases if r["codingStatus"]=="adjudicated" and r["reviewerCount"]>=2),
                "frozenPopulationDenominator":False,
                "overallPledgeFulfillmentRate":None,
                "confidenceInterval":None,
                "warning":"Seven of eight deliberately selected and singly reviewed examples cannot be extrapolated to the 2020 administration, an electorate, or any party. Unscored rows are NOT failed pledges."
            },
            "electoralShortTermism":{
                "verdict":"descriptive_state_finance_ready_election_cycle_causal_effect_unestimated",
                "modernFiscalYears":13,
                "modernStateYears":len(modern["records"]),
                "officialFinanceAggregateRows":modern["coverage"]["officialAggregateRowsRetained"],
                "capitalOutlayRatio":"official SF0178 direct capital outlay divided by official SF0175 total direct expenditure",
                "ratioPercentagesByFiscalYear":year_stats,
                "sampleOf50StateMeanTrend2012to2021Pp":round(by_year[2021]["meanOf50StateCapitalOutlaySharesPct"]-by_year[2012]["meanOf50StateCapitalOutlaySharesPct"],2),
                "sampleOf50StateMeanTrend2022to2024Pp":round(by_year[2024]["meanOf50StateCapitalOutlaySharesPct"]-by_year[2022]["meanOf50StateCapitalOutlaySharesPct"],2),
                "cross2022Comparability":"blocked_by_documented_census_classification_and_social_insurance_change",
                "gubernatorialElectionsMatched":False,
                "verifiedHistoricalFiscalBoundaries":False,
                "calendarTemplateRowsProvisional":len(clock["records"]),
                "electoralTreatmentEffects":None,
                "causalConfidenceInterval":None,
                "warnings":[
                    "Annual financial records cannot identify a within-year spending spike by month.",
                    "Election-related shifts require official poll dates, governors and institutional controls.",
                    "Visible transfers, spending announcements and project return-on-investment are not measured by the capital-outlay proxy.",
                    "2012–21 and 2022–24 comparisons are separately descriptive, not a causal election-cycle test.",
                    "Equal-weighted state averages are not identical to pooled expenditure-weighted shares."
                ]
            }
        },
        "historicalSourceAudit":{
            "years":len(historical["sourceYears"]),
            "rawCapitalCodeRows":historical["totalRawCapitalFamilyRecords"],
            "explicitMissingValueMarkers":historical["totalPublishedMissingValueMarkers"],
            "GandKMayOverlap":True,
            "categoryBreaks":historical["knownBreaks"],
            "cannotCombineWithModernWithoutYearSpecificCodebook":True
        },
        "studyReadiness":{
            "pledgeSourceLinkedCases":"available_provisional_only",
            "exhaustiveManifestoDenominator":"missing",
            "independentDualCoding":"missing",
            "partyResponsibilityModel":"not_estimated",
            "verifiedUSStateFinanceAnnualAggregates":"complete_2012_to_2024",
            "pre2012CapitalCodeFamilies":"source_audited_not_financially_harmonized",
            "electionCalendarJoin":"missing",
            "budgetAuthorizationObligationOutlayClocks":"missing",
            "electoralCycleRegression":"not_estimated",
            "comparativeMultiCountryEmpiricalReplication":"not_completed",
            "causalClaims":"prohibited_pending_identification_validation",
            "normativeBadFaithJudgments":"not_supported_without_independent_intent_evidence",
        },
        "sourceRegistryStaleness":{
            "promiseSourceRegistryListsFiscalSourceAsNotIngested":stale_registry,
            "researchFeedFiscalSeriesCount":old_cycle,
            "correctSeparateModernIngestionObserved":len(modern["records"]),
            "interpretation":"Old pledge-specific registry and feed are stale about finance data; this derived assessment uses actual official finance products and does not silently rewrite the source catalog."
        },
        "inputProvenance":{
            "pilot":"data/promises/us-2020-pilot.json",
            "verifiedExpansion":"data/promises/us-2020-source-verified-expansion.json",
            "candidateQueue":"data/promises/us-2020-review-queue.json",
            "modernFiscal":"data/fiscal/state-timeseries/aggregate-capital-2012-2024.json",
            "historicalCodeAudit":"data/fiscal/state-legacy/quality-audit.json",
            "fiscalClockTemplate":"data/fiscal/state-timeseries/fiscal-calendar-template-2012-2024.json",
            "literature":"research/campaign-promises/assessment-complete-2026-10-29.md",
        },
        "qualityAssurance":"Format, coverage, sourcing and recomputation verified. Factual independent pledge adjudication, causal identification and completeness of historical source sampling not certified."
    }

def main():
    report=make()
    output=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if "--check" in sys.argv[1:]:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=output:
            raise SystemExit("Assessment JSON missing/stale; regenerate and commit")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=output:
            OUT.write_text(output,encoding="utf-8")
    print(json.dumps({
        "assessmentStatus":report["completionStatus"],
        "pledge":{k:report["researchQuestions"]["pledgeFulfillment"][k] for k in
                  ("observedProvisionalPilotCases","unscoredCandidateRows","independentlyDualAdjudicatedCases","overallPledgeFulfillmentRate")},
        "fiscal":{k:report["researchQuestions"]["electoralShortTermism"][k] for k in
                  ("modernStateYears","officialFinanceAggregateRows","electoralTreatmentEffects")},
        "registryStale":report["sourceRegistryStaleness"]["promiseSourceRegistryListsFiscalSourceAsNotIngested"]
    },indent=2))

if __name__=="__main__":
    main()
