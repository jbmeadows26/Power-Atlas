# Political inauthenticity and representation gaps — source-grounded research

**Research snapshot:** October 29, 2026. **Scope:** U.S. 119th Congress; current-roster, not historical opening-day cohorts. This is a research data product, not a list of political offenders.

## What is actually ingested

- [Congressional biographies with age calculations](../../../data/research/political-authenticity/members.json): 539 indexed records, matched by Bioguide ID, chamber, state, active term and House district to CC0 third-party biographies; 539/539 birthdates found, **not independently official-Bioguide confirmed**.
- [Completeness and unmeasured fields](../../../data/research/political-authenticity/coverage.json): 439 House members/delegates, 100 senators; 6 nonvoting House members excluded from voting-seat comparison. Do not mistake 539 identities for 535 voting seats.
- [119th House district crosswalk](../../../data/research/political-authenticity/house-district-crosswalk-119.json): all 435 apportioned seats have validated 2025 ACS geography keys; 433 occupied and two vacant in the October 2026 roster. All district age estimates and margins of error remain null. [Methods and release audit](census-2025-district-crosswalk.md).
- [Age-band comparison](../../../data/research/political-authenticity/age-comparison.json): 2024 ACS national resident population aged 25+ versus voting House members in October 2026. 25-34 population share 19.583%; House 5/433 (1.1547%); gap -18.428 percentage points. Population includes noncitizens; **not an eligibility-standardized estimate or statistical significance test**.
- [Rhetorical analysis codebook](../../../data/research/political-authenticity/rhetoric-codebook.json): preregistration-ready code definitions. **No politician-specific Q/A units coded yet**.

## Methodological safeguards

1. Separate **who occupies office**, **who receives service**, **whose substantive preferences shape decisions**, **public perceptions of authenticity**, and **objective question-answer directness**.
2. No politician is labelled deceptive, disinterested or corrupt from demographic dissimilarity, age, party, asset disclosure, or a single answer.
3. Member biography snapshots are not interchangeable with January 3, 2025 membership. When a seat is vacant or a member has been replaced, do not reconstruct the historic Congress from the current-roster file.
4. Age denominator 25+ is a *resident-population* approximation only. A constitutionally eligible comparison requires age and citizenship-tenure restrictions (House 7 years, Senate 9 years), plus matched geographic and reference-year universes; leave those unavailable rather than pretending Census age totals measure them.
5. Do not score missing disclosures as zero wealth, no education, no responsiveness, or zero integrity.
6. District age and survey joins must use the correct redistricting edition and election year, stable geographic keys, official boundaries, and survey weights. Respect minimum reporting sizes.
7. Before fitting causal models, register adjustment variables for party, ideology, policy preferences, incumbent status, media exposure, district economic conditions, geography, and survey mode. Address reverse causation and measurement error.
8. Two independent rhetoric coders, separate truth-checkers, source-recorded question/answer timestamps, reliability by code, representative strata, negative cases.
9. Human-subject surveys, focus groups and interviews require appropriate ethical review/consent. None have been conducted by this data collection workflow.

## Academic evidence correction discovered October 29

Carnes (2012), *Does the Numerical Underrepresentation of the Working Class in Congress Matter?*, DOI [10.1111/j.1939-9162.2011.00033.x](https://doi.org/10.1111/j.1939-9162.2011.00033.x), received a formal [April 26, 2026 correction](https://doi.org/10.1111/lsq.70066): the published Appendix B mistakenly copied the unadjusted model's occupation coefficients into the adjusted model display. The article's Table 1 was correct, and the author says interpretation is unaffected. Cite the corrected appendix for adjusted occupation coefficients.

Other primary or peer-reviewed evidence: [Pew Congress demographic profile (2025)](https://www.pewresearch.org/short-reads/2025/03/03/the-changing-face-of-congress-in-7-charts/); [CRS 119th profile (2025)](https://www.everycrsreport.com/reports/R48535.html); [Butler & Broockman (2011)](https://doi.org/10.1111/j.1540-5907.2011.00515.x); [Luebke & Engelmann (2023)](https://doi.org/10.1371/journal.pone.0285344); [Clementson (2018)](https://doi.org/10.1177/0261927X17706960).

## Public data access: 2026 change

Since May 2026, the [Census Data API requires a free key for **all data queries**](https://www.census.gov/library/video/2026/adrm/requesting-a-census-data-api-key.html); metadata can be queried without one. [Public ACS FTP tables](https://www.census.gov/programs-surveys/acs/data/data-via-ftp.html) are an alternative without an API credential. The [2025 ACS one-year release](https://www.census.gov/data/developers/data-sets/acs-1year.2025.html) was published October 29, 2026. The district geographic keys have been assembled, but the exact 2025 age table estimates, universes, and margins of error have **not** been imported; retain the verified 2024 benchmark until they are source-checked. The current [2024 ACS source table](https://data.census.gov/table/ACSSE2024.K200104) is explicitly cited; its estimated values and sampling-error notes matter.

## Completion gates

| Evidence layer | Current status | Gate to publish conclusions |
|---|---|---|
| Member identity/age | Indexed, secondary-source verified only | Sample audit against authoritative Bioguide; freeze vintage and membership universe |
| Age national comparison | Reproducible descriptive | Add 2025 ACS or matching-year national cohort, citizenship tenure, MOEs |
| Age by congressional district | 435-seat 119th geography crosswalk validated; 2025 age data null | Retrieve official 2025 district age estimates and MOEs, validate table universes, then perform checked geographic join |
| Wealth/education/occupation | Unmeasured | Public disclosed intervals plus documented class occupation categories and missingness |
| Constituent efficacy | Not joined | ANES/CES weighted microdata joined to valid geography, primary question codes, uncertainty |
| Policy responsiveness | Not tested | Member sponsorship/roll-call/service outcomes plus party and agenda controls |
| Rhetorical inauthenticity | Codebook prepared; no corpus coded | Balanced primary-media recordings, independent coder agreement |
| Causal survey experiment | Proposed, **not fielded** | Ethics review, preregistration, randomization, power and actual respondent data |

**Automation:** [collector](../../../scripts/collect_political_authenticity.py), [age comparison builder](../../../scripts/build_political_authenticity_age_comparison.py), [GitHub workflow](../../../.github/workflows/collect-political-authenticity.yml). Source refresh failures must never be interpreted as evidence of an empty or zero population. Existing files are retained until validation succeeds.

**App integration:** Files are persisted in the same Power Atlas repository; they are **not yet confirmed to be displayed in the Vercel frontend**. Add a frontend feature only after checking the existing data-feed contract and age-metric caveats.
