#!/usr/bin/env python3
"""Source-dated global conflict analyst. No tactical locations or inferred victories.

UCDP Candidate/GED is a delayed event-count measurement. GDELT is media
discovery only, NEVER a second independent measurement of violence. Anomaly
screens are advisory and AI cannot override freshness or evidence gates.
"""
from __future__ import annotations

import argparse
import csv
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
import io
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
from statistics import median
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public/analysis/global-conflict-watch.json"
UCDP_VERSION = os.getenv("EA_UCDP_VERSION", "26.0.10").strip()
UCDP_DOC = "https://ucdp.uu.se/downloads/"
UCDP_CSV = "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v" + UCDP_VERSION.replace(".", "_") + ".csv"
UCDP_BASELINE_CSV = "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v26_01_26_09.csv"
GDELT_DOC = "https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/"
RSS_FEEDS = (
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Deutsche Welle", "https://rss.dw.com/xml/rss-en-world"),
    ("CBC World", "https://www.cbc.ca/webfeed/rss/rss-world"),
)
WINDOW = 28
BASELINE_WINDOWS = 8
MAX_UCDP_PAGES = 120
HEADERS = {"User-Agent": "EasternAxis-OpenIntelligence/1.0 (+public-source-monitoring)", "Accept": "application/json"}

# Monitoring targets, not claims of an ongoing war or of a country's guilt.
# Grouping is deliberate: international flashpoints are not automatically wars.
THEATERS = [
    ("ukraine", "Ukraine / Russia", "Europe", ["Ukraine", "Russia"], ["UA", "RU"], "Ukraine Russia fighting ceasefire"),
    ("gaza", "Israel / Palestinian territories", "Middle East", ["Israel", "Palestine"], ["IL", "PS"], "Gaza Israel fighting ceasefire"),
    ("sudan", "Sudan", "Africa", ["Sudan"], ["SD"], "Sudan conflict fighting ceasefire"),
    ("myanmar", "Myanmar", "Asia", ["Myanmar (Burma)", "Myanmar"], ["MM"], "Myanmar fighting civilians conflict"),
    ("congo", "DR Congo", "Africa", ["DR Congo (Zaire)", "DR Congo", "Congo, Democratic Republic of the"], ["CD"], "Congo M23 conflict fighting"),
    ("yemen", "Yemen / Red Sea", "Middle East", ["Yemen (North Yemen)", "Yemen"], ["YE"], "Yemen Red Sea attacks ceasefire"),
    ("syria", "Syria", "Middle East", ["Syria"], ["SY"], "Syria fighting conflict"),
    ("somalia", "Somalia", "Africa", ["Somalia"], ["SO"], "Somalia militant attacks conflict"),
    ("sahel", "Central Sahel", "Africa", ["Mali", "Burkina Faso", "Niger"], ["ML", "BF", "NE"], "Sahel Mali Burkina Niger militant attacks"),
    ("ethiopia", "Ethiopia", "Africa", ["Ethiopia"], ["ET"], "Ethiopia conflict fighting peace"),
    ("nigeria", "Nigeria", "Africa", ["Nigeria"], ["NG"], "Nigeria insurgency fighting"),
    ("afpak", "Afghanistan / Pakistan", "Asia", ["Afghanistan", "Pakistan"], ["AF", "PK"], "Afghanistan Pakistan border attacks"),
    ("haiti", "Haiti", "Americas", ["Haiti"], ["HT"], "Haiti armed gangs violence"),
    ("south-sudan", "South Sudan", "Africa", ["South Sudan"], ["SS"], "South Sudan conflict fighting"),
    ("lebanon", "Lebanon", "Middle East", ["Lebanon"], ["LB"], "Lebanon border conflict ceasefire"),
    ("iraq", "Iraq", "Middle East", ["Iraq"], ["IQ"], "Iraq armed groups security"),
    ("taiwan", "Taiwan Strait", "Asia-Pacific", ["Taiwan", "China"], ["TW", "CN"], "Taiwan Strait military tensions"),
    ("south-china-sea", "South China Sea", "Asia-Pacific", ["Philippines", "China", "Vietnam"], ["PH", "CN", "VN"], "South China Sea naval tensions"),
    ("korea", "Korean Peninsula", "Asia-Pacific", ["North Korea", "South Korea"], ["KP", "KR"], "Korean peninsula military tensions"),
    ("caucasus", "South Caucasus", "Europe / Asia", ["Armenia", "Azerbaijan", "Georgia"], ["AM", "AZ", "GE"], "Armenia Azerbaijan border peace"),
]
# Avoid double-counting country aggregates as different conflict fronts.
# Strategic multi-country flashpoint groups remain context only.
FLASHPOINTS = {"taiwan", "south-china-sea", "korea", "caucasus"}

