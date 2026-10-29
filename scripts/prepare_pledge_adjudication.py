#!/usr/bin/env python3
"""Build 2020 pledge source inventory and independent-review queue.

The inventory is not exhaustive. Pledges are not rated by a scripted/AI
substitute for independent human adjudication. Absence of observed effort
is never coded as proof of deception.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"data/promises"
OUT=DIR/"adjudication-2020-template.json"
SOURCES=[
 {"id":"US20-DEM-PLATFORM","side":"DEM","type":"party_platform","date":"2020-08-17",
  "url":"https://www.presidency.ucsb.edu/documents/2020-democratic-party-platform",
  "primarySourceScope":"official_archived_platform","governingPartyFor2021_2025":True},
 {"id":"US20-REP-RESOLUTION","side":"REP","type":"platform_resolution","date":"2020-08-24",
  "url":"https://www.presidency.ucsb.edu/documents/resolution-regarding-the-republican-party-platform",
  "primarySourceScope":"no_new_platform_adopted_in_2020","governingPartyFor2021_2025":False},
 {"id":"US20-BIDEN-ACCEPTANCE","side":"DEM","type":"nomination_acceptance_speech","date":"2020-08-20",
  "url":"https://www.presidency.ucsb.edu/documents/address-accepting-the-democratic-presidential-nomination-wilmington-delaware",
  "primarySourceScope":"candidate_acceptance_speech","governingPartyFor2021_2025":True},
 {"id":"US20-TRUMP-ACCEPTANCE","side":"REP","type":"nomination_acceptance_speech","date":"2020-08-27",
  "url":"https://www.presidency.ucsb.edu/documents/address-accepting-the-republican-presidential-nomination-2",
  "primarySourceScope":"candidate_acceptance_speech","governingPartyFor2021_2025":False},
 {"id":"US20-BIDEN-BBB-RELEASE","side":"DEM","type":"campaign_policy_release","date":"2020-09-07",
  "url":"https://www.presidency.ucsb.edu/documents/biden-campaign-press-release-fact-sheet-joe-bidens-plan-build-back-better-for-american",
  "primarySourceScope":"candidate_preelection_policy_release","governingPartyFor2021_2025":True},
]


def read(name):
    return json.loads((DIR/name).read_text(encoding="utf-8"))

def make():
    pilot=read("us-2020-pilot.json")
    expansion=read("us-2020-source-verified-expansion.json")
    queue=read("us-2020-review-queue.json")
    rows=[]
    for r in pilot["records"]+expansion["records"]:
        rows.append({"pledgeId":r["id"],"sourceURL":r["pledgeSource"]["url"],
                     "pledgeParaphrase":r["pledgeParaphrase"],"policyArea":r["policyArea"],
                     "existingCaseReview":"provisional_one_reviewer",
                     "existingProvisionalLabelNotIndependent":r["outcome"]})
    for r in queue["records"]:
        rows.append({"pledgeId":r["id"],"sourceURL":r["pledgeSource"]["url"],
                     "pledgeParaphrase":r["pledgeParaphrase"],"policyArea":r["policyArea"],
                     "existingCaseReview":"unscored_candidate",
                     "existingProvisionalLabelNotIndependent":None})
    if len(rows)!=32 or len(set(r["pledgeId"] for r in rows))!=32:
        raise ValueError("Expected 32 disjoint pledge case or candidate IDs")
    for r in rows:
        url=urlsplit(r["sourceURL"])
        if url.scheme!="https" or not url.hostname:
            raise ValueError("Unverified pledge link")
        r.update({
            # four-point score is ordinal outcome, not intrinsic moral merit;
            # every score is null until 2 independent reviews and reconciliation
            "ordinalOutcome":None,
            "outcomeVocabulary":{
                "3":"fully_achieved_given_pledge_specific_target",
                "2":"partial_achievement_of_target",
                "1":"formal_attempt_target_not_achieved",
                "0":"no_formal_attempt_after_exhaustive_documented_search"
            },
            "reviewerOne":None,"reviewerTwo":None,
            "adjudicated":False,
            "policyReachFraction":None,"statutoryDurability":None,
            "sourcePassageOffset":None,"parentPledgeId":None,
            "actionEvidence":[],
            "searchCompleteness":{
                "nationalCongressBillsReviewed":False,
                "federalRegisterActionsReviewed":False,
                "appropriationsAndBudgetRequestsReviewed":False,
                "agencyImplementationReviewed":False,
                "executiveActionsReviewed":False,
            },
            "effortEvidence":{
                "executiveBudgetOrAgenda":{"applicable":None,"evidencePresent":None,"url":None},
                "legislativeSponsorship":{"applicable":None,"evidencePresent":None,"url":None},
                "administrativePreparations":{"applicable":None,"evidencePresent":None,"url":None},
            },
            "legislativeEffortScore":None,
            "institutionalConstraintEvidence":[],
            "actorIntentClassification":None,
            "openQuestions":["Atomize compound commitments; check parent/duplicate keys; validate authoritative original text; double-code action and target achievement; search dated negative evidence"]
        })
    return {
        "schema":"power-atlas.pledge-review-2020.v1",
        "asOf":"2026-10-29",
        "status":"incomplete_document_inventory_candidate_and_pilot_queue_not_adjudicated",
        "publicationDecision":"never_compute_population_rate_from_this_manifest",
        "periodStart":"2019-01-01","electionDate":"2020-11-03",
        "governingTermEnd":"2025-01-20",
        "sourceCollectionRule":{
            "include":"All authoritative campaign policy statements, platform and nominee convention speeches before election cutoff; fixed tier and catalog before evaluating outcomes",
            "exclude":"Generic non-testable rhetoric, post-election coalition agreements, duplicates, unapproved surrogate speeches",
            "partyRules":"2020 Republicans explicitly did not adopt new 2020 platform; 2016 platform is a historically re-affirmed document, not newly authored 2020 text",
            "candidateReleaseCensusComplete":False,
            "allPlatformSentencesEnumerated":False,
            "allConventionSentencesEnumerated":False,
            "fullDenominatorFrozen":False,
            "oppositionPromisesNotDirectlyAssignableTo2021_2025Administration":True,
        },
        "knownPrimaryDocuments":SOURCES,
        "knownDocumentsCount":len(SOURCES),
        "reviewedPledgeCandidates":len(rows),
        "humanIndependentAdjudications":0,
        "reviewerRubric":{
            "scoring":"3 full, 2 partial, 1 formal attempted, 0 exhaustively confirmed no formal attempt; unknown null",
            "executiveOrderDoesNotAutomaticallyImplyPartial":"Executive order may fully satisfy an executive-action-specific pledge; judge against original promise's target and population",
            "unattemptedRequiresExhaustiveReview":"A missing row, unanswered query, or uncoded document cannot be an outcome 0",
            "dualCoding":"Separate reviewers must independently code original commitment, attempt, implementation, deadline and evidence; reconcile with adjudication log",
            "effortIndex":"Three applicable binary dimensions only. Unknown is null, not zero; inapplicable components must be excluded. Score is never an intent judgment.",
            "intentInference":"Cannot infer deliberate deception from unified government and LEI=0; require direct contemporaneous evidence and competing-cause evaluation."
        },
        "records":sorted(rows,key=lambda r:r["pledgeId"])
    }


def validate_score(row):
    """Future adjudication guard. This does not score existing cases."""
    score=row.get("ordinalOutcome")
    if score is None:
        return None
    if type(score) is not int or score not in (0,1,2,3):
        raise ValueError("Expected discrete ordinal score or unknown (null)")
    a=row.get("reviewerOne")
    b=row.get("reviewerTwo")
    if not (isinstance(a,dict) and isinstance(b,dict)
            and a.get("reviewerId") and b.get("reviewerId")
            and a["reviewerId"]!=b["reviewerId"]
            and a.get("independentlySubmitted") is True
            and b.get("independentlySubmitted") is True
            and a.get("sourceURL") and b.get("sourceURL")
            and row.get("adjudicated") is True):
        raise ValueError("Ordinal score requires two independent reviewers and explicit adjudication")
    if score==0 and not all(v is True for v in row["searchCompleteness"].values()):
        raise ValueError("Zero score requires fully documented, exhaustive negative action search")
    return score


def effort_index(evidence):
    """No deception classifier. Unknown or no applicable dimensions => None."""
    if not isinstance(evidence,dict):
        raise ValueError("Effort evidence must be a dict")
    score=0
    applicable=0
    for key in ("executiveBudgetOrAgenda","legislativeSponsorship","administrativePreparations"):
        dim=evidence.get(key)
        if not isinstance(dim,dict):
            raise ValueError(f"Missing effort dimension {key}")
        if dim.get("applicable") is None:
            return None
        if dim["applicable"] is False:
            continue
        if dim["applicable"] is not True:
            raise ValueError("Invalid applicability")
        applicable+=1
        if dim.get("evidencePresent") is None:
            return None
        if dim["evidencePresent"] is True:
            if not dim.get("url") or not urlsplit(dim["url"]).scheme=="https":
                raise ValueError("An effort claim requires an original evidence link")
            score+=1
        elif dim["evidencePresent"] is not False:
            raise ValueError("Invalid evidencePresent")
    return None if applicable==0 else {"positiveEvidenceCount":score,"applicableDimensions":applicable}


def main(argv=None):
    doc=make()
    rendered=json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if argv and "--check" in argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=rendered:
            raise SystemExit("Stale review template; regenerate and commit")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8")!=rendered:
            OUT.write_text(rendered,encoding="utf-8")
    print(json.dumps({"pledgeRecords":len(doc["records"]),
                      "documentsScoped":len(doc["knownPrimaryDocuments"]),
                      "fullDenominatorFrozen":False,
                      "independentAdjudications":0,"intentInference":"not_permitted"},indent=2))

if __name__=="__main__":
    main(sys.argv[1:])
