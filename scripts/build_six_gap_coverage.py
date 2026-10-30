"""Audit six missing state-level datasets against actually persisted evidence.

Never equate state office directory links, polygon source discovery, federal
data, or incomplete state-only pilot samples to an exhaustive domain.
"""
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/coverage-six-domains.json"
DOMAINS=(
 "state_campaign_finance",
 "state_roll_calls",
 "state_legislative_district_polygons_and_legal_boundary_history",
 "lower_court_litigation_dockets_and_state_cases",
 "state_judicial_selection_and_election_outcomes",
 "statewide_local_returns_and_official_vote_reconciliation",
)
CENSUS="https://www2.census.gov/geo/tiger/TIGER2024"
SOURCE_HINTS={
 "state_campaign_finance":"Official state campaign finance disclosure regulator, state-specific",
 "state_roll_calls":"Official legislature journals and member-level roll call archives, chamber-specific",
 "state_legislative_district_polygons_and_legal_boundary_history":"U.S. Census original TIGER/Line district geometry; court enactment/effective-date history separately required",
 "lower_court_litigation_dockets_and_state_cases":"Official state trial and appellate judiciary, court and county access rules",
 "state_judicial_selection_and_election_outcomes":"Official state judiciary appointment, nominating commissions and state-certified judicial contests",
 "statewide_local_returns_and_official_vote_reconciliation":"Official state/county canvass and original precinct return systems",
}

def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf8"))

