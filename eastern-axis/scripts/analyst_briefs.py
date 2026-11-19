#!/usr/bin/env python3
"""Evidence-limited analysis of public-source titles, not an automated threat assessment.

FastEmbed supplies optional open-weight semantic similarity on the Actions runner.
If the model is unavailable, transparent rule-based source/topic indexing remains usable.
A common topic or similar headline NEVER proves independent corroboration or attribution.
"""
from __future__ import annotations

import collections
import datetime as dt
import math
import re

TOPICS = {
    "cyber": (r"\bcyber\b", r"\bransomware\b", r"\bmalware\b", r"\bhack(?:ing|ers?)?\b",
              r"\b(?:cve-\d{4}-\d+|vulnerabilit(?:y|ies)|data breach|phishing)\b"),
    "military": (r"\bmissiles?\b", r"\bdrones?\b", r"\bairstrikes?\b", r"\barmed forces\b",
                 r"\bnaval\b", r"\bdefen[cs]e\b", r"\bmilitary\b", r"\bwarfare\b",
                 r"\btroops?\b", r"\bweapons?\b", r"\bstrikes?\b", r"\bcombat\b"),
    "sanctions": (r"\bsanction(?:s|ed|ing)?\b", r"\basset freezes?\b", r"\bexport controls?\b",
                  r"\bdesignat(?:ed|ion)\b", r"\bofac\b"),
    "foreign-influence": (r"\bfara\b", r"\bforeign agents?\b", r"\blobby(?:ing|ists?)\b",
                          r"\binterference\b", r"\bcovert influence\b"),
    "power-energy": (r"\bpower grid\b", r"\belectricity\b", r"\benergy\b", r"\boil\b",
                     r"\bgas\b", r"\brefiner(?:y|ies)\b", r"\bblackouts?\b", r"\bpipeline\b"),
    "aviation": (r"\bground stops?\b", r"\bair(?:port|line|space|craft| traffic)\b",
                 r"\bflight\b", r"\baviation\b", r"\bgnss\b", r"\bgps\b"),
    "connectivity": (r"\bbgp\b", r"\bfiber\b", r"\bsubmarine cables?\b", r"\binternet\b",
                     r"\bconnectivity\b", r"\bdata cent(?:er|re)\b", r"\bcloud outage\b"),
    "humanitarian": (r"\bcivilian casualties\b", r"\brefugees?\b", r"\baid\b", r"\bhospital\b",
                     r"\bfamine\b", r"\bhumanitarian\b", r"\bdisplacement\b"),
    "trade-finance": (r"\btrade\b", r"\bfinancial\b", r"\bbank(?:ing|s)?\b",
                      r"\bsupply chain\b", r"\binflation\b", r"\bexports?\b")
}
MATCHERS = {k: tuple(re.compile(x, re.I) for x in vals) for k, vals in TOPICS.items()}

def tags(record: dict) -> list[str]:
    title = str(record.get("title") or "")
    matching = [name for name, rules in MATCHERS.items() if any(rule.search(title) for rule in rules)]
    # CISA and FARA collection names support only subject-area grouping, not factual attribution.
    kind = str(record.get("sourceId") or "").lower()
    if kind == "cisa" and "cyber" not in matching: matching.append("cyber")
    if kind == "fara" and "foreign-influence" not in matching: matching.append("foreign-influence")
    return matching or ["other"]

def _published_date(value: str | None) -> dt.date | None:
    try: return dt.date.fromisoformat(str(value or "")[:10])
    except ValueError: return None

def _source_stub(r: dict) -> dict:
    return {"id": r["id"], "title": r["title"], "url": r["url"], "publisher": r["publisher"],
            "published": r.get("date") or "", "changeType": r.get("changeType", "baseline")}

