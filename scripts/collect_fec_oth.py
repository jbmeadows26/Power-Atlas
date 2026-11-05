"""Bounded official FEC 'OTH' committee-to-committee receipt ingestion.

FEC bulk 'OTH' is a *mixed* transaction file: CMTE_ID is the reporting
committee; direction depends on TRANSACTION_TP. We publish only affirmative
incoming payments from another registered committee. Other types, memos,
person-level records, and money sent to candidates are deliberately excluded.

The archive is streamed to a temporary file and read without extracting it.
It never enters Git. The output is a limited, review-labelled selection of
official rows, not a national census or a financial total.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "data/money-influence/verified-record-previews-v1.json"
OUT = ROOT / "data/finance/fec-committee-transfers.json"
COLUMN_COUNT = 21
MAX_ARCHIVE_BYTES = 350_000_000
MAX_PUBLISH_ROWS = 1200
MIN_AMOUNT = Decimal("2500.00")
CID = re.compile(r"^C[0-9]{8}$")
# Confirmed FEC "receipt from registered filer / affiliated committee".
RECEIPT_TYPES = {
    "18K": "contribution_received_from_registered_filer",
    "18G": "transfer_in_from_affiliated_committee",
    "30K": "convention_account_receipt_from_registered_filer",
    "30G": "convention_account_transfer_in_from_affiliate",
    "31K": "headquarters_account_receipt_from_registered_filer",
    "31G": "headquarters_account_transfer_in_from_affiliate",
    "32K": "recount_account_receipt_from_registered_filer",
    "32G": "recount_account_transfer_in_from_affiliate",
}
DESCRIPTIONS = [
    "https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/",
    "https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/",
]

def source_url(year: int) -> str:
    if year not in (2024, 2026):
        raise ValueError("Only documented 2024/2026 FEC cycles supported")
    return f"https://www.fec.gov/files/bulk-downloads/{year}/oth{year % 100:02d}.zip"

def field(row, position):
    return (row[position - 1] or "").strip() if len(row) >= position else ""

def parse_row(raw, year: int, allow_ids: set[str]):
    if len(raw) != COLUMN_COUNT:
        return None
    recipient = field(raw, 1)
    sender = field(raw, 16)
    typ = field(raw, 6)
    if not (CID.fullmatch(recipient) and CID.fullmatch(sender)):
        return None
    if recipient == sender or (recipient not in allow_ids and sender not in allow_ids):
        return None
    if typ not in RECEIPT_TYPES or field(raw, 19).upper() == "X":
        return None
    if field(raw, 7) in ("IND", "CAN"):
        return None
    try:
        dt = datetime.strptime(field(raw, 14), "%m%d%Y").date()
        if dt.year not in (year, year - 1):
            return None
        money = Decimal(field(raw, 15))
        if not money.is_finite() or money < MIN_AMOUNT or money > Decimal("10000000000"):
            return None
    except (InvalidOperation, ValueError, OverflowError):
        return None
    number = field(raw, 18)
    sub = field(raw, 21)
    if not number.isdigit() or not sub.isdigit():
        return None
    txid = field(raw, 17)
    # One transaction is stable across amended filing versions.
    # Preserve per-report identity (filer, report type, ID and transaction date).
    fingerprint = "|".join((recipient, field(raw, 3), txid or sub, dt.isoformat(), typ))
    return {
        "id": "fec-oth-" + str(year) + "-" + hashlib.sha256(fingerprint.encode()).hexdigest()[:20],
        "from": "fec:" + sender,
        "to": "fec:" + recipient,
        "date": dt.isoformat(), "amountUSD": float(money),
        "jurisdiction": "federal",
        "cycle": year, "transactionType": typ, "transactionMeaning": RECEIPT_TYPES[typ],
        "evidenceType": "official_fec_reported_receipt",
        "reportingCommitteeId": recipient,
        "contributingCommitteeId": sender,
        "filingId": number, "subId": sub,
        "source": f"https://www.fec.gov/data/receipts/?committee_id={recipient}&two_year_transaction_period={year}&contributor_id={sender}",
        "reviewStatus": "fec_raw_receipt_not_filing_amendment_reconciled",
        "_reportSeq": int(number),  # only for latest-file selection; excluded from published output
    }

def scan_rows(rows, year: int, allow_ids: set[str]):
    matched = {}
    stats = {"scannedRows": 0, "eligibleReceiptVersions": 0,
             "supersededVersions": 0, "selectedRows": 0,
             "outputTruncated": False, "selectionFloorUSD": str(MIN_AMOUNT)}
    for raw in rows:
        stats["scannedRows"] += 1
        r = parse_row(raw, year, allow_ids)
        if not r:
            continue
        stats["eligibleReceiptVersions"] += 1
        prior = matched.get(r["id"])
        if prior:
            stats["supersededVersions"] += 1
        if prior is None or (r["_reportSeq"], r["subId"]) > (prior["_reportSeq"], prior["subId"]):
            matched[r["id"]] = r
    selected = sorted(matched.values(), key=lambda x: (-x["amountUSD"], x["id"]))
    stats["distinctEligibleReceiptItems"] = len(selected)
    stats["outputTruncated"] = len(selected) > MAX_PUBLISH_ROWS
    selected = selected[:MAX_PUBLISH_ROWS]
    for r in selected:
        del r["_reportSeq"]
    stats["selectedRows"] = len(selected)
    return selected, stats

def download_archive(year, destination: Path):
    url = source_url(year)
    req = urllib.request.Request(
        url, headers={"User-Agent": "PowerAtlasPublicInterestResearch/1.1",
                      "Accept": "application/zip"})
    size, digest = 0, hashlib.sha256()
    with urllib.request.urlopen(req, timeout=90) as response, destination.open("wb") as target:
        if response.geturl().split("/")[2] != "www.fec.gov":
            raise ValueError("Unexpected FEC download redirect")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_ARCHIVE_BYTES:
                raise ValueError("FEC archive exceeds bounded free-run budget")
            digest.update(chunk)
            target.write(chunk)
    if not zipfile.is_zipfile(destination):
        raise ValueError("FEC archive is not a ZIP")
    return {"sourceArchiveURL": url, "downloadSHA256": digest.hexdigest(),
            "downloadBytes": size}

def import_archive(path: Path, year: int, allow_ids: set[str]):
    with zipfile.ZipFile(path) as z:
        entries = [x for x in z.infolist()
                   if x.filename.lower().endswith(".txt") and not x.is_dir()]
        if len(entries) != 1:
            raise ValueError("Unexpected FEC OTH ZIP layout")
        entry = entries[0]
        if entry.file_size > 3_000_000_000:
            raise ValueError("Uncompressed FEC archive exceeds safety bound")
        with z.open(entry) as binary:
            reader = csv.reader(io.TextIOWrapper(binary, encoding="latin-1", newline=""),
                                delimiter="|", strict=True)
            return scan_rows(reader, year, allow_ids)

def collect():
    preview = json.loads(PREVIEW.read_text(encoding="utf-8"))
    allow = {r["committeeId"] for r in preview["pacCommittees"] if CID.fullmatch(r["committeeId"])}
    if not allow:
        raise ValueError("No indexed committees for scoped filtering")
    year = int(os.environ.get("FEC_OTH_CYCLE", "2026"))
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
    with tempfile.TemporaryDirectory(prefix="atlas-fec-oth-") as tmp:
        archive = Path(tmp) / "official-fec-oth.zip"
        meta = download_archive(year, archive)
        records, stats = import_archive(archive, year, allow)
    if stats["scannedRows"] < 1000:
        raise ValueError("Unexpectedly small FEC transaction bulk file")
    if not records:
        raise ValueError("No eligible FEC records; preserve prior published data")
    newdoc = {
        "schema": "power-atlas.fec.oth-transfers.v1",
        "collectionScope": "Bounded official FEC receipt-side rows; no donor individuals, no payee-name inference",
        "cycle": year, "sourceMetadata": meta,
        "transactionDocumentation": DESCRIPTIONS,
        "selectedCommitteeIds": len(allow),
        "selection": stats,
        "limitations": [
            "A committee's reported receipt is not proof of the ultimate or original source of its donor's funds.",
            "Receipt-side records cannot be summed with disbursement-side records without reconciliation.",
            "Amendment precedence by report number is a heuristic, not certified original/amended filing reconciliation.",
            "Mixed FEC OTH codes, memos, refunds, candidate-targeted spending, and personal donor records are excluded.",
            "Top-dollar bounded sample from indexed committees above minimum; not all federal transactions or all 2026 money."
        ],
        "records": records
    }
    if existing and existing.get("cycle") == year and not records:
        raise ValueError("Refusing to overwrite prior collection with empty data")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(newdoc, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return newdoc

if __name__ == "__main__":
    result = collect()
    print(json.dumps({"cycle": result["cycle"], "selection": result["selection"],
                      "sha256": result["sourceMetadata"]["downloadSHA256"]}, indent=2))
