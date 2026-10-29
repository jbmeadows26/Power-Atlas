#!/usr/bin/env python3
"""Build a bounded public campaign-promise *research evidence* feed.

The purpose-selected pilot must never produce a population fulfillment rate.
This script has no network dependency, no secrets, and never mutates the
existing Power Atlas gerrymandering/app-feed.json.
Usage: python -m scripts.build_promises [--check]
"""
import json
import sys
from pathlib import Path

from scripts.validate_promises import validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/promises"
OUT = DATA / "research-feed.json"


def read(filename):
    return json.loads((DATA / filename).read_text(encoding="utf-8"))


def build_feed():
    pilot = read("us-2020-pilot.json")
    expansion = read("us-2020-source-verified-expansion.json")
    queue = read("us-2020-review-queue.json")
    sources = read("source-registry.json")
    validate(pilot)
    validate(expansion)
    if queue.get("denominatorFrozen") is not False:
        raise ValueError("A manually curated candidate queue is not a frozen sampling frame")
    if queue.get("publicationStatus") != "not_eligible_for_fulfillment_statistics":
        raise ValueError("Candidate queue status is unsafe")
    if sources.get("publicationStatus") != "source_catalog_only_no_data_ingestion":
        raise ValueError("Registry would misrepresent catalog entries as ingested data")
    records = sorted(pilot["records"] + expansion["records"], key=lambda x: x["id"])
    ids = [r["id"] for r in records]
    candidate_ids = [r["id"] for r in queue["records"]]
    if len(set(ids + candidate_ids)) != len(ids + candidate_ids):
        raise ValueError("A pledge/candidate id collision requires de-duplication")
    for candidate in queue["records"]:
        if candidate.get("outcome") is not None:
            raise ValueError("Unadjudicated candidate must not have an outcome")
        if candidate.get("reviewStatus") != "no_outcome_research_completed":
            raise ValueError("Candidate queue review status unexpectedly changed")
    for r in records:
        if r["reviewerCount"] < 2 or r["codingStatus"] != "adjudicated":
            # This is allowed in the pilot, but population inference is NOT.
            pass
    if sources.get("sourceCount") != len(sources.get("sources", [])):
        raise ValueError("Source registry count mismatch")
    if any(s.get("recordCountIngested") != 0 for s in sources["sources"]):
        raise ValueError("The current source catalog does not include ingested fiscal series")
    return {
        "schema": "power-atlas.promise-research-feed.v1",
        "asOf": max(pilot["asOf"], expansion["asOf"], queue["asOf"], sources["asOf"]),
        "publicationStatus": "provisional_purposive_case_ledger_no_population_estimates",
        "coverage": {
            "jurisdictions": ["US"],
            "electionYears": [2020],
            "scoredProvisionalCases": len(records),
            "unscoredCandidateQueue": len(candidate_ids),
            "catalogedSourcesNotIngested": len(sources["sources"]),
            "denominatorFrozen": False,
            "verifiedIndependentDualCoderCases": 0,
            "fiscalSeriesObservations": 0
        },
        "inference": {
            "promiseFulfillmentRate": None,
            "promiseFulfillmentConfidenceInterval": None,
            "electoralSpendingCycleCoefficient": None,
            "causalAttribution": None,
            "reason": "Purposive, singly reviewed cases and unscored candidate queue; no complete denominator or harmonized spending panel."
        },
        "provisionalCases": [
            {
                "id": r["id"],
                "source": r["pledgeSource"]["url"],
                "sourceLocator": r.get("sourceLocator", ""),
                "pledgeParaphrase": r["pledgeParaphrase"],
                "successCriterion": r["successCriterion"],
                "policyArea": r.get("policyArea", "unknown"),
                "outcome": r["outcome"],
                "codingStatus": r["codingStatus"],
                "reviewerCount": r["reviewerCount"],
                "events": [
                    {"date": e["date"], "kind": e["kind"],
                     "description": e["description"], "source": e["source"]}
                    for e in r["events"]
                ],
                "ambiguityNotes": r.get("ambiguityNotes", [])
            }
            for r in records
        ],
        "unscoredCandidates": [
            {"id": r["id"], "pledgeParaphrase": r["pledgeParaphrase"],
             "source": r["pledgeSource"]["url"],
             "reviewStatus": r["reviewStatus"], "outcome": None}
            for r in sorted(queue["records"], key=lambda x: x["id"])
        ],
        "methodology": "research/campaign-promises/deep-gap-audit.md",
        "warning": "This pilot is a case-study evidence ledger, not a representative measure of politician honesty or government performance."
    }


def main():
    feed = build_feed()
    rendered = json.dumps(feed, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv[1:]:
        if not OUT.exists():
            raise SystemExit("Missing research-feed.json: run python scripts/build_promises.py")
        actual = json.loads(OUT.read_text(encoding="utf-8"))
        if actual != feed:
            raise SystemExit("Stale research-feed.json: rebuild and commit it")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != rendered:
            OUT.write_text(rendered, encoding="utf-8")
    print(json.dumps(feed["coverage"], indent=2))
    print("Causal or population estimates: suppressed until validated denominators and data exist")


if __name__ == "__main__":
    main()
