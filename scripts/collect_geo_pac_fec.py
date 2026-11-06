"""FEC bulk PAS2 donor-committee-to-candidate links for GEO employee-funded PAC.

Exports ONLY federally registered committee/candidate IDs, transaction dates,
amounts and filing provenance: no individual names, locations, addresses or
occupational data. PAS2 can contain amendments and memo items; amounts are
shown in separate transaction-type categories, not mixed with corporate funds.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

from scripts.collect_business_federal_awards import money_cents, as_money

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/business-influence/geo-pac-candidate-disbursements-v1.json"
CYCLES = (2018, 2020, 2022, 2024, 2026)
COMMITTEE_ID = "C00382150"
SOURCE_DESCRIPTION = "https://www.fec.gov/campaign-finance-data/contributions-committees-candidates-file-description/"
TRANSACTION_CODES = "https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/"
COLCOUNT = 22
MAX_ARCHIVE_BYTES = 250_000_000
MAX_MATCHED_PER_CYCLE = 6000
TYPE_MEANINGS = {
    "24K": "direct_contribution_to_candidate_committee",
    "24Z": "in_kind_contribution_to_federal_committee",
    "24A": "independent_expenditure_opposing_candidate",
    "24E": "independent_expenditure_supporting_candidate",
    "24C": "coordinated_party_expenditure",
    "24F": "communication_cost_for_candidate",
    "24N": "communication_cost_against_candidate",
    "24P": "contribution_to_possible_federal_candidate",
    "24R": "election_recount_disbursement",
    "24H": "other_political_disbursement",
}
CATEGORY_BY_TYPE = {
    "24K": "direct", "24Z": "in_kind",
    "24A": "independent", "24E": "independent",
    "24C": "coordinated", "24F": "communication",
    "24N": "communication", "24P": "other_candidate",
    "24R": "other_candidate", "24H": "other_candidate",
}


def archive_url(cycle):
    if cycle not in CYCLES:
        raise ValueError("Unapproved FEC election cycle")
    return f"https://www.fec.gov/files/bulk-downloads/{cycle}/pas2{str(cycle)[-2:]}.zip"


def fetch_archive(cycle):
    req = urllib.request.Request(archive_url(cycle), headers={
        "User-Agent": "PowerAtlasPublicResearch/1.0",
        "Accept": "application/zip",
    })
    with urllib.request.urlopen(req, timeout=85) as response:
        if response.status != 200:
            raise ValueError(f"FEC archive HTTP {response.status}")
        body = response.read(MAX_ARCHIVE_BYTES + 1)
        if not body or len(body) > MAX_ARCHIVE_BYTES:
            raise ValueError("FEC archive missing or above bounded size")
    if not zipfile.is_zipfile(io.BytesIO(body)):
        raise ValueError("Official PAS2 file is not a ZIP")
    return body


def parse_pac_line(line, cycle):
    # The only retained fields are committee/candidate IDs and original filing
    # references. Never serialize contributor NAME, CITY, ZIP or EMPLOYER.
    fields = line.rstrip("\r\n").split("|")
    if len(fields) != COLCOUNT:
        raise ValueError("PAS2 matching row column count changed")
    if fields[0] != COMMITTEE_ID:
        raise ValueError("Unexpected committee ID in selected PAS2 row")
    code = fields[5].strip()
    if code not in TYPE_MEANINGS:
        raise ValueError("Unmapped FEC transaction type " + code)
    recipient = fields[15].strip()
    candidate = fields[16].strip()
    tran_id = fields[17].strip()
    report_no = fields[18].strip()
    sub_id = fields[21].strip()
    date_raw = fields[13].strip()
    if not re.fullmatch(r"C[0-9]{8}", recipient) or not re.fullmatch(r"[HSP][0-9A-Z]{8}", candidate):
        # OTHER_ID and CAND_ID are documented FEC nullable columns.
        # We cannot create an edge to an unnamed committee/candidate; preserve
        # the count of excluded rows instead of fabricating a recipient.
        return None
    if not tran_id:
        # FEC notes TRAN_ID applies only to electronic filings.
        # A candidate association with no stable transaction key cannot be
        # safely de-amended, so do not publish a purported unique payment.
        return None
    if len(tran_id) > 60 or not report_no.isdigit() or not sub_id.isdigit():
        raise ValueError("Invalid transaction/file provenance")
    try:
        date = dt.datetime.strptime(date_raw, "%m%d%Y").date()
    except ValueError as exc:
        raise ValueError("Invalid FEC transaction date") from exc
    if not cycle - 2 <= date.year <= cycle:
        raise ValueError("FEC transaction outside two-year cycle window")
    cents = money_cents(fields[14])
    return {
        "sourceCommitteeId": COMMITTEE_ID,
        "recipientCommitteeId": recipient,
        "candidateId": candidate,
        "transactionType": code,
        "transactionMeaning": TYPE_MEANINGS[code],
        "category": CATEGORY_BY_TYPE[code],
        "date": date.isoformat(),
        "amountUsd": as_money(cents),
        "_cents": cents,
        "transactionId": tran_id,
        "filingNumber": int(report_no),
        "subId": sub_id,
        "memoExcluded": fields[19].strip().upper() == "X",
        "reportType": fields[2].strip(),
        "amendmentIndicator": fields[1].strip(),
        "source": f"https://www.fec.gov/data/disbursements/?committee_id={COMMITTEE_ID}&two_year_transaction_period={cycle}",
    }


def parse_archive(blob: bytes, cycle: int):
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        entries = [z for z in zf.infolist() if z.filename.lower().endswith(".txt") and not z.is_dir()]
        if len(entries) != 1 or entries[0].file_size > 550_000_000:
            raise ValueError("Unexpected FEC ZIP member layout or decompressed size")
        matched = []
        seen_all = 0
        missing_link_ids = 0
        matched_filer_rows = 0
        with zf.open(entries[0]) as src:
            for binary in src:
                seen_all += 1
                if not binary.startswith((COMMITTEE_ID + "|").encode("ascii")):
                    continue
                matched_filer_rows += 1
                if matched_filer_rows > MAX_MATCHED_PER_CYCLE:
                    raise ValueError("PAC FEC matched-row cap reached: do not truncate")
                parsed = parse_pac_line(binary.decode("latin-1"), cycle)
                if parsed is None:
                    missing_link_ids += 1
                    continue
                matched.append(parsed)
    if not matched:
        raise ValueError("No GEO PAC row in FEC PAS2: zero cannot be confirmed without auditing PAC registration and source")
    # FEC calls TRAN_ID unique within a committee/report, not necessarily
    # throughout the election cycle; report type and calendar year avoid
    # conflating a recycled ID across distinct reporting periods.
    winning = {}
    duplicate_subids = set()
    for row in matched:
        if row["subId"] in duplicate_subids:
            raise ValueError("Duplicate FEC SUB_ID in same archive")
        duplicate_subids.add(row["subId"])
        key = (row["sourceCommitteeId"], row["date"][:4],
               row["reportType"], row["transactionId"],
               row["recipientCommitteeId"], row["candidateId"],
               row["transactionType"])
        old = winning.get(key)
        if old is None or (row["filingNumber"], row["subId"]) > (old["filingNumber"], old["subId"]):
            winning[key] = row
    selected = [x for x in winning.values() if not x["memoExcluded"]]
    selected.sort(key=lambda x: (x["date"], x["transactionId"], x["filingNumber"], x["subId"]))
    sums = Counter()
    counts = Counter()
    recipient_count = Counter()
    for row in selected:
        sums[row["category"]] += row["_cents"]
        counts[row["category"]] += 1
        recipient_count[row["recipientCommitteeId"]] += 1
    clean = [{k:v for k,v in x.items() if k != "_cents"} for x in selected]
    # Preserve row count exclusions; never pretend amendment selection is legally final.
    return {
        "cycle": cycle,
        "sourceArchive": archive_url(cycle),
        "archiveSha256": hashlib.sha256(blob).hexdigest(),
        "rowsScanned": seen_all,
        "matchedCommitteeRows": matched_filer_rows,
        "rowsWithoutVerifiableRecipientOrTransactionId": missing_link_ids,
        "matchedSourceRowsWithValidEndpoints": len(matched),
        "amendmentVersionsSupersededHeuristic": len(matched) - len(winning),
        "memoRowsExcluded": sum(1 for x in winning.values() if x["memoExcluded"]),
        "categoryTotals": [
            {"category": cat, "netReportedUsd": as_money(sums[cat]),
             "recordCount": counts[cat], "interpretation": "reported_filer_expenditure_after_heuristic_canonicalization_not_independently_filing_reconciled"}
            for cat in sorted(sums)
        ],
        "recipientCommitteeCount": len(recipient_count),
        "records": clean,
        "reviewStatus": "original_FEC_bulk_committee_rows_amendments_heuristically_deduped_nullable_endpoints_excluded",
    }


def collect(fetcher=fetch_archive):
    return {
        "schema": "power-atlas.geo-pac-itemized-to-candidates.v1",
        "createdUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "committeeId": COMMITTEE_ID,
        "committeeName": "THE GEO GROUP, INC. POLITICAL ACTION COMMITTEE",
        "sponsorshipMeaning": "Employee-funded connected PAC, not GEO corporate-treasury spending or individual donations",
        "sourceDescription": SOURCE_DESCRIPTION,
        "transactionCodesSource": TRANSACTION_CODES,
        "sourceCommittee": f"https://www.fec.gov/data/committee/{COMMITTEE_ID}/",
        "caution": "PAS2 includes committee-to-candidate reported disbursements of different types, including independent spending. Types are not interchangeable. A recipient's later government contract is not evidence the contribution affected an award. Filing amendments may remain incomplete despite heuristic deduplication. This is not a complete PAC financial ledger.",
        "cycles": [parse_archive(fetcher(c), c) for c in CYCLES],
    }


def publish(doc):
    if len(doc.get("cycles", [])) != len(CYCLES):
        raise ValueError("Refuse partial PAC cycle coverage")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(OUT)


if __name__ == "__main__":
    result = collect()
    publish(result)
    print(json.dumps({"committee": COMMITTEE_ID,
                      "cycles": [(y["cycle"], len(y["records"]), y["rowsScanned"]) for y in result["cycles"]]}))
