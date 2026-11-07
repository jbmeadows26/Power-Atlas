"""Uncertainty-preserving arithmetic for public annual financial disclosures.

Annual holdings are NOT periodic transaction report flows. This represents only
the schedules actually reported: it is not audited personal net worth.
"""
from decimal import Decimal, InvalidOperation

OWNER_TYPES = {"self", "spouse", "joint", "dependent", "unattributed"}

def _money(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("Missing or invalid amount; unknown must not be zero")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Non-numeric disclosure amount") from exc
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ValueError("Disclosure band must have a finite nonnegative integer USD value")
    return int(number)

def disclosure_band(item):
    if item.get("owner") not in OWNER_TYPES:
        raise ValueError("Must preserve owner of disclosed position")
    if item.get("valueStatus") not in ("reported_range", "reported_open_upper"):
        raise ValueError("Unvalued or ambiguous asset is not zero")
    lo = _money(item.get("valueMinUSD"))
    hi = item.get("valueMaxUSD")
    if item["valueStatus"] == "reported_open_upper":
        if hi is not None:
            raise ValueError("Open-upper bands must have no reported upper bound")
        return lo, None
    hi = _money(hi)
    if hi < lo:
        raise ValueError("Disclosure amount bounds reversed")
    return lo, hi

def sum_section(rows, complete):
    if complete is not True or not isinstance(rows, list):
        return None
    lower = 0
    upper = 0
    for row in rows:
        lo, hi = disclosure_band(row)
        lower += lo
        upper = None if upper is None or hi is None else upper + hi
    return {"lowerUSD": lower, "upperUSD": upper}

def disclosed_position_interval(assets, liabilities, *,
                                asset_section_complete=False,
                                liability_section_complete=False):
    """Combine annual asset and debt bands; no median, no midpoint, no imputation.

    Zero holdings is valid only for a fully verified empty assets schedule.
    Liabilities can be declared even when paid by the year end. The source
    filing may exempt primary residences, spouse assets and blind trusts.
    """
    asset_range = sum_section(assets, asset_section_complete)
    liability_range = sum_section(liabilities, liability_section_complete)
    if asset_range is None or liability_range is None:
        return {
            "status": "not_estimable_incomplete_schedules",
            "assets": asset_range, "liabilities": liability_range,
            "disclosedNetLowerUSD": None, "disclosedNetUpperUSD": None,
        }
    net_lo = (None if liability_range["upperUSD"] is None else
              asset_range["lowerUSD"] - liability_range["upperUSD"])
    net_hi = (None if asset_range["upperUSD"] is None else
              asset_range["upperUSD"] - liability_range["lowerUSD"])
    return {
        "status": "reported_schedules_only_not_personal_net_worth",
        "assets": asset_range, "liabilities": liability_range,
        "disclosedNetLowerUSD": net_lo, "disclosedNetUpperUSD": net_hi,
    }

# Evidence-layer checks: numeric interval arithmetic is insufficient for
# publishing a member-level observation without a traceable original filing.
from datetime import date
from urllib.parse import urlsplit

OFFICIAL_FILING_HOSTS = {"disclosures-clerk.house.gov", "efdsearch.senate.gov"}
VALID_REPORT_TYPES = {"annual", "amended_annual"}

def validate_member_annual_disclosure(record):
    """Validate a source-attributed annual disclosure, preserving nulls.

    Returns normalized interval arithmetic only for explicitly complete
    source-verified asset AND liability schedules. It does not estimate
    undisclosed property or overall personal net worth.
    """
    if not isinstance(record, dict):
        raise ValueError("Disclosure record must be an object")
    member_id = record.get("bioguideId")
    if not isinstance(member_id, str) or not __import__("re").fullmatch(r"[A-Z][0-9]{6}", member_id):
        raise ValueError("A validated Bioguide ID is required")
    if record.get("reportType") not in VALID_REPORT_TYPES:
        raise ValueError("Periodic trades and annual holdings cannot be merged")
    url = record.get("originalFilingURL")
    if not isinstance(url, str):
        raise ValueError("Missing primary source URL")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in OFFICIAL_FILING_HOSTS
            or parsed.username is not None or parsed.password is not None
            or not parsed.path or parsed.path == "/"):
        raise ValueError("Original filing must be a direct official HTTPS document")
    for key in ("filingDate", "observedAt"):
        value = record.get(key)
        if not isinstance(value, str):
            raise ValueError("Missing filing or observation date")
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Invalid ISO source date") from exc
    if record["filingDate"] > record["observedAt"]:
        raise ValueError("Filing cannot postdate evidence observation")
    if record.get("licenseOrReuseRestriction") is None:
        raise ValueError("Missing source reuse restriction")
    if record.get("filingIdentity") in (None, ""):
        raise ValueError("Missing filing identifier for amendment reconciliation")
    assets = record.get("assets")
    liabilities = record.get("liabilities")
    for rows in (assets, liabilities):
        if not isinstance(rows, list):
            raise ValueError("Missing schedule rows must be explicit empty or unknown")
        for row in rows:
            if not isinstance(row, dict) or row.get("sourcePage") is None:
                raise ValueError("Each financial range needs a filing page/section locator")
    verified = record.get("primarySourceVerified") is True
    asset_complete = verified and record.get("assetScheduleComplete") is True
    liability_complete = verified and record.get("liabilityScheduleComplete") is True
    result = disclosed_position_interval(
        assets, liabilities,
        asset_section_complete=asset_complete,
        liability_section_complete=liability_complete,
    )
    return {
        "bioguideId": member_id,
        "filingIdentity": record["filingIdentity"],
        "originalFilingURL": url,
        "filingDate": record["filingDate"],
        "observedAt": record["observedAt"],
        "licenseOrReuseRestriction": record["licenseOrReuseRestriction"],
        "primarySourceVerified": verified,
        "interval": result,
        "interpretation": "reported schedules only; not exact or complete personal net worth",
    }
