# 2025 ACS release and geographic join gate (verified 2026-11-12)

**Source-verified release:** The U.S. Census Bureau states that the **2025 ACS 1-year estimates were publicly released on 2026-10-29**, including congressional-district geographies and the 1-year summary file. This independently confirms the release date already recorded in `acs-2025-age-representation-comparison.json`; no age totals were recomputed in this review.

Primary sources (retrieved/reviewed 2026-11-12):
- Release confirmation: https://www.census.gov/programs-surveys/acs/news/updates/2026.html (entry dated 2026-10-29)
- Release details and summary-file availability: https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html (2025 ACS 1-year release, 2026-10-29)
- Release schedule: https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release-schedule.html (updated 2026-10-29)

**Important availability boundary:** The Census Bureau's 2025 release schedule still lists the **2025 ACS 1-year Public Use Microdata Sample (PUMS)** release date as **TBD** on this review date. The available congressional-district ACS tables do **not** make PUMS individual observations district-identifiable. Do not claim 2025 PUMS occupation-by-congressional-district results, or directly join individual-level ANES/CES respondents to House districts, without released data, compatible geographic identifiers/crosswalks, access rights, and uncertainty treatment. Public-use PUMAs are not interchangeable with House districts. Recheck official release schedules before later ingestion.

**Evidence status:** Census publication dates and release-product availability observed from official Census pages; member-specific occupations, survey political-alienation observations, and responsiveness effects **not observed** in this note. No new statistical estimates, causal findings, or claims about lawmakers. Census federal statistical data generally public domain; web-page embedded third-party materials may carry separate rights. Preserve existing source URLs, hashes, dates, nulls and geography caveats in the canonical dataset.
