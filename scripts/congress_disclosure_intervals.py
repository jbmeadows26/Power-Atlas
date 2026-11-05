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
