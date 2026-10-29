# Political authenticity: verification record, October 29, 2026

**Judgment:** the original descriptive age comparison **passes arithmetic and published-source checks with caveats**; the *full mixed-methods study is not yet empirically complete*. This is a verification log, **not** a claim that political inauthenticity or misconduct has been statistically proven.

## Source and calculation checks

| Test | Independent observation | Result |
|---|---|---|
| Bioguide-key uniqueness in persisted 2026 congressional snapshot | 539 unique IDs across 539 rows | Pass (within secondary-source snapshot) |
| Chamber and participation classification | House including 6 nonvoting delegates = 439; Senate = 100; voting House = 433 | Pass |
| Official voting House size and vacancies | Clerk of the House: 433 voting members, two vacancies (FL-20, TX-23) | Pass: snapshot denominator agrees |
| House seat uniqueness | 433 unique state/district voting seats, no duplicate seats | Pass |
| Senate balance | Two senators from each of 50 states, no missing states | Pass |
| Date-of-birth arithmetic | 539 of 539 stored ages reproduced from birth dates and date 2026-10-29 | Pass *within CC0-derived records* |
| Current age 25–34 in House | 5 / 433 = 0.0115473441 = 1.1547% | Pass |
| 2024 Census age 25–34 | 46,198,405 of 235,910,719 residents aged 25+ = 19.5830% | Pass |
| Age-group difference | (5/433 − 46,198,405/235,910,719) × 100 = −18.42826936 percentage points | Pass |
| House/population proportion ratio | (5/433) / (46,198,405/235,910,719) = 0.05896615, rounded 0.059 | Pass |
| CRS occupation and education baseline | Reviewed August 4, 2025 R48535; House law practice 31%, Senate 47%; House bachelor+ 96%, Senate 99%; 5 union representatives, House only | Supported **for historical 2025 cohort only** |
| Carnes regression correction | April 26, 2026; original Appendix B accidentally copied unadjusted occupation coefficients. Corrected appendix reported; interpretation stated unchanged | Confirmed against publisher |
| Core perceived-authenticity study | Luebke & Engelmann (2023), PLOS ONE, DOI 10.1371/journal.pone.0285344, 12-item instrument | Verified publication |
| Experimental question dodging | Clementson (2018 issue; online May 3, 2017) DOI 10.1177/0261927X17706960 | Verified publication |

### Authoritative citations

- U.S. Census Bureau 2024 ACS 1-Year Supplemental Table K200104: https://data.census.gov/table/ACSSE2024.K200104
- Clerk of the U.S. House: https://clerk.house.gov/Members/ViewVacancies and https://radiotv.house.gov/house-data/party-breakdown
- Congressional Research Service August 4, 2025 R48535: https://www.everycrsreport.com/reports/R48535.html
- Carnes correction (April 2026): https://onlinelibrary.wiley.com/doi/10.1111/lsq.70066
- Luebke and Engelmann (2023): https://doi.org/10.1371/journal.pone.0285344
- Clementson (2018): https://doi.org/10.1177/0261927X17706960
- Butler and Broockman (2011): https://doi.org/10.1111/j.1540-5907.2011.00515.x

## Confirmed issues and repairs

**P1 – Duplicate/stale input could have been accepted by age builder.** Prior age builder accepted arbitrary precomputed `ageYears`, and it did not independently verify ID uniqueness, House district uniqueness, or exactly two senators per state. This could silently corrupt the data product. On October 29, the implementation was amended to recompute ages from birth dates and snapshot date and reject malformed/duplicate identities, duplicated voting House seats, incorrectly classified delegates, and incomplete Senate representation. Independent negative regression tests were added.

**P1 – Age comparison tests were not actually invoked by workflow.** Workflow previously ran the biography collector's tests and did not call the separate age-comparison test module, even though its path was named in the push trigger. Added the test invocation **after** dataset collection and comparison construction so persisted-output assertions are meaningful.

**P1 – Source incompleteness remains.** The 539/539 matched birth dates come from a third-party CC0 congressional-legislator dataset, not an individual-by-individual official Biographical Directory audit. Current study does not include member wealth disclosure intervals, member-level pre-political class, race self-reporting, political efficacy survey joins, policy effects, or observed rhetoric coding.

**P1 – Cross-universe and cross-vintage age gap.** Population baseline is 2024 U.S. *residents* aged 25+, including noncitizens; legislative count is October 2026 *voting House members*. This figure must never be labelled constitutionally candidate-eligible representation gap, causal effect on alienation, or evidence of age-based discrimination. Sampling margins of error for the ACS ratio were not propagated.

**P1 – Production publication unverified.** GitHub source files are persisted; Vercel UI ingestion of the new research is not independently verified. Most recent repository deployment health documented free-plan daily API deployment limit. Do not label the front end synchronized without a served-asset check.

## Status and next validation gates

- **Verified against published source and repository records:** counts, basic age transformations, Census 2024 inputs, CRS 2025 quoted aggregate categories, Carnes 2026 correction, core study identifiers.
- **Code status:** updated builder, new negative tests and CI test invocation are **committed and retrieved** from GitHub. GitHub Actions *success after the final code changes* was not independently established during this check; report it as **pending verification**, not `passed`.
- **Survey and interviews:** no original human-subject interviews, focus groups, or survey experiments have been conducted. These remain proposed designs and must be reviewed ethically before human recruitment.
- **2025 ACS:** release publicly scheduled for October 29, 2026, by 10 a.m. ET. Do not replace verified 2024 figures until 2025 exact K200104 values are independently retrieved, geographically/definitionally checked, and versioned.

### Verified repository paths

- `data/research/political-authenticity/members.json`
- `data/research/political-authenticity/coverage.json`
- `data/research/political-authenticity/age-comparison.json`
- `data/research/political-authenticity/crs-occupations-2025.json`
- `scripts/build_political_authenticity_age_comparison.py`
- `tests/test_political_authenticity_age_comparison.py`
- `.github/workflows/collect-political-authenticity.yml`

**Claim boundary:** Observed demographic separation is not evidence of dishonesty, unlawful discrimination, undue influence, or individual wrongdoing. Representative behavior and constituent experience must be observed independently.
