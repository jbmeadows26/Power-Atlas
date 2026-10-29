"""Compile a small evidence-linked, source-validated mobile research feed."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/hyperpartisanship"
OUT=DATA/"app-summary-v1.json"

def read(name):
    return json.loads((DATA/name).read_text(encoding="utf-8"))

def build():
    p=read("baseline-v1.json")
    v=read("voteview-party-divisions-v1.json")
    g=read("govinfo-119-bill-cosponsors-v1.json")
    if (p["schema"],v["schema"],g["schema"])!=(
        "power-atlas.hyperpartisanship.descriptive.v1",
        "power-atlas.hyperpartisanship.voteview-party-divisions.v1",
        "power-atlas.hyperpartisanship.govinfo-bill-cosponsors.v1"):
        raise ValueError("Unrecognized upstream evidence schema")
    total=len(g["records"])
    yes=sum(x["knownCrossPartyCosponsor"] is True for x in g["records"])
    no=sum(x["knownCrossPartyCosponsor"] is False for x in g["records"])
    missing=total-yes-no
    reported=g["coverage"]
    if total<4000 or (total,yes,no,missing)!=(reported["count"],reported["crossPartyTrue"],reported["crossPartyFalseWithCompletePartyData"],reported["crossPartyUnknown"]):
        raise ValueError("Bill coverage is unverified")
    if yes<100 or yes+no<.70*total:
        raise ValueError("Identity crosswalk failed; do not misreport bipartisanship")
    votes=[]
    for x in v["records"]:
        valid=x["rollCallsEligibleBothParties"]>=100 and x["evidenceStatus"]=="derived_voted_member_aggregates"
        if not valid and x["opposed90PctShare"] is not None:
            raise ValueError("Incomplete source cannot emit numeric voting rate")
        votes.append({"congress":x["congress"],"chamber":x["chamber"],
                      "complete":x["periodStatus"]=="completed_congress",
                      "observed":valid,"eligibleRollCalls":x["rollCallsEligibleBothParties"],
                      "strictPartyOppositionShare":x["opposed90PctShare"] if valid else None,
                      "oppositePartyMajorityShare":x["oppositePartyMajorityShare"] if valid else None,
                      "nominateFirstDimensionMeanGap":x["firstDimensionMeanPartyGap"] if valid else None})
    if len(votes)!=40 or sum(x["observed"] and x["complete"] for x in votes)<26:
        raise ValueError("Insufficient historical voting observations")
    missing_congresses=sorted({x["congress"] for x in votes if x["complete"] and not x["observed"]})
    law=[{"congress":x["congress"],"substantive":x["substantive_laws_pre_election"],
          "ceremonial":x["ceremonial_laws_pre_election"],"clotureAllTypes":x["cloture_motions_filed"],
          "congressComplete":x["complete_congress"]} for x in p["series"]]
    return {
        "schema":"power-atlas.hyperpartisanship.app-summary.v1",
        "asOf":min(v["asOf"],g["asOf"]),"status":"descriptive_not_causal",
        "sources":{"pew":"https://www.pewresearch.org/chart/congress-productivity-continues-to-dwindle/",
                   "senate":"https://www.senate.gov/legislative/cloture/clotureCounts.htm",
                   "voteview":"https://voteview.com/articles/data_help_votes",
                   "govinfo":"https://www.govinfo.gov/bulkdata/BILLSTATUS/119"},
        "coverage":{"bills119":total,"classifiedBills119":yes+no,"crossPartyBills119":yes,
                    "noCrossPartyBills119":no,"unknownPartyBills119":missing,
                    "knownCrossPartyShareClassified":round(yes/(yes+no),6),
                    "observedCompletedChamberCongresses":sum(x["observed"] and x["complete"] for x in votes),
                    "totalCompletedChamberCongresses":38,"sourceMissingCongresses":missing_congresses},
        "limitations":["119th Congress unfinished","GovInfo bill crossparty is cosponsorship, not enactment or floor voting",
                       "Current party roster may not reflect party at each cosponsorship date",
                       "Voteview bulk file omits historical Congresses; null is not zero",
                       "Cloture includes nominations; law and cloture cutoffs differ",
                       "No constituent-preference model, viral rhetoric causality or documented corrupt influence"],
        "methods":{"strictOpposition":"At least 90% of one major party voted yea and 90% of the other nay on an eligible recorded vote",
                   "billCrossParty":"At least one non-withdrawn opposite-major-party cosponsor, unknown identity remains unclassified"},
        "voting":votes,"legislation":law
    }

if __name__=="__main__":
    obj=build()
    serialized=json.dumps(obj,indent=2,ensure_ascii=False)+"\n"
    if len(serialized.encode())>100000: raise ValueError("Too large for mobile summary")
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=serialized:
        OUT.write_text(serialized,encoding="utf-8")
    print("Hyperpartisanship app summary valid",obj["coverage"])
