# Official House financial disclosures: provenance and interpretation gate (2026-11-03)

Source: https://disclosures-clerk.house.gov/FinancialDisclosure
Official search: https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch
Source reviewed: 2026-11-03 UTC. The Clerk provides annual disclosures, candidate filings, and periodic transaction reports; **these are different filing types**, not interchangeable annual net-worth statements.

## Newly confirmed evidence and legal limits
The Clerk states that financial disclosure reports identify sources, types, amounts or values of income. The official search interface displays statutory restrictions on using filing information, including commercial uses other than qualifying news dissemination, credit ratings, and fundraising solicitation. These restrictions require review before any product reuse; public accessibility does **not** imply unrestricted licensing.

## Data interpretation rules
- Match filings to members by independently verified identity, filing year, office, and document identifier; never surname alone.
- Keep asset-category interval lower/upper bounds as disclosed; do not replace open-ended upper ranges with invented caps. Open-ended ranges should have upper bound null and an explicit open-ended marker in a future expanded schema.
- Do not infer net worth from assets without liabilities, ownership shares, exclusions and filing-specific instructions. Joint/spousal assets must not silently become member-owned.
- Separate filing date, reporting period, retrieval date, and member roster snapshot.
- Never treat no matching search result as proof that a member filed nothing. Preserve status 'no_filing_found' as a search observation with search parameters and time.
- As of 2026-11-04, `scripts/validate_house_financial_disclosure.py` accepts verified open-ended asset intervals using `assetLowerUSD` >= 0, `assetUpperUSD: null`, and `assetUpperOpenEnded: true`; finite intervals retain both bounds. It rejects spoofed official hostnames, NaN/infinity, boolean amounts and unverified non-null ranges. This is a **record-level validator**, not a financial statement parser or verified aggregate net-worth estimator. The test fixtures are synthetic; **no observed member wealth figures were added in this increment**.
- Missingness is not zero wealth; party, age, ethnicity, biography or relationships are not evidence of misconduct.

## Next ingestion acceptance criteria
Record official document URL, document ID, filing year, filing type, reporting period, retrieval timestamp, document hash, source terms review, member Bioguide ID, reviewer and extraction method; only then add individual disclosure intervals. Validate cross-file duplicates and independently review anomalous totals. Until then the public member-wealth table must remain null.

This note is a source-policy verification and engineering guard, not a completed disclosure extraction or causal finding.
