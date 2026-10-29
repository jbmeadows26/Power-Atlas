# Institutional Decay: Empirical Findings and Data Audit — 2026-10-29

## Verified scope

**Not a causal research result.** The first country-level descriptive comparison is reproducible from
[data/institutional-decay/trust-country-waves-2023-2025.json](../../data/institutional-decay/trust-country-waves-2023-2025.json),
using `python scripts/analyze_institutional_decay.py`.
The underlying source is OECD (2026), *OECD Survey on Drivers of Trust in Public Institutions 2026 Results: Navigating Rising Expectations and New Horizons*, [DOI 10.1787/9eb63fec-en](https://doi.org/10.1787/9eb63fec-en), Chapter 1, Table 1.3, accessible
[here](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/drivers-of-trust-over-time-lessons-from-the-third-wave-of-the-oecd-trust-survey_440749ab.html).
Country-level 2023–2025 government trust entries were additionally corroborated against the Irish
[CSO Trust Survey 2025 international comparisons](https://www.cso.ie/en/releasesandpublications/ep/p-trsic/trustsurvey2025internationalcomparisons/results/).

The extraction includes **33 OECD countries participating in 2025**, five accession candidates
and Czechia (2023 only): **39 countries with some observations**. OECD Table 1.3
has **28 observed paired national-government trust rows** for 2023/2025:
the OECD's **29** is a count of countries participating in both waves, not the
number of nonmissing national-government trust comparisons. Colombia participated
in both but the 2023 national-government trust value is not given in this
published table. The United States did not participate in the 2025 OECD Trust Survey,
and must remain an external case-study country.

### Country-level changes (28 matched national-government trust observations)

| Outcome | Reproduced result |
| --- | ---: |
| Unweighted mean of published rounded shares in 2023 | 40.50% |
| Unweighted mean of published rounded shares in 2025 | 41.25% |
| Mean change | +0.75 percentage points |
| Median change | 0 percentage points |
| Countries with a rise | 11 |
| Countries with a fall | 13 |
| Countries unchanged at whole-percent rounding | 4 |

The OECD's **published 29-country** comparison gives 40.0% in 2023 and 40.7% in 2025, based on its own unrounded data and selected survey group. Do not replace the 28-country recalculation with these figures or claim the samples are identical. Published shares are rounded to whole percentages and lack underlying respondent-level uncertainty estimates.

Largest changes in the 28 observed national-government trust pairs:
Iceland +23 pp; Korea +14; Norway +9; Portugal +8;
France −12; Slovak Republic −9; Greece −8; Belgium −6.

### Separate institutional trust outcomes

Among the 33 OECD member countries with 2025 institutional data, **23** have higher trust
in the national civil service than in national government, **8** lower and **2** equal at rounding
precision. For local government, the respective counts are **25 higher, 5 lower, 3 equal**.
This is institutional differentiation, **not** proof that one part of government performs better.

On the 28-country matched national-government trust subset, 2023–2025 mean changes
in percentage points calculated from rounded, weighted country shares:
national government +0.750; national civil service +0.214; local government +0.464;
national parliament +0.393.

Sign-divergence cases where national-government and national-civil-service trust moved
in opposite directions: **Canada (+1, −3)**, **Luxembourg (−1, +1)**, **Mexico (−1, +1)**,
**Norway (+9, −4)**, and **United Kingdom (+4, −6)**.
These are useful **counterexamples** to a single 'trust in the state' measure.
Small ±1 changes may be within sampling or rounding uncertainty.
France's national-government trust fell 12 points while civil-service trust fell 3.
These country changes cannot establish causes or statistically significant differences.

### Why survey limitations matter

Per [OECD 2026 technical notes](https://www.oecd.org/en/publications/2026/06/results-of-the-2025-oecd-survey-on-drivers-of-trust-in-public-institutions_96323a65/full-report/technical-details-about-the-data-collection-and-regression-analysis_0480737a.html),
the 2025 survey has **76,927 valid responses** across 33 member and five accession-country
samples and most country samples used **non-probability quota methods**. Fieldwork
generally occurred in September–December 2025, earlier for Brazil/Peru.
Questions were adapted to national institutional terminology and weighted within country.
Mexico's sample is urban. Repeated cross-sections do not track the same individuals;
media, leadership changes, inflation, crises and partisanship can move public opinion.
No country significance claim is possible from our rounded extract alone.

## First directly measured accountability-implementation evidence

The second data product,
[data/institutional-decay/integrity-implementation-2025.json](../../data/institutional-decay/integrity-implementation-2025.json),
extracts OECD Public Integrity Indicators from the *Anti-Corruption and Integrity Outlook 2026*.

Source: [OECD 2026 overview](https://www.oecd.org/en/publications/anti-corruption-and-integrity-outlook-2026_16708b78-en/full-report/component-4.html).
The average difference between the shares of regulatory and practical criteria fulfilled is
**19 percentage points** across integrity areas, **35 pp** for conflict-of-interest systems
and **44 pp** for disciplinary systems. They are *criteria fulfillment gaps*, NOT
estimated corruption rates, guilt, or the percentage of ignored violations.

The country records are deliberately limited and **cannot** be used as a representative
cross-national model:
- [Poland](https://www.oecd.org/en/publications/anti-corruption-and-integrity-outlook-2026_0c8910f8-en/poland_6733ca8f-en.html): 89% of conflict-of-interest regulation criteria and 11% of practical criteria met.
- [Slovak Republic](https://www.oecd.org/en/publications/anti-corruption-and-integrity-outlook-2026_0c8910f8-en/slovak-republic_2c69a236-en.html): conflict-of-interest regulation 78% versus practice 0%; civil-service disciplinary rules 42% versus practice 0%; judicial-integrity criteria 82% versus practice 80%. *The contrast across topic areas itself warns against labeling an entire country simply 'corrupt' or 'uncorrupt'.*

Underlying values are **2025 or latest year available**, extracted by OECD in March 2026.
Practice criteria may include evidence availability and monitoring; absence of documentation
does not automatically mean illegality. An official percentage about criteria met is never
a verified case against a named official.

## Immediate next data-collection gate

The [OECD Public Integrity Indicators](https://www.oecd.org/en/topics/public-integrity.html)
offer de jure and de facto standardized indicators and
[downloadable country-level data](https://oecd-public-integrity-indicators.org/indicators/).
Before computing **any** trust versus implementation scatter/regression:

1. Obtain full OECD PII country, year, theme and criterion definitions, not a cherry-picked two-country example.
2. Verify which practice criteria refer to 2025 vs an earlier reference period; do not forward-fill or pool different criterion sets.
3. Match 2025 OECD trust countries (excluding non-participants and nonmembers) using standardized country codes.
4. Report full-case counts per variable, complete-case missingness, and why values are missing.
5. Separate perceptions of elite impunity, documented practical implementation, direct citizen service experiences, and trust outcomes.
6. Use sensitivity analyses for country selection, question comparability, partisanship, regime quality and background economic conditions.
7. Flag ecological correlations as descriptive. Credible individual or causal inference requires appropriately identified event studies or microdata.
8. Keep detailed claims on people only when supported by official legal statuses or adjudicated decisions; association alone proves nothing.

## Licensing, quality, and reproduction

OECD (2026) material is published with [CC BY 4.0](https://www.oecd.org/en/about/oecd-open-by-default-policy.html)
unless a different license or third-party content applies.
This work adapts the OECD's published figures by transcribing rounded values, linking country
codes, computing differences and adding limitations. **The opinions expressed and arguments
employed in this adaptation should not be reported as representing the official views of
the OECD or its Member countries.** OECD endorsement is not implied.

Reproduce the published-data calculations with `python scripts/analyze_institutional_decay.py`.
Run quality checks with `python -m unittest discover -s tests -p 'test_*.py' -v`.
This research is not yet integrated into `data/app-feed.json` or the deployed Power Atlas
frontend; the separate track remains inspectable in GitHub until licensing, stable schema,
source-vintage checks and product presentation criteria have been met.
