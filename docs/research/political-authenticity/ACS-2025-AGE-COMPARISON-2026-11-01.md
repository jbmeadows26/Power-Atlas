# 2025 ACS House age representation comparison — evidence note (2026-11-01)

## Observed, reproducible descriptive result

Source: [2025 ACS one-year B01001](https://www2.census.gov/programs-surveys/acs/summary_file/2025/table-based-SF/data/1YRData/acsdt1y2025-b01001.dat), [Census 2025 release notice](https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html), and [119th congressional district geography](https://www.census.gov/programs-surveys/decennial-census/about/rdo/congressional-districts.119th_Congress.html). The Census Bureau released the 2025 one-year estimates **October 29, 2026**. Input data is the existing source-fingerprinted 435-district archive at `data/research/political-authenticity/acs-2025-house-district-age.json`, retrieved October 31, 2026. The member roster is a separately fingerprinted CC0 secondary source (`members.json`) dated October 30, 2026; official individual biographies have **not** yet been independently checked.

Across all 435 voting House districts, the 2025 ACS estimates **237,878,256 residents age 25+**, including **46,203,146 age 25–34** (**19.4230%**). The dated member snapshot includes **433 voting representatives**, **5 age 25–34** (**1.1547%**), and **2 vacant seats** (FL-20, TX-23). The member-minus-resident share difference is **−18.2683 percentage points**. These are two different measurement universes and dates, not a candidate eligibility-adjusted estimate or a causal effect.

Descriptive party strata are retained in the machine-readable aggregate for future stratified checks: 214 Democrats (3 aged 25–34), 218 Republicans (2), and one Independent (0). This stratification is **not** an explanation for the age gap, nor evidence of party conduct. There are no regression coefficients, significance claims, or imputed missing member characteristics.

## Reproduction and guardrails

Run `python scripts/build_authenticity_acs2025_comparison.py` with the checked-in ACS and member archives. Run `python -m unittest discover -s tests -p 'test_authenticity_acs2025_comparison.py' -v`. The independent CI workflow `.github/workflows/verify-authenticity-acs2025-comparison.yml` re-runs the builder and requires the published JSON to remain byte-identical. It fails closed on incomplete geography, duplicate IDs, stale member ages or dates, mismatched districts, impossible population counts, or missing source fingerprints.

**Do not** use the 2024 national ACS age comparison as if it were 2025. The older `age-comparison.json` is preserved as an explicitly cross-vintage historical reference, not silently overwritten.

## Remaining research limitations

1. The 2025 resident denominator includes noncitizens and people who cannot legally run for the House; a House-candidate-eligible denominator is not available from these aggregates.
2. Age bins are estimated using the ACS survey. District 90% margins of error are available, but covariance and directly estimated national-share MOEs are not. The published age-share difference has **no** significance test.
3. Member dates of birth are from a secondary CC0 roster; individually source-verified official biographies and member-level occupational histories remain outstanding.
4. House annual financial disclosures report asset **ranges**, not exact net worth. The official [House Clerk financial disclosure archive](https://disclosures-clerk.house.gov/FinancialDisclosure) and [House Ethics instructions](https://ethics.house.gov/financial-disclosure/) are appropriate no-cost primary sources for future document-level wealth interval extraction. Filing indexes alone cannot support an asset-value or net-worth estimate. Preserve nulls until a specific filing and schedule are verified.
5. ANES/CES marginal survey responses cannot be joined to individual districts or member attributes without legally accessible, geography-coded, design-weighted microdata. No invented joins or participant observations are allowed.

**Interpretation:** A substantial descriptive age composition difference is observed; its causes, policy consequences, and any connection to political inauthenticity are untested hypotheses.
