"""Bounded Voteview roll-call polarization aggregates, no raw individual-vote republication.

Usage: python scripts/collect_hyperpartisanship_voteview.py
Source documentation: https://voteview.com/articles/data_help_votes and
https://voteview.com/articles/data_help_members
This is a descriptive metric, NOT proof of misconduct, a constituent-interest test,
or a measure of cross-party cosponsorship.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import io
import json
import math
import urllib.request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/hyperpartisanship/voteview-party-divisions-v1.json"
MEMBERS_URL = "https://voteview.com/static/data/out/members/HSall_members.csv"
VOTES_URL = "https://voteview.com/static/data/out/votes/HSall_votes.csv"
CHAMBERS = ("House", "Senate")
PARTIES = {"100": "D", "200": "R"}
FIRST_CONGRESS = 100
LAST_CONGRESS = 119  # 119th is necessarily partial; mark it explicitly.
MAX_MEMBER_ROWS = 250000
MAX_VOTE_ROWS = 35000000
MIN_PARTY_CAST = {"House": 100, "Senate": 20}
THRESHOLD = 0.90

def stream_csv(url):
    if not url.startswith("https://voteview.com/static/data/out/"):
        raise ValueError("Disallowed source URL")
    req = urllib.request.Request(url, headers={"User-Agent": "PowerAtlasResearch/1.0 (non-commercial research; cite Voteview)", "Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=100) as response:
        if response.status != 200:
            raise RuntimeError("Voteview returned non-200 status")
        # Read incrementally: do not load the multi-million-row vote file into RAM.
        with io.TextIOWrapper(response, encoding="utf-8-sig", newline="") as reader:
            yield from csv.DictReader(reader)

def parse_members(rows, min_rows=1000):
    member_party = {}
    ideology = defaultdict(lambda: {"D": [], "R": []})
    count = 0
    for row in rows:
        count += 1
        if count > MAX_MEMBER_ROWS:
            raise ValueError("Member input exceeds audited row limit")
        congress = int(row["congress"])
        chamber = row["chamber"]
        if congress < FIRST_CONGRESS or congress > LAST_CONGRESS or chamber not in CHAMBERS:
            continue
        party = PARTIES.get(str(row["party_code"]))
        if not party:
            continue
        icpsr = str(row["icpsr"])
        key = (congress, chamber, icpsr)
        if key in member_party:
            # Ambiguous source membership is a hard stop; never multiply vote rows.
            raise ValueError(f"Duplicated Voteview member key: {key}")
        member_party[key] = party
        try:
            loc = float(row["nominate_dim1"])
            if math.isfinite(loc):
                ideology[(congress, chamber)][party].append(loc)
        except (ValueError, TypeError):
            pass
    if count < min_rows or not member_party:
        raise ValueError("Voteview members unexpectedly sparse")
    return member_party, ideology

def summarize_votes(rows, member_party, ideology):
    # roll vote count order: D-yea, D-nay, R-yea, R-nay.
    tallies = defaultdict(lambda: [0, 0, 0, 0])
    row_count = 0
    unmatched = 0
    for row in rows:
        row_count += 1
        if row_count > MAX_VOTE_ROWS:
            raise ValueError("Vote input exceeds audited row limit")
        congress = int(row["congress"])
        chamber = row["chamber"]
        if not (FIRST_CONGRESS <= congress <= LAST_CONGRESS and chamber in CHAMBERS):
            continue
        party = member_party.get((congress, chamber, str(row["icpsr"])))
        if not party:
            unmatched += 1
            continue
        # Strict recorded Yea/Nay only. Paired, announced, present and absent are excluded.
        cast = str(row["cast_code"])
        if cast not in ("1", "6"):
            continue
        slot = (0 if party == "D" else 2) + (0 if cast == "1" else 1)
        tallies[(congress, chamber, int(row["rollnumber"]))][slot] += 1
    if row_count < 1000 or not tallies:
        raise ValueError("Voteview vote input unexpectedly sparse")
    out = []
    for (congress, chamber) in ((c, h) for c in range(FIRST_CONGRESS, LAST_CONGRESS + 1) for h in CHAMBERS):
        considered = split = disagree = roll_count = 0
        for (n, h, _), (dy, dn, ry, rn) in tallies.items():
            if n != congress or h != chamber:
                continue
            roll_count += 1
            d, r = dy + dn, ry + rn
            if d < MIN_PARTY_CAST[chamber] or r < MIN_PARTY_CAST[chamber]:
                continue
            considered += 1
            d_yes, r_yes = dy / d, ry / r
            if (d_yes >= THRESHOLD and r_yes <= 1 - THRESHOLD) or (r_yes >= THRESHOLD and d_yes <= 1 - THRESHOLD):
                split += 1
            if (d_yes > 0.5 and r_yes < 0.5) or (r_yes > 0.5 and d_yes < 0.5):
                disagree += 1
        party_ideology = ideology.get((congress, chamber), {})
        dem = party_ideology.get("D", [])
        rep = party_ideology.get("R", [])
        out.append({
            "congress": congress, "chamber": chamber,
            "periodStatus": "incomplete_congress" if congress == LAST_CONGRESS else "completed_congress",
            "rollCallsObserved": roll_count,
            "rollCallsEligibleBothParties": considered,
            "opposed90PctPartyRollCalls": split,
            "opposed90PctShare": round(split / considered, 6) if considered else None,
            "oppositePartyMajorityRollCalls": disagree,
            "oppositePartyMajorityShare": round(disagree / considered, 6) if considered else None,
            "democraticMemberIdeologyN": len(dem),
            "republicanMemberIdeologyN": len(rep),
            "firstDimensionMeanPartyGap": round(sum(rep) / len(rep) - sum(dem) / len(dem), 6) if dem and rep else None,
            "evidenceStatus": "derived_voted_member_aggregates" if considered and dem and rep else "insufficient_valid_rows"
        })
    return out, row_count, unmatched

def collect():
    members, ideology = parse_members(stream_csv(MEMBERS_URL))
    member_fallback = {}
    for congress in range(114, 118):
        # Voteview's all-member export omitted complete congressional periods.
        # The official Voteview per-Congress membership archive is still present.
        member_url = f"https://voteview.com/static/data/out/members/HS{congress}_members.csv"
        extra_members, extra_ideology = parse_members(stream_csv(member_url), min_rows=200)
        coverage = {"House": 0, "Senate": 0}
        for key, party in extra_members.items():
            if key[0] != congress:
                raise ValueError(f"Wrong Congress in member fallback {member_url}")
            if key in members and members[key] != party:
                raise ValueError(f"Conflicting party identity for {key} across Voteview sources")
            members[key] = party
            coverage[key[1]] += 1
        for k, by_party in extra_ideology.items():
            if k[0] != congress:
                raise ValueError("Ideology fallback Congress mismatch")
            existing = ideology[k]
            if not existing["D"] and not existing["R"]:
                ideology[k] = by_party
            elif len(existing["D"]) + len(existing["R"]) != len(by_party["D"]) + len(by_party["R"]):
                raise ValueError(f"Conflicting historical ideology memberships for {k}")
        if coverage["House"] < 400 or coverage["Senate"] < 90:
            raise RuntimeError(f"Party roster fallback sparse for {congress}: {coverage}")
        member_fallback[str(congress)] = {"source": member_url, "memberRows": coverage}
    records, n, unmatched = summarize_votes(stream_csv(VOTES_URL), members, ideology)
    # Voteview's all-Congress CSV currently omits four complete Congresses.
    # Its documented data-download template also offers per-Congress CSVs.
    # Try those *verified Voteview paths* without inventing missing rows.
    fallback_status = {}
    for congress in range(114, 118):
        by_chamber = [x for x in records if x["congress"] == congress]
        if all(x["rollCallsEligibleBothParties"] >= 100 for x in by_chamber):
            continue
        # The Voteview download UI exposes H and S chamber-specific archives.
        # Never assume a combined HS file contains both chambers for a given era.
        house_url = f"https://voteview.com/static/data/out/votes/H{congress}_votes.csv"
        senate_url = f"https://voteview.com/static/data/out/votes/S{congress}_votes.csv"
        sources = [house_url, senate_url]
        from itertools import chain
        try:
            alternate, alternate_n, alternate_unknown = summarize_votes(chain(stream_csv(house_url), stream_csv(senate_url)), members, ideology)
        except HTTPError as exc:
            if exc.code in (404, 410):
                fallback_status[str(congress)] = {"sources": sources, "status": f"http_{exc.code}_not_available"}
                continue
            raise
        except ValueError as exc:
            if str(exc) == "Voteview vote input unexpectedly sparse":
                fallback_status[str(congress)] = {"sources": sources, "status": "empty_or_sparse_per_congress_export"}
                continue
            raise
        candidate = [x for x in alternate if x["congress"] == congress]
        if len(candidate) != 2 or not all(x["rollCallsEligibleBothParties"] >= 100 for x in candidate):
            fallback_status[str(congress)] = {"sources": sources, "status": "incomplete_source"}
            continue
        records = [x for x in records if x["congress"] != congress] + candidate
        n += alternate_n
        unmatched += alternate_unknown
        fallback_status[str(congress)] = {"sources": sources, "status": "verified_per_chamber_fallback",
                                          "houseEligible": candidate[0]["rollCallsEligibleBothParties"] if candidate[0]["chamber"] == "House" else candidate[1]["rollCallsEligibleBothParties"],
                                          "senateEligible": candidate[0]["rollCallsEligibleBothParties"] if candidate[0]["chamber"] == "Senate" else candidate[1]["rollCallsEligibleBothParties"]}
    records.sort(key=lambda r: (r["congress"], r["chamber"]))
    complete = [r for r in records if r["congress"] <= 118]
    gaps = [(r["congress"], r["chamber"], r["rollCallsObserved"], r["rollCallsEligibleBothParties"]) for r in complete if r["rollCallsEligibleBothParties"] < 100]
    if len(complete) != 38:
        raise RuntimeError("Missing chamber-congress output rows: refusing publication")
    # The upstream HSall_votes bulk export can omit entire Congresses; never
    # turn these into zero polarization, nor suppress all otherwise valid years.
    for row in records:
        if row["rollCallsEligibleBothParties"] < 100:
            row["opposed90PctShare"] = None
            row["oppositePartyMajorityShare"] = None
            row["evidenceStatus"] = "insufficient_source_coverage_no_rate_published"

    document = {
        "schema": "power-atlas.hyperpartisanship.voteview-party-divisions.v1",
        "status": "derived_voteview_aggregates_not_legislative_intent",
        "asOf": datetime.now(timezone.utc).date().isoformat(),
        "source": {
            "votes": VOTES_URL, "members": MEMBERS_URL,
            "documentation": "https://voteview.com/articles/data_help_votes",
            "citation": "Lewis, Poole, Rosenthal, Boche, Rudkin, and Sonnet (2026), Voteview: Congressional Roll-Call Votes Database",
            "publicationRights": "Only compact derived aggregates published. Verify upstream terms before reusing raw data."
        },
        "methods": {
            "denominator": "Roll calls where >=100 House members or >=20 Senate members from EACH of D and R cast recorded Yea(1) or Nay(6), irrespective of bill subject.",
            "opposed90PctPartyRollCalls": "At least 90% of one party voted Yea and at least 90% of the other voted Nay.",
            "oppositePartyMajorityRollCalls": "Strict majorities of D and R voted in opposite directions.",
            "ideologyGap": "Difference in unweighted mean Voteview first-dimension NOMINATE estimate (R minus D) within chamber-congress.",
            "excludedCodes": [0, 2, 3, 4, 5, 7, 8, 9],
            "sourceRollNumber": "Voteview rollnumber, not House Clerk rollnumber",
            "biases": ["Floor agenda selection", "Party members omitted or absent", "Unanimous consent and voice votes not represented", "Mix of legislative and nomination votes", "NOMINATE estimation updates may change history", "No explicit constituent-preference measure", "No cosponsorship measure"],
            "inference": "Descriptive only. Party voting divergence is not proof that a member acted against constituents."
        },
        "diagnostics": {
            "perCongressMemberFallback": member_fallback,
            "perCongressFallback": fallback_status,
            "historicalMissingChamberPeriods": [{"congress": c, "chamber": h, "rollCallsObserved": observed, "eligibleRollCalls": eligible} for c, h, observed, eligible in gaps],
            "historicalCoverageComplete": len(gaps) == 0,
            "doNotInterpolateOrTreatMissingAsZero": True,
            "memberKeys": len(members),
            "voteRowsScanned": n,
            "voteRowsNoMatchingMajorPartyMember": unmatched
        },
        "records": records
    }
    text = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
        OUT.write_text(text, encoding="utf-8")
    print("Voteview historical chamber records:", len(complete), "raw rows scanned:", n)

if __name__ == "__main__":
    collect()
