# 2025 ACS district comparison: verified access and geographic-vintage gate (2026-11-17)

## Verified primary-source findings
- The Census Bureau reports that 2025 ACS 1-year estimates **were released October 29, 2026**, including congressional districts, with 65,000-person publication threshold. Source: https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html (accessed 2026-11-17).
- Census Bureau 2025 ACS API documentation now states **all Census Data API queries require an API key**. Do not assume anonymous API access. A free API key is not a paid dataset, but key provision and rate/access limits must be checked before ingestion. Source: https://www.census.gov/data/developers/data-sets/acs-1year.html (accessed 2026-11-17).
- The Census Bureau explicitly provides the **2025 ACS 1-year Summary File on FTP** as an alternative to API retrieval; use this lawful public route when no key is available. Source: https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html (accessed 2026-11-17).
- Census says the currently available ACS congressional-district data are for **119th Congress** districts; 120th Congress district ACS data will be released later. A future 120th-district roster must not be silently joined to 119th geography. Source: https://www.census.gov/programs-surveys/decennial-census/about/rdo/congressional-districts.html (accessed 2026-11-17; verify the live page before production).
- Census warns that 2024 ACS comparison profiles were suppressed for AL, GA, LA, NY, NC because district boundaries changed; 2025 profiles resume without pre-2024 estimates in those geographies. Source: https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2025-04.html (accessed 2026-11-17).

## Required ingestion gates (not yet executed)
1. Record raw source URL, retrieval timestamp, table ID, variable ID, estimate/MOE/annotation, geography identifier, ACS vintage, 119th district vintage, and original license/use terms for each observation.
2. Retrieve 2025 district tables via official public FTP Summary File if API key is unavailable; validate row counts, duplicate GEOIDs, annotation/suppression codes and published geography metadata. Do **not** interpret a suppressed estimate as zero.
3. Join only to a date-appropriate 119th Congress member-seat snapshot, with vacancies explicitly null; flag any district boundary mismatch and do not coerce across congressional vintages.
4. Do not treat ACS district population estimates as member characteristics, nor treat public PUMAs as districts. Maintain sample error and denominator labels. Any occupational comparison needs aligned resident/member occupational taxonomies and universes.
5. ANES/CES respondent geography requires actual permitted access and validated district identifiers. Without that, keep political-alienation linkage null. Legislative responsiveness requires time-aligned issue measures, party and policy controls; do not infer motives or misconduct.

## Status
This note verifies availability and corrects the access/geography acquisition plan. No district observations were downloaded or joined, no new estimates computed, and no financial disclosures verified in this increment. All missing measures remain missing. Public Census releases are U.S. government statistical products; check the applicable product terms and citation guidance before redistribution.
