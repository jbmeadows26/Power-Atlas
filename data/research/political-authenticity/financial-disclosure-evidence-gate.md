# Member financial disclosure evidence gate (2026-11-07)

## Research question
Can public annual financial disclosures support a reproducible **reported-assets and liabilities interval**, without inventing exact member wealth or conflating transaction flows with year-end holdings?

## Implementation
`scripts/congress_disclosure_intervals.py` now includes `validate_member_annual_disclosure`. This gate requires a Bioguide ID, annual or amended-annual report type, unique filing identity for later amendment reconciliation, an original HTTPS report URL on an official House Clerk or Senate disclosure host, filing and observation dates, stated reuse restrictions, page/section locators for every reported asset and liability band, and explicit source-verification and schedule-completeness flags.

For incomplete or unverified schedules, all **net** interval endpoints remain `null`. A verified, complete empty schedule can be zero, but an absent schedule is **never** assumed to be zero. Open upper bounds remain open. Spouse ownership is retained rather than reassigned to the legislator. These intervals describe the **reported schedules only**: disclosure exemptions, asset categories and liabilities prevent treating them as audited personal net worth.

## Primary sources and reuse
- House Clerk financial disclosures: https://disclosures-clerk.house.gov/FinancialDisclosure
- Senate financial disclosures: https://efdsearch.senate.gov/
- Ethics in Government Act, public disclosure restrictions (5 U.S.C. § 13107(c)): https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title5-section13107&num=0&edition=prelim

Source-link host checks do **not** constitute verification that a report exists, that a URL is accessible, that a PDF is authentic, or that a disclosure is complete. Those require independent retrieval and page-level reconciliation, including superseding amendments. URLs in tests are synthetically constructed and **not claims that the documents exist**.

## Scope and missingness
This increment validates the data model; **zero additional member-level filings were extracted or source-verified**. The separately published third-party S&P 500 holdings aggregates are not substituted for official member filings. Neither the annual aggregates nor the stale 58-row daily trade delta establish net worth, misconduct, or legislative influence. Do not compute an empirical member-wealth index or a causal effect until primary filings, member identities, coverage denominators and model controls are verified.

## Testing
`python -m unittest tests.test_authenticity_finance` covers complete and incomplete schedules, open ranges, spouse ownership, source metadata, lookalike URLs, and rejection of periodic trades. The tests do not certify individual filings. Any CI run status must be checked separately.
