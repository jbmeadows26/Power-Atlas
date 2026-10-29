"""Official GovInfo BILLSTATUS bill/cosponsor relationships (119th H.R. and S. only).

Keyless, bounded, ZIP-based collection. Never infer motive or congressional party
from names. Use independently attributed CC0 congressional roster, mark missing.
The snapshot is *not* a historical trend or proof that cross-party collaboration
rose/fell. Source: https://www.govinfo.gov/developers
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen
import json
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/hyperpartisanship/govinfo-119-bill-cosponsors-v1.json"
ROSTER = ROOT / "data/people/congress-members.json"
CONGRESS = 119
KINDS = ("hr", "s")
URL_BASE = "https://www.govinfo.gov/bulkdata"
MAX_LISTING_BYTES = 15_000_000
MAX_ZIP_BYTES = 85_000_000
MAX_ENTRY_BYTES = 5_000_000
MAX_UNCOMPRESSED_BYTES = 1_200_000_000
MAX_ENTRIES_PER_ZIP = 25000

def child(el, name):
    if el is None:
        return None
    return next((x for x in el if x.tag.rsplit("}", 1)[-1] == name), None)

def descend(el, *path):
    for name in path:
        el = child(el, name)
    return el

def textof(el, *path):
    node = descend(el, *path)
    return "".join(node.itertext()).strip() if node is not None else ""

def items(el, *path):
    root = descend(el, *path)
    return [] if root is None else [x for x in root if x.tag.rsplit("}", 1)[-1] == "item"]

def source_json(url):
    if not url.startswith(URL_BASE + "/json/BILLSTATUS/119/"):
        raise ValueError("Unapproved directory endpoint")
    req = Request(url, headers={"User-Agent": "PowerAtlasResearch/1.0 (public records)", "Accept": "application/json"})
    with urlopen(req, timeout=70) as res:
        raw = res.read(MAX_LISTING_BYTES + 1)
    if len(raw) > MAX_LISTING_BYTES:
        raise RuntimeError("GovInfo index exceeded size safety bound")
    return json.loads(raw.decode("utf-8"))

def resolve_official_zip(kind):
    assert kind in KINDS
    listing = source_json(f"{URL_BASE}/json/BILLSTATUS/{CONGRESS}/{kind}")
    expected = f"BILLSTATUS-{CONGRESS}-{kind}.zip"
    found = [x for x in listing.get("files", []) if x.get("justFileName", x.get("name")) == expected and not x.get("folder")]
    if len(found) != 1:
        raise RuntimeError(f"GovInfo {kind} archive is not uniquely listed by official source")
    url = found[0].get("link", "")
    if not url.startswith(URL_BASE + "/BILLSTATUS/119/") or not url.endswith("/" + expected):
        raise RuntimeError("GovInfo ZIP download link failed host/path validation")
    return url

def party_roster():
    doc = json.loads(ROSTER.read_text(encoding="utf-8"))
    if doc.get("license") != "CC0-1.0":
        raise RuntimeError("Missing source license for 119th identity crosswalk")
    ids = {}
    roster_date = doc.get("asOfDate", "")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", roster_date):
        raise RuntimeError("Legislator roster lacks a verifiable snapshot date")
    for m in doc["records"]:
        ident = m.get("bioguideId")
        if not re.fullmatch(r"[A-Z][0-9]{6}", ident or ""):
            continue
        if not (m.get("termStart", "") <= roster_date < m.get("termEnd", "9999")):
            continue
        p = str(m.get("party", "")).lower()
        party = "D" if p.startswith("democrat") else ("R" if p.startswith("republican") else None)
        if ident in ids and ids[ident] != party:
            raise RuntimeError("Conflicting official party crosswalk entry")
        ids[ident] = party
    if len(ids) < 500:
        raise RuntimeError("Unusually sparse current Congressional ID crosswalk")
    return ids

def parse_bill(xml_bytes, kind, source_url, parties):
    root = ET.fromstring(xml_bytes)
    bill = child(root, "bill")
    if bill is None:
        raise ValueError("Missing bill container")
    congress = textof(bill, "congress")
    number = textof(bill, "billNumber")
    if congress != str(CONGRESS):
        raise ValueError(f"Wrong Congress in {source_url}: {congress!r}")
    official_match = re.search(rf"BILLSTATUS-{CONGRESS}{kind}([1-9][0-9]*)[.]xml$", source_url)
    if number and not number.isdecimal():
        raise ValueError(f"Malformed XML bill number in {source_url}: {number!r}")
    if not number:
        # GovInfo occasionally leaves <billNumber> blank while the official ZIP
        # member filename supplies the issued numeric identifier. Track fallback.
        if not official_match:
            raise ValueError(f"No XML bill number and no official filename fallback: {source_url}")
        number = official_match.group(1)
        number_origin = "official_BILLSTATUS_filename_fallback"
    else:
        number_origin = "billStatus_XML_field"
        if official_match and int(number) != int(official_match.group(1)):
            raise ValueError(f"Conflicting XML/official filename bill numbers: {source_url}")
    sponsor_ids = []
    for item in items(bill, "sponsors"):
        ident = textof(item, "identifiers", "bioguideId") or next((v for node in item.iter() if node.tag.rsplit("}", 1)[-1].lower() == "bioguideid" for v in [(node.text or "").strip()] if v), "")
        if re.fullmatch(r"[A-Z][0-9]{6}", ident):
            sponsor_ids.append(ident)
    if len(set(sponsor_ids)) != len(sponsor_ids):
        raise ValueError("Repeated sponsor identity")
    cosponsors = []
    seen_events = set()
    for position, item in enumerate(items(bill, "cosponsors")):
        ident = textof(item, "identifiers", "bioguideId") or next((v for node in item.iter() if node.tag.rsplit("}", 1)[-1].lower() == "bioguideid" for v in [(node.text or "").strip()] if v), "")
        if not re.fullmatch(r"[A-Z][0-9]{6}", ident or ""):
            # Some official XML source records lack a stable ID. Preserve
            # each unknown independently; NEVER guess identity from a name.
            ident = f"unresolved-source-cosponsor-{position}"
        started = textof(item, "sponsorshipDate")
        withdrawn = textof(item, "sponsorshipWithdrawnDate")
        event = (ident, started or None, withdrawn or None)
        if event in seen_events:
            continue  # identical duplicate source event is not a second cosponsorship
        seen_events.add(event)
        cosponsors.append([ident, started or None, withdrawn or None])
    sponsor_party = parties.get(sponsor_ids[0]) if len(sponsor_ids) == 1 else None
    current_ids = {c[0] for c in cosponsors if c[2] is None}
    withdrawn_ids = {c[0] for c in cosponsors if c[2] is not None} - current_ids
    distinct_known = {parties.get(ident) for ident in current_ids if parties.get(ident) in ("D", "R")}
    unknown = sum(parties.get(ident) not in ("D", "R") for ident in current_ids)
    cross_known = bool(sponsor_party in ("D", "R") and ({"D", "R"} - {sponsor_party}) & distinct_known)
    if cross_known:
        cross = True
    elif sponsor_party not in ("D", "R") or unknown:
        cross = None
    else:
        cross = False
    return {
        "id": f"{CONGRESS}-{kind}-{int(number)}",
        "billNumber": int(number),
        "billNumberOrigin": number_origin,
        "billTypeSource": textof(bill, "billType") or None,
        "title": textof(bill, "title")[:220] or None,
        "introducedDate": textof(bill, "introducedDate") or None,
        "lastActionDate": textof(bill, "lastAction", "actionDate") or None,
        "sponsorIds": sponsor_ids,
        "sponsorPartyCrosswalk": sponsor_party,
        "cosponsorEvents": cosponsors,
        "activeCosponsorCount": len(current_ids),
        "withdrawnCosponsorCount": len(withdrawn_ids),
        "activeCosponsorUnknownPartyCount": unknown,
        "cosponsorSourceMissingBioguideCount": sum(c[0].startswith("unresolved-source-cosponsor-") for c in cosponsors),
        "knownCrossPartyCosponsor": cross,
        "source": source_url,
        "reviewStatus": "official_billstatus_crosswalk_requires_review" if cross is None else "official_billstatus_derived_cosponsor_link"
    }

def ingest_zip(kind, parties):
    url = resolve_official_zip(kind)
    req = Request(url, headers={"User-Agent": "PowerAtlasResearch/1.0 public data", "Accept": "application/zip"})
    with NamedTemporaryFile(suffix=".zip") as temp:
        with urlopen(req, timeout=120) as res:
            total = 0
            while True:
                chunk = res.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ZIP_BYTES:
                    raise RuntimeError("GovInfo ZIP exceeds compressed size safety bound")
                temp.write(chunk)
        temp.flush()
        with zipfile.ZipFile(temp.name) as archive:
            files = [x for x in archive.infolist() if not x.is_dir()]
            if len(files) > MAX_ENTRIES_PER_ZIP or sum(x.file_size for x in files) > MAX_UNCOMPRESSED_BYTES:
                raise RuntimeError("GovInfo ZIP expanded content exceeds size safety bound")
            pattern = re.compile(rf"^BILLSTATUS-{CONGRESS}{kind}[1-9][0-9]*\.xml$")
            rows = []
            for info in files:
                filename = Path(info.filename).name
                if not pattern.fullmatch(filename):
                    # Do not trust arbitrary archive members.
                    continue
                if info.file_size > MAX_ENTRY_BYTES:
                    raise RuntimeError(f"GovInfo individual XML too large: {filename}")
                source_url = f"{URL_BASE}/BILLSTATUS/{CONGRESS}/{kind}/{filename}"
                rows.append(parse_bill(archive.read(info), kind, source_url, parties))
            if kind == "hr" and len(rows) < 3000:
                raise RuntimeError("House corpus unexpectedly sparse")
            if kind == "s" and len(rows) < 1000:
                raise RuntimeError("Senate corpus unexpectedly sparse")
            rows.sort(key=lambda r: r["billNumber"])
            if len({r["id"] for r in rows}) != len(rows):
                raise RuntimeError("Duplicate bill identity in official source archive")
            return rows, url

def collect():
    parties = party_roster()
    rows = []
    sources = []
    for kind in KINDS:
        result, url = ingest_zip(kind, parties)
        rows.extend(result)
        sources.append(url)
    doc = {
        "schema": "power-atlas.hyperpartisanship.govinfo-bill-cosponsors.v1",
        "status": "official_billstatus_119_core_bills_snapshot_not_historical_trend",
        "asOf": datetime.now(timezone.utc).date().isoformat(),
        "scope": "119th Congress H.R. and S. bills only; excludes joint/concurrent/simple resolutions; may include bills introduced earlier in this Congress",
        "sources": sources,
        "identityCrosswalk": "CC0 unitedstates/congress-legislators current 119th Congress from data/people/congress-members.json; party at bill's sponsorship date not independently verified",
        "methods": "Use source IDs, preserve dated cosponsor entries including withdrawn status. Unknown party is null, not assigned by name. Cross-party = at least one active known opposite-party cosponsor; null if party unknown and no known opposing cosponsor.",
        "inference": "No comparison with past Congresses, nor evidence of public interest, substantive agreement, party discipline, actual votes or illegal influence.",
        "coverage": {
            "billTypes": list(KINDS),
            "count": len(rows),
            "crossPartyTrue": sum(r["knownCrossPartyCosponsor"] is True for r in rows),
            "crossPartyFalseWithCompletePartyData": sum(r["knownCrossPartyCosponsor"] is False for r in rows),
            "crossPartyUnknown": sum(r["knownCrossPartyCosponsor"] is None for r in rows),
            "unresolvedActiveCosponsors": sum(r["activeCosponsorUnknownPartyCount"] for r in rows)
        },
        "records": rows
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n"
    if len(encoded.encode("utf-8")) > 95_000_000:
        raise RuntimeError("Research output too large for repository")
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != encoded:
        OUT.write_text(encoded, encoding="utf-8")
    print("GovInfo H.R./S. archived bill records:", len(rows), "coverage:", doc["coverage"])

if __name__ == "__main__":
    collect()