def now_utc():
    return datetime.now(timezone.utc)

def iso(dt):
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")

def day(value):
    try:
        stamp = str(value or "")
        # GDELT DOC returns YYYYMMDDTHHMMSSZ, unlike ISO-8601 data feeds.
        if re.match(r"^\d{8}T", stamp):
            stamp = stamp[:4] + "-" + stamp[4:6] + "-" + stamp[6:8]
        return date.fromisoformat(stamp[:10])
    except (TypeError, ValueError):
        return None

def request_json(url, timeout=18):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError("Unexpected upstream status")
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise ValueError("Upstream response exceeds size limit")
    return json.loads(raw)

def safe_evidence_url(url):
    if not isinstance(url, str):
        return None
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        return None
    if len(url) > 500 or u.port not in (None, 443):
        return None
    # No dynamic URL fetches; evidence links are displayed only.
    return url

def parse_ucdp_events(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("Result"), list):
        raise ValueError("Unexpected UCDP API payload")
    clean = []
    for row in payload["Result"]:
        if not isinstance(row, dict):
            continue
        observed = day(row.get("date_start"))
        country = str(row.get("country") or "").strip()
        if not observed or not country:
            continue
        try:
            fatalities = max(0, int(float(row.get("best") or 0)))
        except (TypeError, ValueError, OverflowError):
            fatalities = 0
        clean.append({"date": observed, "country": country, "fatalities": fatalities,
                      "id": str(row.get("id") or ""), "actors": [
                          str(row.get("side_a") or "")[:90],
                          str(row.get("side_b") or "")[:90]]})
    return clean

def collect_ucdp(version=UCDP_VERSION, reader=None):
    """Join UCDP's January-September cumulative and October monthly releases.

    UCDP 26.0.10 contains *October only*. A one-month file cannot establish a
    historical anomaly baseline. Both official license-compatible releases are
    mandatory. Never treat a partial year as a verified complete annual history.
    """
    if not re.fullmatch(r"\d{2}\.\d{1,2}(?:\.\d{1,2}){0,3}", version):
        raise ValueError("Invalid UCDP candidate version")
    if version != "26.0.10":
        raise ValueError("Unreviewed UCDP release version; update the source manifest")
    latest_url = "https://ucdp.uu.se/downloads/candidateged/GEDEvent_v" + version.replace(".", "_") + ".csv"
    sources = (("jan-sep-2026", UCDP_BASELINE_CSV),
               ("oct-2026", latest_url))
    events, seen, covered = [], set(), {}
    today = now_utc().date()
    for release, url in sources:
        if reader is None:
            req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
            with urllib.request.urlopen(req, timeout=38) as response:
                data = response.read(32_000_001)
        else:
            data = reader(url)
        if not isinstance(data, bytes) or not 0 < len(data) <= 32_000_000:
            raise ValueError("Missing, oversized or invalid UCDP release: " + release)
        table = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
        if not table.fieldnames or not {"id", "country", "date_start"}.issubset(set(table.fieldnames)):
            raise ValueError("UCDP CSV schema mismatch: " + release)
        release_count = 0
        release_min, release_max = None, None
        for row in table:
            if not isinstance(row, dict):
                continue
            for item in parse_ucdp_events({"Result": [row]}):
                if item["date"] > today or item["date"] < today - timedelta(days=400):
                    continue
                key = item["id"] or (item["date"], item["country"], item["fatalities"])
                if key in seen:
                    continue
                seen.add(key)
                events.append(item)
                release_count += 1
                release_min = min(release_min, item["date"]) if release_min else item["date"]
                release_max = max(release_max, item["date"]) if release_max else item["date"]
        if release_count == 0:
            raise ValueError("UCDP historical release empty or duplicated: " + release)
        covered[release] = {"rows": release_count, "url": url,
                            "earliest": release_min.isoformat(),
                            "latest": release_max.isoformat()}
    earliest = min(e["date"] for e in events)
    latest = max(e["date"] for e in events)
    if (latest - earliest).days < 252:
        raise ValueError("Combined UCDP releases do not cover 8 complete historical windows")
    return events, {"status": "ok", "rows": len(events), "format": "two official downloadable CSV releases",
                    "version": version, "url": UCDP_DOC,
                    "releases": covered, "earliest": earliest.isoformat(),
                    "latest": latest.isoformat(),
                    "attribution": "UCDP Candidate Events, Hegre et al. (2020), CC BY 4.0",
                    "measurement": "Retrospectively coded candidate events, not current battlefield intelligence"}

