#!/usr/bin/env python3
"""Polite, source-verified snapshot of DOJ FARA active registrants.

This index contains registration metadata only. A FARA filing is not proof of
misconduct, state control, or any particular foreign-principal country.
Never replace a good snapshot with a partial, unparseable, or 429 response.
"""
import datetime
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

URL = "https://efile.fara.gov/api/v1/Registrants/json/Active"
OUTPUT = pathlib.Path(__file__).resolve().parents[1] / "backend/faraSnapshot.json"
MAX_BYTES = 6_000_000

def main():
    headers = {
        "Accept": "application/json",
        "User-Agent": "EasternAxisPublicResearch/1.0 (daily official-source index)"
    }
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers=headers), timeout=30) as response:
            if response.status != 200:
                raise RuntimeError("DOJ FARA unexpected status {}".format(response.status))
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise RuntimeError("DOJ FARA response exceeds configured size")
    except urllib.error.HTTPError as exc:
        # Do not request repeatedly after a rate limit, or fall back to untrusted data.
        if exc.code == 429:
            print("DOJ FARA rate-limited this collection (HTTP 429); prior verified snapshot kept.", file=sys.stderr)
        raise
    data = json.loads(raw.decode("utf-8-sig"))
    top = data.get("REGISTRANTS_ACTIVE") if isinstance(data, dict) else None
    entries = top.get("ROW") if isinstance(top, dict) else None
    if not isinstance(entries, list) or len(entries) < 300:
        raise RuntimeError("DOJ FARA response incomplete or schema changed")
    rows = []
    seen = set()
    for item in entries:
        if not isinstance(item, dict):
            continue
        n, s, d = item.get("Registration_Number"), item.get("Name"), item.get("Registration_Date")
        if not (str(n).isdigit() and isinstance(s, str) and s.strip() and isinstance(d, str)):
            continue
        n = int(n)
        if n in seen or n < 1 or n > 99999999 or not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d):
            continue
        seen.add(n)
        rows.append({"n": n, "s": " ".join(s.split())[:240], "d": d})
    rows.sort(key=lambda r: r["n"], reverse=True)
    if len(rows) < 300 or len(rows) < int(len(entries) * 0.9):
        raise RuntimeError("DOJ FARA validation failed: too few distinct dated entries")
    digest = hashlib.sha256(raw).hexdigest()
    prior = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    if prior.get("originalSha256") == digest and prior.get("coverage") == "complete-official-source":
        print("Official DOJ FARA source identical; no snapshot change.")
        return
    snapshot = {
        "schema": "ea-fara-active-snapshot-v1",
        "source": URL,
        "retrievedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "originalSha256": digest,
        "total": len(rows),
        "coverage": "complete-official-source",
        "rows": rows
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Verified {} distinct active FARA registrations; digest {}".format(len(rows), digest[:14]))

if __name__ == "__main__":
    main()
