#!/usr/bin/env python3
"""Official-source early-warning snapshots for static Eastern Axis Pages.
No credentials, scraping of personal data, speculative attribution, or invented readings.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "public" / "analysis" / "physical-early-warning.json"
SOFR_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr/last/10.json"
SOFR_SOURCE = "https://www.newyorkfed.org/markets/reference-rates/sofr"
PINK_SHEET_URL = "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx"
PINK_SHEET_SOURCE = "https://www.worldbank.org/en/research/commodity-markets"
SCORECARD_URL = "https://api.scorecard.dev/projects/github.com/{repo}"
OSS_REPOS = ("curl/curl", "openssl/openssl", "libexpat/libexpat")
MAX_BYTES = 12_000_000
CATALOG = (
    ("brent", ("crude oil, brent", "crude oil brent", "crude brent"), "Brent crude oil", "$/bbl"),
    ("us-gas", ("natural gas (u.s.)", "natural gas (us)", "natural gas, u.s.", "natural gas us"), "US natural gas", "$/mmbtu"),
    ("europe-gas", ("natural gas (europe)", "natural gas (european)"), "European natural gas", "$/mmbtu"),
    ("urea", ("urea",), "Urea fertilizer", "$/mt"),
    ("potash", ("potassium chloride",), "Potash fertilizer", "$/mt"),
    ("copper", ("copper",), "Copper", "$/mt"),
    ("coal", ("coal (australia)", "coal (australian)"), "Australian coal", "$/mt"),
)
def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def get(url: str, accept: str = "application/json") -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": "EasternAxis-PublicSourceCollector/1.0 (attributable historical observations)",
        "Accept": accept,
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise ValueError("Unexpected upstream status")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("Upstream document exceeds safety limit")
        return payload

def num(value: object) -> float:
    if isinstance(value, bool):
        raise ValueError("Boolean is not numeric source data")
    result = float(value)
    if not (-1e12 < result < 1e12):
        raise ValueError("Nonfinite or implausible number")
    return result

def change(latest: float, previous: float) -> float:
    if previous == 0:
        raise ValueError("Prior baseline cannot be zero")
    return round((latest / previous - 1) * 100, 3)

def iso_day(value: object) -> str | None:
    s = str(value or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        return None

def read_sofr(raw: bytes) -> list[dict]:
    data = json.loads(raw)
    rates = data.get("refRates")
    if not isinstance(rates, list):
        raise ValueError("NY Fed JSON lacks refRates")
    good = []
    for point in rates:
        if not isinstance(point, dict) or point.get("type") != "SOFR":
            continue
        published = iso_day(point.get("effectiveDate"))
        if not published:
            continue
        rate, volume = num(point.get("percentRate")), num(point.get("volumeInBillions"))
        if not (0 <= rate <= 50 and volume > 0):
            continue
        if date.fromisoformat(published) > date.today():
            continue
        good.append((published, rate, volume))
    good.sort(reverse=True)
    if len(good) < 2 or good[0][0] == good[1][0]:
        raise ValueError("NY Fed requires two distinct dated observations")
    latest, prior = good[:2]
    out = []
    for key, title, ix, unit, mode in (
        ("sofr-rate", "US secured overnight financing rate", 1, "% annualized", "basis-points"),
        ("sofr-volume", "SOFR overnight repo transaction volume", 2, "US$ billions", "percent")
    ):
        value, before = latest[ix], prior[ix]
        out.append({
            "id": key, "label": title, "value": value, "previous": before,
            "period": latest[0], "previousPeriod": prior[0], "interval": "daily",
            "unit": unit, "group": "US", "compareMode": mode,
            "changePct": change(value, before),
            "changeBps": round((value - before) * 100, 2) if mode == "basis-points" else None,
            "source": "Federal Reserve Bank of New York", "sourceUrl": SOFR_SOURCE
        })
    return out

def month(value: object) -> str | None:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m")
    s = str(value or "").strip()
    match = re.fullmatch(r"(\d{4})\s*[Mm-]\s*(\d{1,2})(?:-\d{1,2})?", s)
    if not match:
        return None
    y, m = int(match.group(1)), int(match.group(2))
    if not 1950 <= y <= datetime.now(timezone.utc).year or not 1 <= m <= 12:
        return None
    return f"{y:04d}-{m:02d}"

def read_pink_sheet(raw: bytes) -> list[dict]:
    from openpyxl import load_workbook
    workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    try:
        # Official monthly export commonly calls this sheet 'Monthly Prices'.
        sheet = next((w for w in workbook.worksheets if "monthly" in w.title.lower()), workbook.worksheets[0])
        rows = sheet.iter_rows(values_only=True)
        lead = [next(rows, ()) for _ in range(12)]
        head_at = None
        for i, row in enumerate(lead):
            texts = [str(x or "").lower().strip() for x in row]
            if any("copper" == x for x in texts) and any("urea" == x for x in texts):
                head_at = i
                break
        if head_at is None:
            raise ValueError("World Bank monthly header not verified")
        headers = [str(x or "").strip().lower() for x in lead[head_at]]
        indexes = {}
        for key, aliases, title, unit in CATALOG:
            pos = next((i for i, value in enumerate(headers) if value in aliases), None)
            if pos is not None:
                indexes[key] = (pos, title, unit)
        if len(indexes) < 3:
            raise ValueError("Too few verified commodity columns")
        observations: dict[str, list[tuple[str,float]]] = {k: [] for k in indexes}
        def visit(row: tuple):
            period = month(row[0] if row else "")
            if not period:
                return
            for key, (i, title, unit) in indexes.items():
                if i >= len(row) or row[i] in (None, "", "N/A"):
                    continue
                try:
                    value = num(row[i])
                except (ValueError, TypeError):
                    continue
                if value > 0:
                    observations[key].append((period, value))
        for row in lead[head_at+1:]:
            visit(row)
        for row in rows:
            visit(row)
        result = []
        for key, series in observations.items():
            series = sorted(set(series), reverse=True)
            if len(series) < 2:
                continue
            (current_date, current), (prior_date, previous) = series[:2]
            if current_date == prior_date:
                continue
            _, title, unit = indexes[key]
            result.append({
                "id": "worldbank-" + key, "label": title,
                "value": round(current, 4), "previous": round(previous, 4),
                "period": current_date, "previousPeriod": prior_date,
                "interval": "monthly", "unit": unit, "group": "global",
                "compareMode": "percent", "changePct": change(current, previous),
                "changeBps": None,
                "source": "World Bank Pink Sheet", "sourceUrl": PINK_SHEET_SOURCE
            })
        if len(result) < 3:
            raise ValueError("Too few validated recent commodity series")
        return result
    finally:
        workbook.close()

def parse_scorecard(raw: bytes, repo: str, prior: dict | None = None) -> dict:
    data = json.loads(raw)
    score = num(data["score"])
    published = str(data.get("date", ""))[:10]
    if not 0 <= score <= 10 or not iso_day(published):
        raise ValueError("Invalid OpenSSF score or date")
    checks = data.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError("Scorecard checks missing")
    byname = {c.get("name"): c.get("score") for c in checks if isinstance(c, dict)}
    previous = prior.get("score") if isinstance(prior, dict) else None
    if not isinstance(previous, (int,float)) or not 0 <= previous <= 10:
        previous = None
    return {
        "repository":repo, "score":score, "published":published,
        "previousScore":previous, "previousCheckedAt":prior.get("checkedAt") if previous is not None else None,
        "checkedAt":now(),
        "codeReview":byname.get("Code-Review") if isinstance(byname.get("Code-Review"),int) else None,
        "signedReleases":byname.get("Signed-Releases") if isinstance(byname.get("Signed-Releases"),int) else None,
        "sourceUrl":"https://scorecard.dev/viewer/?uri=github.com/"+repo,
        "method":"Public security practice indicators. A low or changing score does not imply compromise or malicious maintainers."
    }

def collect(output: Path, strict: bool = False) -> dict:
    prior = {}
    if output.exists():
        try:
            previous = json.loads(output.read_text(encoding="utf-8"))
            prior = {r["repository"]: r for r in previous.get("oss", []) if isinstance(r,dict) and isinstance(r.get("repository"),str)}
        except (OSError, ValueError, TypeError):
            pass
    data = {"schemaVersion":1,"checkedAt":now(),"status":"unavailable","metrics":[],"oss":[],"sources":[],
            "limitations":[
                "Public pricing and SOFR values are observations, not forecasts. Scope and date must be displayed.",
                "GNSS aviation anomalies cannot establish PTP drift or enterprise database failure.",
                "OpenSSF Scorecard describes software security practices; it cannot identify hostile or compromised maintainers.",
                "Commercial war-risk premiums, supplier OTIF, transformer private backlogs and calibrated cascade probabilities are not ingested.",
                "Price spikes alone do not establish future crop failure, bank panic, political instability, or causality."
            ]}
    def record(id: str, action):
        try:
            result = action()
            if not result:
                raise ValueError("No validated source observations")
            if id == "sofr" or id == "pink-sheet":
                data["metrics"].extend(result)
                detail = f"{len(result)} measurements; source period {max(r['period'] for r in result)}"
            else:
                data["oss"].append(result)
                detail = f"Published Scorecard {result['published']}; current score {result['score']}/10"
            data["sources"].append({"id":id,"status":"ok","detail":detail,"checkedAt":now()})
        except Exception as exc:
            data["sources"].append({"id":id,"status":"error","detail":type(exc).__name__+": unable to validate upstream data","checkedAt":now()})
    record("sofr",lambda:read_sofr(get(SOFR_URL)))
    record("pink-sheet",lambda:read_pink_sheet(get(PINK_SHEET_URL, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")))
    for repo in OSS_REPOS:
        record("scorecard:"+repo, lambda repo=repo:parse_scorecard(
            get(SCORECARD_URL.format(repo=repo)),repo,prior.get(repo)))
    good = sum(s["status"]=="ok" for s in data["sources"])
    data["status"] = "ok" if good == len(data["sources"]) else ("partial" if good else "unavailable")
    if strict and (not data["metrics"] or good == 0):
        raise ValueError("No verifiable official price or funding observations; retaining prior published artifact")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return data

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=DEST)
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args()
    snapshot=collect(args.output,args.strict)
    print(f"Sources OK: {sum(s['status']=='ok' for s in snapshot['sources'])}/{len(snapshot['sources'])}. "
          f"Validated metrics: {len(snapshot['metrics'])}. OSS projects: {len(snapshot['oss'])}.")
if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("Early warning collector blocked: "+str(exc),file=sys.stderr)
        sys.exit(1)
