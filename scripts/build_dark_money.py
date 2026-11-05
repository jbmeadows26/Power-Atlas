"""Build a source-attributed, privacy-minimised cross-jurisdiction money graph.

Only explicit FEC committee IDs or independently reviewed organizational IDs
become transfer edges. Aggregated FEC receipts are NOT donor-to-recipient edges.
Potential sequential flows are investigation leads, never traced dollars.
No individual donors, street addresses, personal identifiers or inferred owners.
"""
from __future__ import annotations
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/money-influence"
FEC_PREVIEW = BASE / "verified-record-previews-v1.json"
FEC_DISB = ROOT / "data/finance/fec-disbursements.json"
REVIEWED = BASE / "reviewed-organizational-transfers-v1.json"
OUT = BASE / "dark-money-graph-v1.json"
CID = re.compile(r"^C[0-9]{8}$")
KINDS = {"federal", "state", "county", "municipal", "school_board", "ballot_measure"}
FORBIDDEN = {"address", "street", "email", "phone", "ssn", "dob", "occupation", "employer",
             "person", "contributor", "donor_name", "registered_agent"}
LIMITATIONS = [
    "A committee's category-level receipts and spending do not identify the original donor or connect incoming dollars to a particular outbound payment.",
    "Two payments of similar size close in time do not establish that the same money moved between organizations.",
    "Use of a common vendor does not by itself establish illegal coordination.",
    "Most 501(c)(4) and 501(c)(6) organizations do not publicly disclose donor identities through Form 990; no undisclosed donor is reconstructed.",
    "Local, state, IRS and ballot-measure itemized coverage is incomplete. Blank sections mean unavailable evidence, not zero spending."
]

def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def public_url(value):
    if not isinstance(value, str) or not value.startswith("https://"):
        raise ValueError("A direct HTTPS evidence URL is required")
    host = urlsplit(value).hostname or ""
    if not host or host.endswith(".local") or host in {"localhost", "127.0.0.1"}:
        raise ValueError("Invalid public evidence host")
    return value

def amount(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0 < value < 1e12):
        raise ValueError("Transfer amount must be positive and finite")
    return round(value, 2)

def is_safe_organization(obj):
    if not isinstance(obj, dict):
        return False
    if any(str(k).lower() in FORBIDDEN or "address" in str(k).lower() for k in obj):
        return False
    return obj.get("entityType") in {"committee", "nonprofit", "corporation", "political_party"}

def reviewed_rows():
    """Optional manually reviewed cross-jurisdiction organizational records."""
    doc = read_json(REVIEWED, {"records": []})
    if not isinstance(doc, dict) or not isinstance(doc.get("records"), list):
        raise ValueError("Invalid reviewed-transfer ledger")
    seen = set()
    for row in doc["records"]:
        if not isinstance(row, dict) or any(
            str(k).lower() in FORBIDDEN or "address" in str(k).lower() for k in row
        ):
            raise ValueError("Private-person or address field in organization ledger")
        if row.get("id") in seen or not re.fullmatch(r"[a-zA-Z0-9_.:-]{5,100}", str(row.get("id", ""))):
            raise ValueError("Missing or duplicate source transaction ID")
        seen.add(row["id"])
        if row.get("jurisdiction") not in KINDS:
            raise ValueError("Invalid election jurisdiction")
        if row.get("reviewStatus") != "human_checked_official_filing":
            raise ValueError("No cross-jurisdiction edges without documented review")
        if not row.get("filingId") or not row.get("reviewedBy"):
            raise ValueError("Filing ID and reviewer required")
        left, right = row.get("fromEntity"), row.get("toEntity")
        if not (is_safe_organization(left) and is_safe_organization(right)):
            raise ValueError("Only organization endpoints with explicit IDs are accepted")
        for obj in (left, right):
            if not re.fullmatch(r"[a-zA-Z0-9_.:-]{3,110}", str(obj.get("id", ""))):
                raise ValueError("Stable organizational ID required")
            if not isinstance(obj.get("name"), str) or not obj["name"].strip():
                raise ValueError("Organization name required")
        date.fromisoformat(row["date"])
        amount(row["amountUSD"])
        public_url(row["source"])
        yield row

