"""Reference-first audit tripwire for Power Atlas.

No network calls, scraping, PDF downloads, or automatic changes to a public
claim. A provider adapter may inject a bounded HTTP response and extracted
text. This module categorizes observations and requests human review.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Iterable
from urllib.error import HTTPError


@dataclass(frozen=True)
class Retrieved:
    http_status: int
    content_type: str
    body: bytes


@dataclass(frozen=True)
class Extracted:
    text: str
    clean: bool = True


@dataclass(frozen=True)
class AuditOutcome:
    check_state: str
    expected_excerpt_found: bool | None
    human_review_required: bool
    publication_action: str = "none"
    public_warning: bool = False
    note: str = ""


def normalized_tokens(value: str) -> tuple[str, ...]:
    """Ignore formatting, not meaningful numeric decimal/grouping punctuation.

    2.836 and 28.36 must NEVER collapse to the same numeric value.
    """
    clean = unicodedata.normalize("NFKC", value).casefold()
    clean = clean.replace("\u200b", "").replace("\ufeff", "")
    return tuple(re.findall(r"\d+(?:[.,]\d+)*|[^\W\d_]+", clean, re.UNICODE))


def contains_expected(text: str, excerpt: str) -> bool:
    hay = normalized_tokens(text)
    needle = normalized_tokens(excerpt)
    if not needle:
        raise ValueError("Source excerpt may not be blank")
    return any(hay[i:i + len(needle)] == needle
               for i in range(0, len(hay) - len(needle) + 1))


def looks_readable(content: str) -> bool:
    if not isinstance(content, str):
        return False
    tokens = normalized_tokens(content)
    if len(tokens) < 5 or sum(ch.isalnum() for ch in content) < 25:
        return False
    printable = sum(ch.isprintable() or ch.isspace() for ch in content)
    return printable / max(1, len(content)) > .90


def looks_blocked(body: bytes) -> bool:
    # Conservatively treat known access-challenge shapes as access problems,
    # not as official documents that have changed.
    head = body[:6000].decode("utf-8", errors="replace").casefold()
    return any(marker in head for marker in (
        "cf-chl-", "checking your browser before accessing", 
        "verify you are human", "<title>just a moment", 
        "cloudflare ray id", "captcha challenge"
    ))


def consecutive_404_days(today: date, prior: Iterable[tuple[date, str]]) -> int:
    # Do not count multiple same-day requests as independent days.
    by_date = {when: state for when, state in prior if when < today}
    days = 1
    for n in range(1, 3):
        if by_date.get(today - timedelta(days=n)) != "hard_404":
            break
        days += 1
    return days


def inspect_reference(
    expected_excerpt: str,
    observed_on: date,
    fetch: Callable[[], Retrieved],
    extract: Callable[[Retrieved], Extracted],
    prior_checks: Iterable[tuple[date, str]] = (),
) -> AuditOutcome:
    if not normalized_tokens(expected_excerpt):
        raise ValueError("Live reference requires a non-empty expected excerpt")
    try:
        response = fetch()
    except HTTPError as err:
        status = err.code
        if status == 404:
            days = consecutive_404_days(observed_on, prior_checks)
            return AuditOutcome("dead_link_review_candidate" if days >= 3 else "hard_404",
                                None, days >= 3, note="HTTP 404; source removal not established")
        return AuditOutcome("access_blocked" if status in (401,403,429) else "http_error",
                            None, False, note=f"HTTP {status}")
    except (TimeoutError, ConnectionError, OSError):
        return AuditOutcome("http_error", None, False, note="Network/access error, retry separately")
    if response.http_status == 404:
        days = consecutive_404_days(observed_on, prior_checks)
        return AuditOutcome("dead_link_review_candidate" if days >= 3 else "hard_404",
                            None, days >= 3, note="Repeated missing link needs human review")
    if response.http_status in (401,403,429):
        return AuditOutcome("access_blocked", None, False, note="Access blocked or limited")
    if response.http_status != 200:
        return AuditOutcome("http_error", None, False, note=f"HTTP {response.http_status}")
    if not response.body or looks_blocked(response.body):
        return AuditOutcome("access_blocked" if response.body else "parse_error",
                            None, False, note="Unusable response body or access challenge")
    try:
        parsed = extract(response)
    except (ValueError, UnicodeError, RuntimeError):
        return AuditOutcome("parse_error", None, False, note="Source extractor failed")
    if not isinstance(parsed, Extracted) or not parsed.clean or not looks_readable(parsed.text):
        return AuditOutcome("parse_error", None, False, note="Extraction not reliable")
    if contains_expected(parsed.text, expected_excerpt):
        return AuditOutcome("content_verified", True, False, note="Located excerpt in clean extraction")
    return AuditOutcome("pending_manual_review", False, True,
                        note="Clean extraction lacks excerpt; no claim of record alteration")


def reviewer_disposition(
    audit: AuditOutcome, *, reviewer_id: str, reviewed_original: bool,
    decision: str,
) -> dict:
    """Only an explicit human review can label a substantive source change."""
    if not reviewer_id.strip() or not reviewed_original:
        raise ValueError("Human reviewer and original-record inspection required")
    if decision not in {"unchanged", "source_changed", "inconclusive"}:
        raise ValueError("Unsupported human disposition")
    if audit.check_state != "pending_manual_review" and decision == "source_changed":
        raise ValueError("Only clean-extraction discrepancy can be adjudicated as source change")
    return {"manual_disposition": decision, "reviewed_by": reviewer_id,
            "publication_action": "request_editorial_reassessment" if decision == "source_changed" else "none",
            "automatic_claim_retraction": False}
