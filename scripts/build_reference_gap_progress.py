"""Generate the reference-first gap progress ledger with strict evidence guards.

No HTTP requests, raw downloads, external credentials or Pi hardware required.
A source pointer, or a bounded verified record, NEVER closes a national gate.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_GAPS = ROOT / "data/health/sitewide-missing-sources-v1.json"
ORIGINAL_GATES = ROOT / "data/health/completion-gates.json"
BACKLOG = ROOT / "research/assessments/ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json"
CASES = ROOT / "data/health/reference-first-evidence-cases-v1.json"
OUT = ROOT / "data/health/reference-gap-progress-v1.json"
SCHEMA = "power-atlas.reference-gap-progress.v1"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build():
    original = load(ORIGINAL_GAPS)
    gates = load(ORIGINAL_GATES)
    backlog = load(BACKLOG)
    receipts = load(CASES)
    original_local = {g["id"] for g in original["gaps"]}
    original_national = set(gates["blockingGates"])
    local = {g["id"]: g for g in backlog["localGaps"]}
    national = {g["id"]: g for g in backlog["nationalGates"]}
    if original_local != set(local) or original_national != set(national):
        raise ValueError("Backlog no longer matches canonical 55 local and nine national gates")
    if len(original_local) != 55 or len(original_national) != 9:
        raise ValueError("Scope changed; review with an explicit new baseline")
    receipt_ids = [c["id"] for c in receipts["cases"]]
    if len(receipt_ids) != len(set(receipt_ids)):
        raise ValueError("Duplicate evidence receipt")
    reference_ids = {s["id"] for s in backlog["verifiedEntryPoints"]}
    case_lookup = defaultdict(list)
    for c in receipts["cases"]:
        if c["originalGapClosureAllowed"] is not False:
            raise ValueError("Bounded evidence may not auto-close original gaps")
        ids = c["relatedLocalGapIds"] + c["relatedNationalGateIds"]
        if not ids:
            raise ValueError("Unlinked case")
        if not set(c["relatedLocalGapIds"]).issubset(original_local):
            raise ValueError("Unknown local gap in receipt")
        if not set(c["relatedNationalGateIds"]).issubset(original_national):
            raise ValueError("Unknown national gate in receipt")
        if not c.get("sourceDocuments") or not c.get("checks"):
            raise ValueError("Case missing original source and explicit measured checks")
        for gap_id in ids:
            case_lookup[gap_id].append(c["id"])
    rows = []
    for category, dataset in (("local", local), ("national", national)):
        for gap_id in sorted(dataset):
            gap = dataset[gap_id]
            linked = sorted(case_lookup.get(gap_id, []))
            expected = sorted(gap.get("boundedEvidenceCaseIds", []))
            if linked != expected:
                raise ValueError(f"Case linkage out of sync for {gap_id}")
            refs = sorted(s["id"] for s in backlog["verifiedEntryPoints"]
                          if gap_id in s["relevantGates"])
            if not set(refs).issubset(reference_ids):
                raise ValueError("Unknown source reference")
            rows.append({
                "gapId": gap_id,
                "category": category,
                "originalStatus": gap["originalStatus"],
                "status": "bounded_source_evidence_reviewed_gap_open" if linked else "open_no_new_bounded_evidence",
                "originalGateClosed": False,
                "boundedCaseIds": linked,
                "quickReferenceSourceIds": refs,
                "originalDirectorySourceIds": gap["sourceIds"] if category == "local" else [],
                "stillRequired": gap["requiredJoin"] if category == "local" else gap["nextAction"],
                "acceptanceRule": ("Verify exact original records, provenance, time, place, "
                                   "entity joins, legal status, completeness and independent "
                                   "review within the claimed scope; no automatic national closure."),
            })
    rows.sort(key=lambda row: (row["category"], row["gapId"]))
    return {
        "schema": SCHEMA,
        "asOfLocalDate": receipts["reviewedLocalDate"],
        "operatingMode": "reference_first_no_bulk_ingestion",
        "scope": {
            "localGapCount": 55,
            "nationalBlockingGateCount": 9,
            "openTotal": len(rows),
            "fullGapClosures": 0,
            "boundedEvidenceCasesReviewed": len(receipts["cases"]),
            "distinctGapsWithNewBoundedEvidence": len(case_lookup),
            "originalPublicSourceEntryPoints": len(reference_ids),
        },
        "safeguard": "Source discovery and narrow checks are not completion. Continue work on every remaining required join; all original nationwide and local gates stay open.",
        "gaps": rows,
    }


def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--summary", action="store_true")
    args = p.parse_args()
    expected = build()
    if args.write:
        OUT.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved {OUT.relative_to(ROOT)}")
        return
    current = load(OUT)
    if current != expected:
        raise SystemExit("Out-of-sync gap ledger: run python scripts/build_reference_gap_progress.py --write")
    if args.summary:
        print(json.dumps(current["scope"], indent=2))
    else:
        print(f"PASS: {current['scope']['openTotal']} original gaps remain open; "
              f"{current['scope']['boundedEvidenceCasesReviewed']} verified bounded cases")


if __name__ == "__main__":
    main()
