#!/usr/bin/env python3
"""Validate the strictly source-linked campaign-promise pilot (no network calls).

Format validation is NOT factual adjudication or evidence completeness.
Run: python scripts/validate_promises.py [data/promises/us-2020-pilot.json]
"""
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data/promises/us-2020-pilot.json"
OUTCOMES = {
    "fully_enacted", "partially_enacted", "attempted_not_enacted",
    "unattempted", "unresolved",
}
ACTIVITY = {
    "proposed_policy", "executive_action", "narrower_executive_action",
    "international_entry_into_force", "final_rule", "enacted_statute",
    "legislative_introduction", "budget_appropriation", "spending_outlay",
}
IMPLEMENTATION = {
    "international_entry_into_force", "executive_action", "final_rule",
    "enacted_statute", "spending_outlay",
}
STATUSES = {"provisional_source_checked", "adjudicated", "candidate_unreviewed"}
CONFIDENCES = {"high", "medium", "low", "unknown"}


def date(value, location):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("ISO YYYY-MM-DD required")
        return dt.date.fromisoformat(value)
    except ValueError as ex:
        raise ValueError(f"{location}: invalid date {value!r}") from ex


def url(value, location):
    if not isinstance(value, str):
        raise ValueError(f"{location}: source URI must be a string")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
        raise ValueError(f"{location}: HTTPS URL required without embedded credentials")


def validate(doc):
    if doc.get("schema") != "power-atlas.campaign-promises.v1":
        raise ValueError("Unexpected promise schema")
    date(doc.get("asOf"), "asOf")
    if doc.get("publicationStatus") != "provisional_pilot_not_representative":
        raise ValueError("Pilot publication status must flag nonrepresentative selection")
    coverage = doc.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("denominatorDefined") is not False:
        raise ValueError("Do not treat a hand-picked pilot as an exhaustive denominator")
    if set(doc.get("allowedOutcomes", [])) != OUTCOMES:
        raise ValueError("Outcome vocabulary drift")
    records = doc.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("No pledge records")
    seen = set()
    for i, row in enumerate(records):
        p = f"record[{i}]"
        uid = row.get("id")
        if not isinstance(uid, str) or not uid.startswith("US-2020-"):
            raise ValueError(f"{p}: invalid stable pledge id")
        if uid in seen:
            raise ValueError(f"{p}: duplicate pledge id")
        seen.add(uid)
        if row.get("country") != "US" or row.get("electionYear") != 2020:
            raise ValueError(f"{p}: pilot country/election mismatch")
        if row.get("pledgeMakerType") not in ("party", "candidate"):
            raise ValueError(f"{p}: unknown pledge maker type")
        for field in ("pledgeMaker", "pledgeParaphrase", "successCriterion", "governingActor"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"{p}: missing {field}")
        source = row.get("pledgeSource")
        if not isinstance(source, dict) or source.get("isPreElection") is not True:
            raise ValueError(f"{p}: source must be a pre-election primary pledge")
        url(source.get("url"), f"{p}.pledgeSource")
        if source.get("sourceType") not in (
            "archived_party_platform", "archived_campaign_press_release",
            "official_debate_transcript", "official_campaign_speech"
        ):
            raise ValueError(f"{p}: unsupported pledge source type")
        pledge_date = date(source.get("documentDate"), f"{p}.pledgeSource.documentDate")
        if pledge_date >= dt.date(2020, 11, 3):
            raise ValueError(f"{p}: post-election statement is not a campaign pledge")
        term_end = date(row.get("evaluationWindowEnd"), f"{p}.evaluationWindowEnd")
        if row.get("outcome") not in OUTCOMES:
            raise ValueError(f"{p}: invalid outcome")
        if row.get("codingStatus") not in STATUSES:
            raise ValueError(f"{p}: invalid review status")
        if row.get("confidence") not in CONFIDENCES:
            raise ValueError(f"{p}: invalid confidence")
        if not isinstance(row.get("reviewerCount"), int) or row["reviewerCount"] < 0:
            raise ValueError(f"{p}: invalid reviewer count")
        if row["codingStatus"] == "adjudicated" and row["reviewerCount"] < 2:
            raise ValueError(f"{p}: one reviewer cannot certify independent adjudication")
        if not isinstance(row.get("rightCensored"), bool):
            raise ValueError(f"{p}: missing right censor flag")
        if row["rightCensored"] and row["outcome"] not in ("unresolved",):
            raise ValueError(f"{p}: right-censored outcome must be unresolved")
        events = row.get("events")
        if not isinstance(events, list):
            raise ValueError(f"{p}: events must be an array")
        for j, e in enumerate(events):
            e_path = f"{p}.events[{j}]"
            event_date = date(e.get("date"), e_path)
            if event_date < pledge_date:
                raise ValueError(f"{e_path}: implementation before pledged text")
            if event_date > term_end and e.get("kind") != "post_term_policy_reversal":
                raise ValueError(f"{e_path}: subsequent action cannot count as in-term action")
            if not isinstance(e.get("description"), str) or not e["description"].strip():
                raise ValueError(f"{e_path}: missing event description")
            url(e.get("source"), e_path)
        in_term = [
            e for e in events if date(e["date"], p) <= term_end
            and e.get("kind") != "post_term_policy_reversal"
        ]
        if row["outcome"] == "fully_enacted" and not any(
            e.get("kind") in IMPLEMENTATION for e in in_term
        ):
            raise ValueError(f"{p}: full enactment requires in-term implementation event")
        if row["outcome"] == "attempted_not_enacted" and not any(
            e.get("kind") in ACTIVITY for e in in_term
        ):
            raise ValueError(f"{p}: attempted pledge lacks in-term action")
        if row["outcome"] == "unattempted" and any(
            e.get("kind") in ACTIVITY for e in in_term
        ):
            raise ValueError(f"{p}: unattempted contradicts documented attempts")
        date(row.get("outcomeAsOf"), f"{p}.outcomeAsOf")
        comparison = row.get("secondaryComparison")
        if comparison:
            url(comparison.get("source"), f"{p}.secondaryComparison")
        if not isinstance(row.get("ambiguityNotes"), list):
            raise ValueError(f"{p}: missing uncertainty / caveat array")
    return {"schema": doc["schema"], "records": len(records),
            "outcomes": dict(sorted(Counter(r["outcome"] for r in records).items())),
            "representative": False, "factualAdjudication": False}


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    result = validate(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
