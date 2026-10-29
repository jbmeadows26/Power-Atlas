"""Reproduce descriptive, institution-specific trust comparisons from published OECD aggregates.

This script deliberately does not estimate causal relationships, infer corruption, or
make country significance claims from rounded percentages. No external packages/network.
Usage: python scripts/analyze_institutional_decay.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/institutional-decay/trust-country-waves-2023-2025.json"


def _pearson(xs: list[float], ys: list[float]) -> float:
    """Descriptive country-level Pearson correlation; no causal or individual interpretation."""
    assert len(xs) == len(ys) and len(xs) >= 3
    mx, my = mean(xs), mean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom_x = sum((x - mx) ** 2 for x in xs)
    denom_y = sum((y - my) ** 2 for y in ys)
    assert denom_x > 0 and denom_y > 0, "All values must not be equal"
    return numerator / ((denom_x * denom_y) ** 0.5)


def build_summary(path: Path = INPUT) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == "power-atlas.institutional-decay.trust-country-waves.v1"
    rows = data["rows"]
    assert len({r["countryCode"] for r in rows}) == len(rows)
    oecd25 = [
        r for r in rows
        if r["group"] == "oecd_member" and r["nationalGovernment2025"] is not None
    ]
    paired = [
        r for r in oecd25
        if r["nationalGovernment2023"] is not None
    ]
    assert len(oecd25) == 33, "Expected 33 OECD country rows in 2025"
    assert len(paired) == 28, "Expected 28 observable pairs; Colombia 2023 is unavailable"
    assert next(r for r in oecd25 if r["countryCode"] == "COL")["nationalGovernment2023"] is None
    assert all(r["countryCode"] != "USA" for r in rows), "USA not in 2025 Trust Survey"

    for r in rows:
        for column in (
            "nationalGovernment2023", "nationalGovernment2025", "localGovernment2025",
            "nationalParliament2025", "nationalCivilService2025", "courts2025",
            "politicalParties2025", "localGovernment2023",
            "nationalParliament2023", "nationalCivilService2023",
            "courts2023", "politicalParties2023",
        ):
            v = r[column]
            if v is not None:
                assert isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100

    changes = [
        {"countryCode": r["countryCode"], "country": r["country"],
         "changePercentagePoints": r["nationalGovernment2025"] - r["nationalGovernment2023"]}
        for r in paired
    ]
    sorted_changes = sorted(changes, key=lambda x: (x["changePercentagePoints"], x["countryCode"]))
    c = Counter(
        "increase" if r["changePercentagePoints"] > 0
        else "decrease" if r["changePercentagePoints"] < 0 else "no_rounded_change"
        for r in changes
    )

    gaps = {
        "civil_service_minus_national_government": [
            r["nationalCivilService2025"] - r["nationalGovernment2025"] for r in oecd25
        ],
        "local_government_minus_national_government": [
            r["localGovernment2025"] - r["nationalGovernment2025"] for r in oecd25
        ],
        "parliament_minus_national_government": [
            r["nationalParliament2025"] - r["nationalGovernment2025"] for r in oecd25
        ],
    }
    by_gap = {
        key: {
            "countryCount": len(values),
            "meanDifferencePercentagePoints": round(mean(values), 3),
            "medianDifferencePercentagePoints": median(values),
            "above": sum(v > 0 for v in values),
            "below": sum(v < 0 for v in values),
            "equalAtRoundedPrecision": sum(v == 0 for v in values),
        }
        for key, values in gaps.items()
    }
    dg = [r["nationalGovernment2025"] - r["nationalGovernment2023"] for r in paired]
    dc = [r["nationalCivilService2025"] - r["nationalCivilService2023"] for r in paired]
    dl = [r["localGovernment2025"] - r["localGovernment2023"] for r in paired]
    country_sensitivity = [
        {
            "countryCodeExcluded": r["countryCode"],
            "correlation": _pearson(
                [x for j, x in enumerate(dg) if j != idx],
                [x for j, x in enumerate(dc) if j != idx],
            ),
        }
        for idx, r in enumerate(paired)
    ]
    correlations = {
        "population": "countries as units, weighted national survey estimates aggregated by OECD",
        "notFor": "No causal inference, no p-value, no country ranking of misconduct",
        "nationalGovernmentVsCivilService2025": round(_pearson(
            [r["nationalGovernment2025"] for r in oecd25],
            [r["nationalCivilService2025"] for r in oecd25],
        ), 4),
        "nationalGovernmentVsLocalGovernment2025": round(_pearson(
            [r["nationalGovernment2025"] for r in oecd25],
            [r["localGovernment2025"] for r in oecd25],
        ), 4),
        "changeNationalGovernmentVsCivilService2023to2025": round(_pearson(dg, dc), 4),
        "changeNationalGovernmentVsLocalGovernment2023to2025": round(_pearson(dg, dl), 4),
        "nCountries2025": len(oecd25),
        "nPairedCountries": len(paired),
        "leaveOneCountryOutChangeGovCivil": {
            "minimum": round(min(x["correlation"] for x in country_sensitivity), 4),
            "maximum": round(max(x["correlation"] for x in country_sensitivity), 4),
        },
        "limitations": [
            "All values are aggregate percentages rounded to whole integers.",
            "These are Pearson relationships across countries, not individuals.",
            "Confounding by political support, income and survey mode is not resolved.",
            "Leave-one-out range is sensitivity to omitting one country; it is not a confidence interval.",
        ],
    }
    out = {
        "schema": "power-atlas.institutional-decay.trust-comparisons.v1",
        "input": "data/institutional-decay/trust-country-waves-2023-2025.json",
        "source": data["source"],
        "yearPairs": [2023, 2025],
        "metric": "percentage of adults indicating trust 6-10 on a 0-10 scale",
        "population": "survey country estimates (country weighted internally); descriptive country means unweighted",
        "status": "descriptive_noncausal_analysis_of_rounded_published_aggregates",
        "counts": {
            "countriesRepresented": len(rows),
            "oecdCountryRowsIn2025": len(oecd25),
            "accessionCountryRowsIn2025": sum(
                r["group"] == "oecd_accession_candidate" and r["nationalGovernment2025"] is not None for r in rows
            ),
            "pairedGovernmentTrustCountries": len(paired),
            "missing2023ColombiaGovernmentTrust": True,
            "missing2025CzechiaGovernmentTrust": True,
            "usaNotInSurvey": True,
        },
        "nationalGovernmentTrustPaired": {
            "mean2023Percent": round(mean(r["nationalGovernment2023"] for r in paired), 3),
            "mean2025Percent": round(mean(r["nationalGovernment2025"] for r in paired), 3),
            "meanChangePercentagePoints": round(mean(r["changePercentagePoints"] for r in changes), 3),
            "medianChangePercentagePoints": median(r["changePercentagePoints"] for r in changes),
            "increased": c["increase"],
            "decreased": c["decrease"],
            "unchangedAtRoundingPrecision": c["no_rounded_change"],
            "largestIncreases": list(reversed(sorted_changes[-6:])),
            "largestDecreases": sorted_changes[:6],
        },
        "institutionalGaps2025": by_gap,
        "institutionalAssociations": correlations,
        "institutionChanges2023to2025": {
            "matchedCountries": len(paired),
            "meanChangePercentagePoints": {
                "nationalGovernment": round(mean(
                    r["nationalGovernment2025"] - r["nationalGovernment2023"] for r in paired
                ), 3),
                "civilService": round(mean(
                    r["nationalCivilService2025"] - r["nationalCivilService2023"] for r in paired
                ), 3),
                "localGovernment": round(mean(
                    r["localGovernment2025"] - r["localGovernment2023"] for r in paired
                ), 3),
                "nationalParliament": round(mean(
                    r["nationalParliament2025"] - r["nationalParliament2023"] for r in paired
                ), 3),
            },
            "oppositeDirectionNationalVsCivilService": [
                {
                    "countryCode": r["countryCode"],
                    "country": r["country"],
                    "nationalGovernmentChangePp":
                        r["nationalGovernment2025"] - r["nationalGovernment2023"],
                    "civilServiceChangePp":
                        r["nationalCivilService2025"] - r["nationalCivilService2023"],
                }
                for r in paired
                if (
                    (r["nationalGovernment2025"] - r["nationalGovernment2023"])
                    * (r["nationalCivilService2025"] - r["nationalCivilService2023"]) < 0
                )
            ],
        },
        "limitations": [
            "Rounded percentages omit within-country sampling variance and question-level uncertainty.",
            "2023-2025 repeated cross-sections do not track the same respondents.",
            "The OECD's published 29-country wave-participation cohort is not equivalent to 28 published trust-item pairs.",
            "Trust is not a direct measure of efficiency, corruption, impunity or democratic commitment.",
            "Country means and institutional gaps are descriptive; no ecological causal attribution or hypothesis test.",
        ],
    }
    return out


if __name__ == "__main__":
    print(json.dumps(build_summary(), indent=2, ensure_ascii=False))
