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