def parse_gdelt_articles(payload, today=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise ValueError("Unexpected GDELT article payload")
    today = today or now_utc().date()
    articles, seen = [], set()
    for row in payload["articles"]:
        if not isinstance(row, dict):
            continue
        url = safe_evidence_url(row.get("url"))
        observed = day(row.get("seendate") or row.get("date"))
        if not url or not observed or not 0 <= (today - observed).days <= 10:
            continue
        host = urllib.parse.urlsplit(url).hostname.lower()
        if url in seen:
            continue
        seen.add(url)
        articles.append({"id": "news-" + str(len(articles) + 1),
                         "title": str(row.get("title") or "Source article")[:180],
                         "date": observed.isoformat(), "publisher": host, "url": url})
    return articles

def collect_gdelt(query, reader=request_json):
    params = urllib.parse.urlencode({"query": query, "mode": "artlist",
                                     "format": "json", "timespan": "7d",
                                     "sort": "datedesc", "maxrecords": 65})
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + params
    return parse_gdelt_articles(reader(url, timeout=12))

def parse_public_rss(payload, publisher, checked=None):
    """Parse independent editorial RSS with direct HTTPS article citations."""
    if not isinstance(payload, (bytes, str)):
        raise ValueError("Invalid RSS payload")
    raw = payload if isinstance(payload, bytes) else payload.encode()
    if not raw or len(raw) > 5_000_000:
        raise ValueError("Oversized/empty RSS feed")
    root = ET.fromstring(raw)
    checked = checked or now_utc().date()
    records, seen = [], set()
    for entry in root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("title") or entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        url = entry.findtext("link")
        if not url:
            link = entry.find("{http://www.w3.org/2005/Atom}link")
            url = link.get("href") if link is not None else None
        url = safe_evidence_url(url)
        raw_date = (entry.findtext("pubDate") or entry.findtext("date") or
                    entry.findtext("{http://purl.org/dc/elements/1.1/}date") or
                    entry.findtext("{http://www.w3.org/2005/Atom}updated"))
        stamp = day(raw_date)
        if not stamp:
            try:
                stamp = parsedate_to_datetime(raw_date or "").date()
            except (ValueError, TypeError, OverflowError):
                continue
        if not (url and title and stamp and 0 <= (checked - stamp).days <= 10) or url in seen:
            continue
        seen.add(url)
        records.append({"id": "rss-" + str(len(records) + 1),
                        "title": re.sub(r"<[^>]*>", "", title)[:180],
                        "date": stamp.isoformat(), "publisher": publisher, "url": url})
    return records


def collect_public_rss(reader=None):
    article_index, health = [], []
    for publisher, url in RSS_FEEDS:
        try:
            if reader is None:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=14) as response:
                    raw = response.read(5_000_001)
            else:
                raw = reader(url)
            rows = parse_public_rss(raw, publisher)
            article_index.extend(rows)
            health.append({"name": publisher, "status": "ok", "articles": len(rows), "url": url})
        except (ET.ParseError, OSError, ValueError, TypeError):
            health.append({"name": publisher, "status": "unavailable", "articles": 0, "url": url})
    return article_index, health