def semantic_pairs(records: list[dict], *, use_model: bool = True) -> tuple[list[dict], dict]:
    """Return related TITLE pairs, never a claim that articles confirm one another."""
    if not use_model or len(records) < 2:
        return [], {"status": "disabled" if not use_model else "insufficient-data",
                    "method": "No semantic comparison performed"}
    try:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vecs = [list(v) for v in model.embed([r["title"] for r in records])]
        if len(vecs) != len(records): raise ValueError("Embedding count mismatch")
        norms = [math.sqrt(sum(v * v for v in row)) for row in vecs]
        pairs = []
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                first, second = records[i], records[j]
                if first["publisher"] == second["publisher"]: continue
                # Avoid connecting unrelated places based on generic military language.
                a, b = set(first.get("countries", [])), set(second.get("countries", []))
                if a and b and not a.intersection(b): continue
                shared_topics = (set(tags(first)) & set(tags(second))) - {"other"}
                if not shared_topics: continue
                if not norms[i] or not norms[j]: continue
                sim = sum(x*y for x,y in zip(vecs[i], vecs[j])) / (norms[i]*norms[j])
                if sim >= .78:
                    pairs.append({"sourceIds": [first["id"], second["id"]],
                                  "topics": sorted(shared_topics), "relation": "similar-headlines",
                                  "note": "Possible overlap only; not independent corroboration"})
        pairs.sort(key=lambda item: item["sourceIds"])
        return pairs[:12], {"status": "available", "method": "Open-weight MiniLM title embeddings; threshold 0.78; cross-publisher only",
                            "model": "sentence-transformers/all-MiniLM-L6-v2"}
    except Exception as exc:
        return [], {"status": "unavailable", "method": "No semantic comparisons; source/topic indexing remains available",
                    "reason": type(exc).__name__}

def build_analysis(records: list[dict], *, use_model: bool = True) -> dict:
    """Pure evidence aggregation. Only fields taken from the validated source index."""
    countries: dict[str,list[dict]] = collections.defaultdict(list)
    topics: dict[str,list[dict]] = collections.defaultdict(list)
    today = dt.datetime.now(dt.timezone.utc).date()
    for rec in records:
        rec["topics"] = tags(rec)
        for code in rec.get("countries", []): countries[code].append(rec)
        for topic in rec["topics"]: topics[topic].append(rec)
    briefs = []
    for code, rows in sorted(countries.items()):
        pubs = sorted({r["publisher"] for r in rows})
        briefs.append({
            "code": code, "sourceCount": len(rows), "publisherCount": len(pubs),
            "publishers": pubs[:12],
            "changedCount": sum(r.get("changeType") != "baseline" for r in rows),
            "topics": sorted({t for r in rows for t in r["topics"]}),
            "sourceIds": [r["id"] for r in rows[:20]],
            "statement": f"{len(rows)} indexed public-source {'record' if len(rows)==1 else 'records'} explicitly {'mentions' if len(rows)==1 else 'mention'} {code}. This is coverage, not a threat or attribution score."
        })
    themes = []
    for topic, rows in sorted(topics.items()):
        pubs = sorted({r["publisher"] for r in rows})
        themes.append({
            "topic": topic, "sourceCount": len(rows), "publisherCount": len(pubs),
            "changedCount": sum(r.get("changeType") != "baseline" for r in rows),
            "countries": sorted({c for r in rows for c in r.get("countries", [])}),
            "sourceIds": [r["id"] for r in rows[:24]],
            "note": "Keyword indexing of publication titles; no claim that underlying events are confirmed."
        })
    themes.sort(key=lambda x: (-x["changedCount"], -x["sourceCount"], x["topic"]))
    # Missing dates remain unknown, not fresh. 30 days is a visibility metric, not an alarm.
    dates = [_published_date(r.get("date")) for r in records]
    age = sum(1 for d in dates if d is not None and (today-d).days > 30)
    unknown = sum(d is None for d in dates)
    related, model = semantic_pairs(records, use_model=use_model)
    return {
        "method": "Evidence-only title indexing and optional open-weight semantic grouping; NOT all-source threat analysis",
        "recordsAnalyzed": len(records), "countryBriefs": briefs, "themes": themes[:20],
        "relatedReports": related, "semantic": model,
        "quality": {"sourceTitlesWithoutDates": unknown, "titlesOlderThan30Days": age,
                    "publisherCount": len({r["publisher"] for r in records}),
                    "countryTaggedCount": sum(bool(r.get("countries")) for r in records)},
        "limitations": [
            "No full-document validation or human-source intelligence",
            "Source mentions do not establish military activity, guilt, intent, or causal connections",
            "Multiple sources covering one event are not necessarily independent",
            "Missing records and old dates are not evidence of low risk",
        ],
    }