def build():
    states=[x for x in read("data/geography/states.json")["states"] if x["postal"] not in ("PR","DC")]
    auth={r["state"]:r for r in read("data/elections/official-source-index.json")["records"]}
    geom=read("data/geography/state-legislative-2024/index.json")
    nc=read("data/elections/nc-2024/reconciliation.json")
    wa=read("data/legislation/wa-2023-24-rollcalls/source-rollcalls.json")
    if len(states)!=50 or len(set(s["postal"] for s in states))!=50:
        raise ValueError("Expected 50 unique US states")
    if not set(x["postal"] for x in states).issubset(auth):
        raise ValueError("Missing state election authority mapping")
    if (geom.get("chamberGeometriesDownloaded")!=99 or geom.get("notApplicable")!=1 or
        geom.get("distinctGEOIDFeatures")!=6785 or geom.get("legalPlanHistoryComplete") is not False):
        raise ValueError("2024 Census state legislative geometry has not been validated")
    if (wa.get("state")!="WA" or wa.get("rollCalls")!=56 or
        wa.get("memberVoteRows")!=4017 or wa.get("allStateRollCallsComplete") is not False):
        raise ValueError("WA official member rollcall sample count mismatch")
    if (nc.get("state")!="NC" or nc.get("precinctCandidateRowsInspected")!=233510 or
        nc.get("countiesWithVotes")!=100 or nc.get("certifiedSpotcheckDiscrepancyCount")!=4 or
        nc.get("spotChecksAllMatch") is not False):
        raise ValueError("Original NC 2024 result and its certified exceptions not validated")
    by_state=defaultdict(list)
    for g in geom["records"]:
        by_state[g["state"]].append(g)
    if len(by_state)!=50 or any(len(x)!=2 for x in by_state.values()):
        raise ValueError("Unbalanced 2024 geography source")
    rows=[]
    for state in states:
        postal=state["postal"]
        for domain in DOMAINS:
            record={
                "id":postal+":"+domain,
                "state":postal,"fips":state["fips"],"stateName":state["name"],
                "domain":domain,
                "sourceDiscovery":{
                    "officialSourceHint":SOURCE_HINTS[domain],
                    "electionOfficeURL":auth[postal]["electionOfficeURL"],
                    "authorityURLOrigin":"FEC directory of official state election offices",
                },
                "recordsIngested":0,
                "officialRecordsSourceLinked":False,
                "coverageStatus":"source_discovery_only",
                "certificationStatus":"not_verified",
                "reconciliationStatus":"not_run",
                "blockingDependency":"exact official record-level source + statewide historical backfill + completeness reconciliation",
                "domainFullyComplete":False,
            }
            if domain=="state_legislative_district_polygons_and_legal_boundary_history":
                chapters=by_state[postal]
                ready=[g for g in chapters if g["status"].startswith("official_")]
                count=sum(g["features"] for g in ready)
                expected=1 if postal=="NE" else 2
                if len(ready)!=expected or count<=0:
                    raise ValueError(f"Missing official state geometry: {postal}")
                record.update({
                    "recordsIngested":count,"officialRecordsSourceLinked":True,
                    "coverageStatus":"2024_official_geometries_complete_for_state_legal_plan_history_unverified",
                    "certificationStatus":"original_census_tiger_source_sha_verified",
                    "reconciliationStatus":"district_GE OID_identity_and_geometry_checked".replace(" ",""),
                    "blockingDependency":"Prior redistricting plan vintages, state plan enactments, court-ordered map changes, effective dates and district lineage",
                })
                record["sourceDiscovery"]["current2024CensusZIPs"]=[
                    {"chamber":g["chamber"],"url":g["source"],"path":g["path"],
                     "sha256OriginalZIP":g["sha256OriginalZIP"],"polygonRecords":g["features"]}
                    for g in ready]
            elif postal=="WA" and domain=="state_roll_calls":
                record.update({
                    "recordsIngested":wa["memberVoteRows"],
                    "officialRecordsSourceLinked":True,
                    "coverageStatus":"official_2023_24_member_votes_sample_not_full_biennium",
                    "certificationStatus":"official_WA_legislative_web_services_member_tallies_reconciled",
                    "reconciliationStatus":"56_rollcall_member_vote_counts_match_original_summary",
                    "blockingDependency":"Enumerate and ingest every WA 2023-24 bill/session rollcall plus all other states, link official session rosters and journal vote identifiers",
                })
                record["sourceDiscovery"].update({
                    "officialRollCallService":wa["officialSourceService"],
                    "dataPath":"data/legislation/wa-2023-24-rollcalls/source-rollcalls.json",
                    "rollCalls":wa["rollCalls"],
                    "billsRequested":wa["billsRequested"],
                })
            elif postal=="NC" and domain=="statewide_local_returns_and_official_vote_reconciliation":
                record.update({
                    "recordsIngested":nc["precinctCandidateRowsInspected"],
                    "officialRecordsSourceLinked":True,
                    "coverageStatus":"one_2024_election_original_precinct_rows_100_counties_partial_certification",
                    "certificationStatus":"2024_statewide_four_choice_canvass_compared_with_small_unresolved_deltas",
                    "reconciliationStatus":"four_certified_spotchecks_unresolved",
                    "blockingDependency":"Identify source/canvass 1-3 vote differences and reconcile every candidate/contest to authenticated county and state canvasses; ingest further cycles and other states",
                })
                record["sourceDiscovery"].update({
                    "originalNCSBEZIP":nc["sourceURL"],
                    "sourceSHA256":nc["sourceZIPSHA256"],
                    "certifiedCanvassPDF":nc["certifiedCanvassSourceURL"],
                    "countyCount":100,
                    "countyChoiceRows":nc["countyContestChoiceRows"],
                    "exceptionCount":nc["certifiedSpotcheckDiscrepancyCount"]
                })
            elif postal=="NC" and domain=="state_judicial_selection_and_election_outcomes":
                record.update({
                    "recordsIngested":nc["judicialContestChoiceRows"],
                    "officialRecordsSourceLinked":True,
                    "coverageStatus":"source_indexed_2024_judicial_candidate_vote_totals_selection_history_missing",
                    "certificationStatus":"NC_2024_aggregate_judicial_totals_not_independently_certified_per_seat",
                    "blockingDependency":"Authenticate each 2024 judicial race after litigation, then all judicial selection methods, appointing authorities, seat histories and historical contests statewide",
                })
                record["sourceDiscovery"].update({
                    "ncsbeElectionResultOriginalZIP":nc["sourceURL"],
                    "judicialCandidateTotalsPath":"data/elections/nc-2024/judicial-candidate-totals.json",
                })
            rows.append(record)
    if len(rows)!=300 or len(set(r["id"] for r in rows))!=300:
        raise ValueError("Duplicate or missing six-domain state observation")
    cov={}
    for domain in DOMAINS:
        a=[r for r in rows if r["domain"]==domain]
        cov[domain]={
           "jurisdictionsIndexed":50,
           "sourceVerifiedJurisdictions":sum(r["officialRecordsSourceLinked"] for r in a),
           "jurisdictionsCompleted":sum(r["domainFullyComplete"] for r in a),
           "officialSourceRecordsIngested":sum(r["recordsIngested"] for r in a),
           "overallStatus":"partial" if any(r["officialRecordsSourceLinked"] for r in a) else "source_registry_only",
        }
    return {
        "schema":"power-atlas.six-domain-coverage.v1",
        "publicationStatus":"official_partial_record_evidence_live_not_six_domain_completion",
        "jurisdictions":50,
        "additionalDistrictOfColumbiaElectionAuthorityKnown":"DC" in auth,
        "domains":list(DOMAINS),
        "coverage":cov,
        "knownExistingSeparateDatasets":{
            "stateLegislators":"data/people/state-legislators.json",
            "stateRedistrictingBillCandidates":"data/legislation/state-redistricting-bills.json",
            "officialElectionOfficeDirectory":"data/elections/official-source-index.json",
            "note":"Federal appointments, third-party bill votes, and offices with source links are not full state-domain coverage",
        },
        "records":rows,
        "warning":"Current 2024 Census legislative geometry is complete at source-file level, but 2024 legal plan history, historical plans, state campaign finance, statewide rollcalls, trial dockets and exact canvass reconciliation remain incomplete; 2024 NC elections are one-state partial evidence.",
    }

def main():
    doc=build()
    encoded=json.dumps(doc,indent=2,sort_keys=True)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf8")!=encoded:
        OUT.write_text(encoded,encoding="utf8")
    print(json.dumps({"coverage":doc["coverage"],"totalDomainStateRows":len(doc["records"])},indent=2))

if __name__=="__main__":
    main()
