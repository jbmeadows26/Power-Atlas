"""Build compact, evidence-gated voting access frontend feed. stdlib, free, offline."""
import json
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/"data"/"voting-access"

def load(name):
    return json.loads((D/name).read_text(encoding="utf-8"))

def main():
    coverage=load("state-policy-coverage-v1.json")
    evidence=load("evidence-seed-v1.json")
    assert coverage["jurisdictionCount"] == len(coverage["jurisdictions"]) == 51
    assert evidence["count"] == len(evidence["records"])
    assert coverage["verifiedRuleCount"] == sum(
        p["status"] == "verified_current"
        for j in coverage["jurisdictions"] for p in j["topics"].values()
    ), "Verified count inconsistent with source"
    out={"schema":"power-atlas.voting-access.feed.v1",
         "asOf": coverage["asOf"],
         "publicationStatus":"research_only_not_verified_2026_law",
         "counts":{"jurisdictions":coverage["jurisdictionCount"],
                   "topics":coverage["topicCount"],
                   "verifiedRules":coverage["verifiedRuleCount"],
                   "evidenceRecords":evidence["count"]},
         "states":[{"id":j["id"],"name":j["name"],
                    "verifiedPolicies":sum(p["status"]=="verified_current" for p in j["topics"].values())}
                   for j in coverage["jurisdictions"]],
         "researchRecords":evidence["records"],
         "warnings":[coverage["publicationStatus"],evidence["publicationStatus"],
                     "Source links and past case decisions do not establish current law or causal effect."]}
    dest=D/"feed-v1.json"
    dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Built {dest.relative_to(ROOT)} with {out['counts']}")

if __name__=="__main__":
    main()