def collect_graph(preview, disbursements, manual=()):
    snapshots, nodes, edges = [], {}, {}
    for row in preview["pacCommittees"]:
        cid = row["committeeId"]
        if not CID.fullmatch(cid):
            raise ValueError("Invalid FEC committee")
        n_id = "fec:" + cid
        nodes[n_id] = {"id": n_id, "name": row["name"], "entityType": "committee",
                       "jurisdiction": "federal", "source":
                       "https://www.fec.gov/data/committee/" + cid + "/"}
        snapshots.append({k: row[k] for k in (
            "committeeId", "name", "cycle", "coverageEnd", "receiptsUSD", "disbursementsUSD",
            "individualContributionsUSD", "otherCommitteeContributionsUSD",
            "transfersFromAffiliatesUSD", "contributionsToOtherCommitteesUSD",
            "transfersToAffiliatesUSD", "independentExpendituresUSD",
            "partyCoordinatedExpendituresUSD", "source"
        )})
    for row in disbursements.get("records", []):
        src, dst = row.get("committeeId"), row.get("recipientCommitteeId")
        if not (CID.fullmatch(str(src)) and CID.fullmatch(str(dst))):
            continue  # never publish recipient names without official committee IDs
        if src == dst:
            continue
        day = row["date"]
        date.fromisoformat(day)
        a = amount(row["amountUSD"])
        for cid in (src, dst):
            nid = "fec:" + cid
            nodes.setdefault(nid, {"id": nid, "name": "FEC " + cid, "entityType": "committee",
                                   "jurisdiction": "federal", "source":
                                   "https://www.fec.gov/data/committee/" + cid + "/"})
        eid = "fec:" + row["id"]
        if eid in edges:
            raise ValueError("Duplicate FEC filing item")
        edges[eid] = {"id": eid, "from": "fec:" + src, "to": "fec:" + dst,
                      "amountUSD": a, "date": day, "jurisdiction": "federal",
                      "evidenceType": "filed_committee_payment", "source":
                      public_url(row["source"]), "reviewStatus":
                      "official_filing_not_independently_reconciled"}
    for row in manual:
        a, b = row["fromEntity"], row["toEntity"]
        for org in (a, b):
            nodes[org["id"]] = {"id": org["id"], "name": org["name"],
                                "entityType": org["entityType"],
                                "jurisdiction": row["jurisdiction"],
                                "source": public_url(row["source"])}
        eid = "filing:" + row["id"]
        if eid in edges:
            raise ValueError("Duplicate reviewed organizational transaction")
        edges[eid] = {"id": eid, "from": a["id"], "to": b["id"],
                      "amountUSD": amount(row["amountUSD"]), "date": row["date"],
                      "jurisdiction": row["jurisdiction"], "evidenceType":
                      "reviewed_organization_transfer", "filingId": row["filingId"],
                      "source": public_url(row["source"]), "reviewStatus":
                      "human_checked_official_filing"}
    links = list(edges.values())
    signals = []
    for incoming in links:
        for outgoing in links:
            if incoming["to"] != outgoing["from"] or incoming["id"] == outgoing["id"]:
                continue
            gap = (date.fromisoformat(outgoing["date"]) -
                   date.fromisoformat(incoming["date"])).days
            ratio = abs(outgoing["amountUSD"] - incoming["amountUSD"]) / incoming["amountUSD"]
            if 0 <= gap <= 45 and ratio <= 0.05 and outgoing["to"] != incoming["from"]:
                signals.append({"type": "potential_sequential_payment",
                                "evidence": [incoming["id"], outgoing["id"]],
                                "dateGapDays": gap, "amountDifferencePct": round(ratio * 100, 2),
                                "interpretation": "Investigative lead only; no source-of-funds attribution"})
    return {"schema": "power-atlas.dark-money.graph.v1", "sourceStatus": "partial",
            "scope": "Published organization/committee records only; not a census of dark money",
            "metrics": {"fecCommitteeCycleSnapshots": len(snapshots),
                        "distinctOrganizations": len(nodes), "filedTransferEdges": len(links),
                        "potentialSequentialPaymentLeads": len(signals),
                        "verifiedOriginalDonorAttributions": 0},
            "nodes": sorted(nodes.values(), key=lambda x: x["id"]),
            "snapshots": sorted(snapshots, key=lambda x: (x["cycle"], x["committeeId"])),
            "edges": sorted(links, key=lambda x: x["id"]),
            "signals": sorted(signals, key=lambda x: x["evidence"])[:100],
            "limitations": LIMITATIONS}

def build():
    p = read_json(FEC_PREVIEW)
    d = read_json(FEC_DISB, {"records": []})
    if not p or not isinstance(p.get("pacCommittees"), list):
        raise ValueError("Missing documented FEC committee snapshots")
    result = collect_graph(p, d, reviewed_rows())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                   encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(build()["metrics"], indent=2))