NEWS_TOPICS = {
    "ukraine": ("ukraine", "kyiv"), "gaza": ("gaza", "palestinian", "israel"),
    "sudan": ("sudan",), "myanmar": ("myanmar", "burma"),
    "congo": ("congo", "m23", "kinshasa"), "yemen": ("yemen", "houthi", "red sea"),
    "syria": ("syria", "damascus"), "somalia": ("somalia", "mogadishu"),
    "sahel": ("sahel", "burkina faso", "mali", "niger"),
    "ethiopia": ("ethiopia", "tigray"), "nigeria": ("nigeria", "boko haram"),
    "afpak": ("afghanistan", "pakistan", "taliban"),
    "haiti": ("haiti",), "south-sudan": ("south sudan",),
    "lebanon": ("lebanon", "hezbollah"), "iraq": ("iraq", "baghdad"),
    "taiwan": ("taiwan",), "south-china-sea": ("south china sea", "philippines"),
    "korea": ("north korea", "south korea", "korean"), "caucasus": ("armenia", "azerbaijan"),
}


def match_rss_to_theaters(articles, health):
    available = any(h["status"] == "ok" for h in health)
    index = {}
    for slug, _, _, _, _, _ in THEATERS:
        words = NEWS_TOPICS[slug]
        matched = []
        for row in articles:
            title = row["title"].lower()
            if slug == "sudan" and "south sudan" in title:
                continue
            if any(re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", title) for word in words):
                matched.append(row)
        index[slug] = {"status": "ok" if available else "unavailable",
                       "articles": sorted(matched, key=lambda x: x["date"], reverse=True)[:25]}
    return index


def country_alias(name):
    value = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    replacements = {
        "democratic republic of congo": "dr congo", "congo democratic republic of the": "dr congo",
        "dr congo zaire": "dr congo", "myanmar burma": "myanmar",
        "yemen north yemen": "yemen", "palestine": "palestine",
        "israel": "israel", "russia soviet union": "russia"
    }
    return replacements.get(value, value)

def score_history(counts, anchor, first_date):
    # The latest data day is an OBSERVATION-period anchor, never "today".
    if not anchor or not first_date or first_date > anchor - timedelta(days=WINDOW * (BASELINE_WINDOWS + 1) - 1):
        return {"status": "insufficient", "history": [], "recent": None, "median": None,
                "robustZ": None, "changePct": None, "direction": "unassessed"}
    history = []
    for i in range(BASELINE_WINDOWS, 0, -1):
        end = anchor - timedelta(days=WINDOW * i)
        start = end - timedelta(days=WINDOW - 1)
        history.append(sum(v for stamp, v in counts.items() if start <= stamp <= end))
    recent_start = anchor - timedelta(days=WINDOW - 1)
    recent = sum(v for stamp, v in counts.items() if recent_start <= stamp <= anchor)
    med = median(history)
    mad = median([abs(n - med) for n in history])
    scale = max(1.0, 1.4826 * mad, math.sqrt(med + 1))
    z = (recent - med) / scale
    change = None if med <= 0 else (recent / med - 1) * 100
    direction = "stable"
    if z >= 3 and recent >= 8 and recent >= 1.4 * max(1, med):
        direction = "deteriorating"
    elif z <= -3 and med >= 8 and recent <= 0.6 * med:
        direction = "improving"
    return {"status": "assessable", "history": history, "recent": recent,
            "median": round(med, 1), "robustZ": round(z, 2),
            "changePct": round(change, 1) if change is not None else None,
            "direction": direction}

def select_diverse_evidence(articles, limit=5):
    """Use separate publishers before repeated reports from the same outlet."""
    rows, seen_urls, publishers = [], set(), set()
    for article in articles:
        if article["publisher"] not in publishers and article["url"] not in seen_urls:
            rows.append(article)
            seen_urls.add(article["url"])
            publishers.add(article["publisher"])
        if len(rows) >= limit:
            return rows
    for article in articles:
        if article["url"] not in seen_urls:
            rows.append(article)
            seen_urls.add(article["url"])
        if len(rows) >= limit:
            break
    return rows


def assess(events, media_by_theater, checked_at=None):
    checked_at = checked_at or now_utc()
    anchor = max((e["date"] for e in events), default=None)
    first_date = min((e["date"] for e in events), default=None)
    age = (checked_at.date() - anchor).days if anchor else None
    # Annual/year-to-date completion does NOT imply that a newly coded conflict
    # event has occurred in every country.
    fresh = age is not None and 0 <= age <= 45
    groups = defaultdict(list)
    for ev in events:
        groups[country_alias(ev["country"])].append(ev)
    zones = []
    for slug, name, region, aliases, codes, query in THEATERS:
        area_events = []
        for alias in set(country_alias(a) for a in aliases):
            area_events.extend(groups.get(alias, []))
        counts = Counter(e["date"] for e in area_events)
        history = score_history(counts, anchor, first_date)
        media = media_by_theater.get(slug, {})
        articles = media.get("articles", [])
        publishers = len({a["publisher"] for a in articles})
        coverage = media.get("status", "unavailable")
        # GDELT publisher breadth is not independent event-count corroboration.
        candidate = (slug not in FLASHPOINTS and fresh and
                     history["direction"] in ("deteriorating", "improving"))
        assessment = {
            "id": slug, "name": name, "region": region, "countryCodes": codes,
            "kind": "strategic-flashpoint" if slug in FLASHPOINTS else "armed-conflict-watch",
            "status": "review" if candidate else ("data-gap" if history["status"] != "assessable" else "monitor"),
            "direction": history["direction"], "change": history, "observationEnd": anchor.isoformat() if anchor else None,
            "measurementFresh": fresh, "modelReviewed": False, "promoted": False,
            "sourceQuality": "coded-events" if history["status"] == "assessable" else "insufficient",
            "sourceCount": 1 if events else 0,
            "media": {"status": coverage, "articles": len(articles), "publishers": publishers,
                      "evidence": select_diverse_evidence(articles), "limitation": "Editorial news context, not event or death verification"},
            "actors": [actor for actor, count in Counter(a for e in area_events[-120:] for a in e["actors"] if a).most_common(5)],
            "whoBenefits": "Not established. Named participants are not proof of battlefield advantage.",
            "globalRisks": "Potential humanitarian, displacement, diplomatic and supply-chain spillovers; specific pathways require corroboration.",
            "potentialUpside": "A verified durable de-escalation could reduce civilian harm and cross-border disruption; no outcome is predicted.",
            "reason": ("Coded violence outside this theater's 8-window baseline; needs independent review."
                       if candidate else "Monitoring; no independently confirmed current exceptional shift."),
            "evidence": [{"source": "UCDP Candidate", "url": UCDP_CSV,
                          "observedAt": anchor.isoformat() if anchor else None,
                          "kind": "event-history"}] if history["status"] == "assessable" else [],
        }
        zones.append(assessment)
    return zones, {"latestCodedEvent": anchor.isoformat() if anchor else None,
                   "firstCodedEvent": first_date.isoformat() if first_date else None,
                   "dataAgeDays": age, "eventCount": len(events),
                   "eventFresh": fresh, "worldwideCompleteness": "not asserted"}

def model_review(record, endpoint, model="qwen2.5:1.5b"):
    evidence = record["media"]["evidence"]
    # AI may review a UCDP anomaly without same-period media; independent
    # corroboration still vetoes publication as an assessed exception.
    # Bounded evidence only; a single media article or UCDP aggregate cannot
    # substantiate that a named faction benefits materially from an escalation.
    brief = {"id": record["id"], "theater": record["name"],
             "eventCounts": record["change"], "observationEnd": record["observationEnd"],
             "articleSources": evidence, "actorsMentionedNotWinners": record["actors"]}
    prompt = (
        "You are a cautious strategic conflict analyst. Consider ONLY the provided "
        "source-dated evidence. Editorial articles are coverage, not independently measured "
        "conflict counts. Provide conditional plausible risks and potential de-escalation "
        "benefits for the broader world. Do not claim an actor benefits or that conditions "
        "are current without an article explicitly supporting that conclusion. "
        "Never state tactical positions, force movements or targets. "
        "Return one JSON object with keys id,decision,whoBenefits,globalRisks,potentialUpside,"
        "reason,confidence. decision must be monitor or review, confidence low or medium; "
        "all four narrative strings 15-350 characters. Do not invent facts or URLs. Input: "
        + json.dumps(brief, ensure_ascii=False))
    payload = json.dumps({"model": model, "format": "json", "stream": False,
                          "options": {"temperature": 0, "num_predict": 500},
                          "prompt": prompt}).encode()
    req = urllib.request.Request(endpoint.rstrip("/") + "/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            answer = json.loads(json.load(response).get("response", ""))
        if not isinstance(answer, dict) or answer.get("id") != record["id"]:
            return None
        if answer.get("decision") not in ("monitor", "review") or answer.get("confidence") not in ("low", "medium"):
            return None
        for key in ("whoBenefits", "globalRisks", "potentialUpside", "reason"):
            if not isinstance(answer.get(key), str) or not 15 <= len(answer[key]) <= 350:
                return None
        return answer
    except (OSError, ValueError, TypeError, KeyError):
        return None

def evaluate(events, media, *, checked_at=None, model_endpoint=""):
    checked_at = checked_at or now_utc()
    zones, stats = assess(events, media, checked_at)
    reviewed = 0
    for record in zones:
        if record["status"] != "review":
            continue
        answer = model_review(record, model_endpoint) if model_endpoint else None
        if answer:
            reviewed += 1
            record["modelReviewed"] = True
            record["whoBenefits"] = answer["whoBenefits"]
            record["globalRisks"] = answer["globalRisks"]
            record["potentialUpside"] = answer["potentialUpside"]
            record["reason"] = answer["reason"]
            # Publication in Defense is analytical triage, not confirmation
            # of near-real-time battlefield direction or automatic Command alert.
            if answer["decision"] == "review":
                record["status"] = "assessed"
                record["promoted"] = True
                record["sourceQuality"] = "coded-events-with-media-context"
    return zones, stats, reviewed

def build(*, model_endpoint="", ucdp_reader=request_json, gdelt_reader=request_json):
    checked = now_utc()
    events, ucdp_status = [], {"status": "unavailable", "version": UCDP_VERSION, "url": UCDP_DOC}
    try:
        events, ucdp_status = collect_ucdp()
    except (OSError, ValueError, TypeError, KeyError) as error:
        ucdp_status["error"] = type(error).__name__
    # Reusable RSS is the free default; GDELT is optional enrichment, not
    # required for functioning source trails or independently measured violence.
    feed_articles, feed_health = collect_public_rss()
    media = match_rss_to_theaters(feed_articles, feed_health)
    gdelt_ok = 0
    if os.getenv("EA_ENABLE_GDELT") == "1":
        for slug, _, _, _, _, query in THEATERS:
            try:
                latest = collect_gdelt(query, reader=gdelt_reader)
                seen = {a["url"] for a in media[slug]["articles"]}
                media[slug]["articles"].extend(a for a in latest if a["url"] not in seen)
                gdelt_ok += 1
            except (OSError, ValueError, TypeError, KeyError):
                pass
    zones, stats, reviewed = evaluate(events, media, checked_at=checked, model_endpoint=model_endpoint)
    # In an unavailable/partial event feed, never describe zero results as zero incidents.
    state = "ok" if ucdp_status["status"] == "ok" else "partial"
    if state != "ok":
        for row in zones:
            row["status"] = "data-gap"
            row["sourceQuality"] = "unavailable"
            row["reason"] = "Coded conflict feed unavailable; no exceptional-violence finding asserted."
    return {
        "schemaVersion": 1, "generatedAt": iso(checked),
        "status": state, "category": "Defense, Security & Cyber",
        "analyst": {"name": "Global Conflict & Hotspot Analyst",
                    "model": "qwen2.5:1.5b" if model_endpoint else None,
                    "modelStatus": "reviewed" if reviewed else ("unavailable" if model_endpoint else "not-run"),
                    "reviewed": reviewed,
                    "gate": "8 dated 28-day baselines + robust anomaly + fresh coded observations + 3 independent news publishers + bounded AI review",
                    "commandEligible": 0,
                    "methodology": "Strategic, delayed, civilian-focused. No verified battlefield positions."},
        "sources": {"ucdp": ucdp_status,
                    "rss": {"status": "ok" if any(h["status"] == "ok" for h in feed_health) else "unavailable",
                            "feeds": feed_health,
                            "publishers": sum(h["status"] == "ok" for h in feed_health),
                            "type": "public-editorial-media-context-not-event-verification"},
                    "gdelt": {"status": "ok" if gdelt_ok else "disabled-or-unavailable",
                              "targets": gdelt_ok, "url": GDELT_DOC,
                              "type": "optional-media-monitoring-only"}},
        "measurement": stats,
        "summary": {"hotspots": len(zones), "assessed": sum(z["promoted"] for z in zones),
                    "deteriorating": sum(z["promoted"] and z["direction"] == "deteriorating" for z in zones),
                    "improving": sum(z["promoted"] and z["direction"] == "improving" for z in zones),
                    "awaitingReview": sum(z["status"] == "review" for z in zones),
                    "monitored": sum(z["status"] == "monitor" for z in zones),
                    "coverageGaps": sum(z["status"] == "data-gap" for z in zones)},
        "zones": zones, "limitations": [
            "Hotspots are monitoring scopes, not a certified list of active wars.",
            "UCDP candidate events are coded retrospectively. The latest coded event is not a completeness date.",
            "Country aggregates cannot isolate a border or subnational theater; multinational flashpoints are context-only.",
            "Changes in coded violence are not proof of territorial advantage, who benefits, or a future outcome.",
            "Publisher variety and reporting frequency cannot independently verify casualties, coded event counts or severity.",
            "Unavailable feeds, insufficient baseline and missing AI review cannot create a promoted assessment.",
            "No automatic Command Center promotion; that requires a separate multi-source operational validation gate."
        ]
    }


def aligned_evidence_period(record):
    """Bounded recent editorial context; never confirms coded-event counts."""
    last = day(record.get("observationEnd"))
    if not last:
        return False
    return len({a.get("publisher") for a in record.get("media", {}).get("evidence", [])
                if day(a.get("date")) and 0 <= (day(a["date"]) - last).days <= 45}) >= 3

def apply_review(report, endpoint):
    reviewed = 0
    if not endpoint:
        return report
    for record in report.get("zones", []):
        if record.get("status") != "review" or reviewed >= 8:
            continue
        answer = model_review(record, endpoint)
        if not answer:
            continue
        record["modelReviewed"] = True
        reviewed += 1
        record["whoBenefits"] = "Analyst hypothesis, unverified: " + answer["whoBenefits"]
        record["globalRisks"] = answer["globalRisks"]
        record["potentialUpside"] = answer["potentialUpside"]
        if answer["decision"] == "review" and aligned_evidence_period(record):
            record["promoted"] = True
            record["status"] = "assessed"
            record["reason"] = answer["reason"]
            record["sourceQuality"] = "coded-events-with-period-matched-media-context"
        else:
            record["reason"] = "Source dates or corroboration insufficient for publishing a fresh exception. " + answer["reason"][:170]
    report["analyst"]["reviewed"] = reviewed
    report["analyst"]["modelStatus"] = "reviewed" if reviewed else "unavailable"
    report["summary"]["assessed"] = sum(r["promoted"] for r in report["zones"])
    report["summary"]["deteriorating"] = sum(r["promoted"] and r["direction"] == "deteriorating" for r in report["zones"])
    report["summary"]["improving"] = sum(r["promoted"] and r["direction"] == "improving" for r in report["zones"])
    report["summary"]["awaitingReview"] = sum(r["status"] == "review" for r in report["zones"])
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--model-endpoint", default="")
    parser.add_argument("--review-only", action="store_true")
    args = parser.parse_args()
    if args.review_only:
        if not args.output.exists() or not args.model_endpoint:
            raise SystemExit("Review requires an existing snapshot and a local model endpoint")
        report = apply_review(json.loads(args.output.read_text()), args.model_endpoint)
    else:
        report = build(model_endpoint="")
        if args.model_endpoint:
            report = apply_review(report, args.model_endpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("Global conflict analysis:", report["status"], report["summary"],
          "coded through", report["measurement"]["latestCodedEvent"])

if __name__ == "__main__":
    main()
