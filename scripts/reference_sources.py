"""Offline source-pointer registry for Power Atlas.

Builds an interim reference-only index from an independently reviewed gap
backlog. This module never performs an HTTP request or reads a reader's ZIP.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "research/assessments/ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json"
INDEX = ROOT / "platform/unified/data/source-reference-index-v1.json"
SCHEMA = "power-atlas.source-reference-index.v1"


def build() -> dict:
    backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))
    sources = []
    for source in backlog["verifiedEntryPoints"]:
        url = source["url"]
        bulk = source.get("bulkFile")
        for value in (url, bulk):
            if value:
                parsed = urlsplit(value)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError("Only non-credentialed HTTPS source URLs are allowed")
        sources.append({
            "id": source["id"],
            "publisher": source["origin"],
            "authority": "secondary_mirror" if source["origin"].startswith("Free Law Project") else "official",
            "officialReferenceURL": url,
            "archiveCandidateURL": bulk or None,
            "verifiedReferenceDate": "2026-11-12",
            "linkedGateIDs": source["relevantGates"],
            "coverageCaveat": source["coverage"],
            "interimAccess": "direct_source_reference",
            "retrievalStatus": "source_entry_point_identified_not_evidence_ingested",
            "archivalEligibility": "requires_license_and_validation_review",
        })
    sources.sort(key=lambda row: row["id"])
    ids = [row["id"] for row in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source IDs in backlog")
    return {
        "schema": SCHEMA,
        "generatedFrom": "research/assessments/ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json",
        "asOf": "2026-11-12",
        "activeMode": "reference",
        "activeModeMeans": "Official-source pointers only. The index does not fetch, cache, import, verify record contents, or close an evidence gap.",
        "futureMode": "hybrid_reference_cache_selective_archive_after_local_hardware_and_backup_gates",
        "referencedSourceCount": len(sources),
        "integrityPolicy": {
            "noImplicitGapClosure": True,
            "noAutomaticRecordDownload": True,
            "noClaimsOfSourceFreshness": True,
            "publicLinkNotEqualToVerifiedEvidence": True,
            "licenseAndTermsReviewBeforeArchival": True,
            "zipAndUserIdentityNotPersisted": True,
            "strictOriginAllowlistForFutureFetch": True,
            "piHardwareNotYetActivated": True,
        },
        "sources": sources,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Resolve Power Atlas original-source links offline")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Ensure source index is in sync with the backlog")
    group.add_argument("--write", action="store_true", help="Regenerate the source index")
    group.add_argument("--list", action="store_true", help="List source IDs and URLs")
    group.add_argument("--id", metavar="SOURCE_ID", help="Show exactly one source")
    group.add_argument("--gate", metavar="GATE_ID", help="Show sources relevant to one research gate")
    args = p.parse_args()
    expected = build()
    if args.write:
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        INDEX.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Updated {INDEX.relative_to(ROOT)} ({len(expected['sources'])} pointers)")
        return
    current = json.loads(INDEX.read_text(encoding="utf-8"))
    if current != expected:
        raise SystemExit("Source index is stale. Regenerate: python scripts/reference_sources.py --write")
    if args.check:
        print(f"OK: {len(current['sources'])} reference-only source pointers; no records downloaded")
        return
    if args.list:
        for src in current["sources"]:
            print(f"{src['id']}\t{src['officialReferenceURL']}")
        return
    found = [s for s in current["sources"] if (s["id"] == args.id if args.id else args.gate in s["linkedGateIDs"])]
    if not found:
        raise SystemExit("No matching reference found")
    print(json.dumps(found[0] if args.id else found, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
