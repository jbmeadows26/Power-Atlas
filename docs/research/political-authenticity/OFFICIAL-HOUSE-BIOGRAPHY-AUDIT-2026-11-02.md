# Official House Historian biography audit — 2026-11-02

**Purpose:** Close the most consequential source-verification gap in the 2025 ACS–House age comparison: the official dates of birth of **all five** voting House members aged 25–34 in the frozen October 30, 2026 roster. A six-member, bipartisan, older comparison set demonstrates how to preserve multi-label occupational histories. This is a **purposive audit, not a representative sample**.

## Method and actual observed result

Read the House Historian's primary-source *Concise Biography* pages for the 11 individuals listed in [the evidence file](../../../data/research/political-authenticity/official-house-biography-audit-2026-11-02.json), matching the embedded Bioguide ID and official date of birth against the CC0 secondary `members.json` roster. All 11 official dates of birth agree with that snapshot; all five members aged 25–34 have primary-source matches. The 2025 ACS–2026 House descriptive comparison remains **5/433 (1.1547%)** versus **19.4230%** of 2025 residents aged 25+ living in voting districts, or **−18.2683 percentage points**. The remaining **422** voting House birthdates are **not** claimed to be officially verified by this audit. The Senate and nonvoting delegates are outside its scope.

The five young members: Yassamin Ansari (D-AZ), Everton Blair (D-GA), Maxwell Frost (D-FL), Brandon Gill (R-TX), and Addison McDowell (R-NC). Six comparison members: Robert Aderholt (R-AL), Jake Auchincloss (D-MA), Mark Amodei (R-NV), Alma Adams (D-NC), Pete Aguilar (D-CA), and Jodey Arrington (R-TX). Selection was **not random**: all young members plus six deliberate bipartisan contrasts. No overall party, occupation, or class percentages may be estimated from these 11 cases.

## Occupational evidence without class inference

Each record retains source-reported prior roles as **overlapping** role tags; a member can have been a teacher, business professional, staffer, soldier, or elected official at different times. This is not an independently coded socioeconomic class. The official biography for Frost reports college attendance but not a completed credential, so the highest-degree field is **null**, not "no degree." Ten other biographies report a degree. The original `members.json` fields remain unchanged, so downstream readers must explicitly join this evidence overlay by Bioguide ID; do not silently promote the full roster to verified status.

**Financial disclosures:** All 11 wealth intervals remain null. Occupation and education are not financial disclosures. To populate intervals later, inspect the member-specific official House Clerk [Financial Disclosure archive](https://disclosures-clerk.house.gov/FinancialDisclosure), capture filing year, asset/liability schedule rows and disclosed lower/upper ranges, and retain missing, spouse, and exempt categories; do not infer point estimates from disclosure bands.

## Source provenance and reproducibility

The primary sources are individual `history.house.gov/People/` pages (one complete URL per member in the evidence JSON), observed November 2, 2026, with `sourceSection=Concise Biography`. Original page version dates and raw-content SHA-256 hashes were not available from the indexed views and remain **null**. The source is an official U.S. House government work, generally public domain in the United States; embedded third-party media require separate reuse checks. Manual single-reviewer verification does not establish independent double coding or historical permanence of the live page.

Run `python scripts/validate_authenticity_official_biographies.py --check` and `python -m unittest discover -s tests -p 'test_authenticity_official_biographies.py' -v`. These fail on birthdate or district mismatches, duplicate IDs, source substitutions, unverifiable education, invented hashes, and any attempt to infer class or wealth. The GitHub workflow checks the same conditions without paid services or external scraping. It verifies **internal consistency**, not the continued availability or unchanged content of each external page.

**Remaining gaps:** 422 voting House primary DOB checks; 100 senators and nonvoting delegates outside this audit; disclosure-backed wealth intervals; representative and independently adjudicated occupational coding; geographically and legally valid survey joins; party- and issue-controlled legislative responsiveness; and independently coded rhetoric. None of these is a finding of political misconduct or causal inauthenticity.
