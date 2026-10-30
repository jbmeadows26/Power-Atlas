"""Audit each of six state-level coverage gaps without equating a source URL to ingested records."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/coverage-six-domains.json"
DOMAINS=(
 "state_campaign_finance","state_roll_calls",
 "state_legislative_district_polygons_and_legal_boundary_history",
 "lower_court_litigation_dockets_and_state_cases",
 "state_judicial_selection_and_election_outcomes",
 "statewide_local_returns_and_official_vote_reconciliation",
)
CENSUS="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer"
SOURCE_HINTS={
 "state_campaign_finance":"Official state campaign finance disclosure regulator, state-specific",
 "state_roll_calls":"Official legislature journals and bill/roll-call repositories, chamber-specific",
 "state_legislative_district_polygons_and_legal_boundary_history":"U.S. Census TIGERweb official current/historical geometry; state plan and court history independently required",
 "lower_court_litigation_dockets_and_state_cases":"Official state judiciary dockets, county and court access policies",
 "state_judicial_selection_and_election_outcomes":"Official state judiciary, nomination/appointments and certified election authorities",
 "statewide_local_returns_and_official_vote_reconciliation":"Official state and county election canvass and certification records",
}

def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf8"))

def build():
    states=[s for s in read("data/geography/states.json")["states"] if s["postal"] not in ("DC","PR")]
    authorities=read("data/elections/official-source-index.json")["records"]
    auth={r["state"]:r for r in authorities}
    result=[]
    for state in states:
        postal=state["postal"]
        if postal not in auth:
            raise ValueError("No official election-office directory entry: "+postal)
        for domain in DOMAINS:
            record={
                "id":postal+":"+domain,
                "state":postal,"fips":state["fips"],"stateName":state["name"],
                "domain":domain,
                "sourceDiscovery":{"officialSourceHint":SOURCE_HINTS[domain],
                  "electionOfficeURL":auth[postal]["electionOfficeURL"],
                  "sourceAuthority":"FEC state-office directory for election-office link only"},
                "recordsIngested":0,
                "coverageStatus":"not_source_verified_at_state_record_level",
                "certificationStatus":"not_verified",
                "reconciliationStatus":"not_run",
                "blockingDependency":"official exact source + state-level event/record evidence + completeness reconciliation",
                "reviewRequired":True,
            }
            if domain=="state_legislative_district_polygons_and_legal_boundary_history":
                record["sourceDiscovery"]["censusLayerIndex"]=CENSUS
                record["sourceDiscovery"]["layers"]={"2024_upper":5,"2024_lower":6,"2026_upper":1,"2026_lower":2}
                record["blockingDependency"]="download and verify each polygon geometry plus versioned state plan/court effective-date history"
            if domain=="statewide_local_returns_and_official_vote_reconciliation":
                record["blockingDependency"]="retrieve state-certified canvass and matching county/precinct results with contest-identity and vote-sum checks"
            result.append(record)
    ids=[r["id"] for r in result]
    if len(ids)!=len(set(ids)):
        raise ValueError("Duplicate coverage keys")
    counts=Counter(x["domain"] for x in result)
    if not (len(states)==50 and set(x["postal"] for x in states).issubset(auth)):
        raise ValueError("State/election authority jurisdiction universe differs")
    return {"schema":"power-atlas.six-domain-coverage.v1",
            "publicationStatus":"source_discovery_only_not_coverage_completion",
            "jurisdictions":len(states),"additionalDistrictOfColumbiaElectionAuthorityKnown":"DC" in auth,"domains":list(DOMAINS),
            "coverage":{k:{"jurisdictionsIndexed":v,"jurisdictionsCompleted":0,
                         "sourceVerifiedJurisdictions":0} for k,v in counts.items()},
            "knownExistingSeparateDatasets":{
                "stateLegislators":"data/people/state-legislators.json",
                "stateRedistrictingBillCandidates":"data/legislation/state-redistricting-bills.json",
                "officialElectionOfficeDirectory":"data/elections/official-source-index.json",
                "note":"Existing partial records do not equal state roll-call, certified canvass or state campaign-finance completeness"},
            "records":result,
            "warning":"Neither an official directory link nor a district source URL proves state-level records have been ingested, reviewed, reconciled or complete."}

def main():
    document=build()
    OUT.write_text(json.dumps(document,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({"jurisdictions":document["jurisdictions"],"rows":len(document["records"]),
                      "domains":{k:v["jurisdictionsIndexed"] for k,v in document["coverage"].items()}},indent=2))
if __name__=="__main__":
    main()
