# Public Integrity — financial trading while governing (2026 baseline)

**Status:** Review branch only; third-party compiled disclosure data, mathematically reconciled to the published aggregate but **not** independently checked against every original federal filing. No conflict, insider-trading, corruption, or household-price finding is asserted.

## Why this belongs in Power Atlas
The Reddit visualization at https://www.reddit.com/r/dataisbeautiful/comments/1xog0rc/oc_trumps_accounts_made_more_trades_than_all_of/ makes a useful *lead*, not a determination of misconduct. The underlying Kadoa comparison is the source of the numeric values and methodology. This public-integrity lens connects to the existing campaign-money, corporate ownership, business influence, personal cost and civic reform paths without merging unlike datasets or asserting causality.

## Source-reported comparison
- Comparison period: **January 2025–August 2026** (20 months). August 2026 is potentially incomplete.
- **31,877** disclosed transactions attributed to eight accounts in President Trump's reports versus **20,973** across Congress including reportable family transactions: **10,904** more / **52.0%** more by count; Trump accounts exceed Congress in **16 of 20 months**.
- Kadoa published *disclosure-based notional ranges*, not precise profit totals: **$1.6B–$5.2B** in presidential-account activity versus **$0.6B–$1.8B** congressional activity; ranges overlap.
- White House says third-party managers run the accounts. Original filings do **not** establish who directed each order. Eight managed investment accounts are not comparable to 535 lawmakers or unique human trade decisions.
- The **746-stock** view covers January–May 2026 and excludes non-ticker holdings (such as certain bonds). It should not be conflated with the full 20-month trade count.
- Treat the Reddit thread as discovery/background, **not** data verification.

## Data objects and display
- Reusable corpus: `data/public-integrity/official-trading-2025-2026-v1.json`.
- Static site deployment mirror: `platform/unified/official-trading-data-v1.json`, identical to the corpus at this review.
- Interactive dashboard: `platform/unified/public-trading.html`. Accessible from the unified research homepage, donor intelligence and Step 3 of the location-first Daily Life explorer.
- Interactive bars display actual reported monthly counts, accessible by keyboard; 2025 and 2026 toggles retain comparability. The data is not fed into an invented corruption or consumer-cost score.

## Sources
1. Kadoa summary and monthly data: https://www.kadoa.com/congress/insights/trump-trades
2. Kadoa open-source methodology (MIT, raw public reporting caveats): https://github.com/kadoa-org/congress-trading-monitor
3. Office of Government Ethics public financial disclosure access: https://www.oge.gov/web/oge.nsf/accessdocs_disclosure-quickstart?OpenForm
4. House Clerk Financial Disclosure reports: https://disclosures-clerk.house.gov/FinancialDisclosure
5. Senate public eFD search: https://efdsearch.senate.gov/search/home/
6. 2026 OGE annual disclosure announcement: https://www.publicnow.com/view/A659E664B6DFE08CB3BF6BF9D5C0D66D2C798B23

## Next evidentiary gates before impact or wrongdoing claims
1. Re-fetch each relevant OGE/House/Senate transaction report, preserve document URL, line/page, filing time, amendments, reporting delay, asset type and unique filing keys; independently reconcile Kadoa aggregate counts.
2. Resolve filers, spouses, dependents, beneficial owners, managers, discretionary authority, asset IDs and range values. Do **not** collapse all trades into personally directed presidential trades.
3. Date specific government actions and identify material exposures to directly affected entities; distinguish legislation, executive orders, procurement, antitrust, healthcare regulation, and financial regulation.
4. Run predeclared event windows and appropriate firm, sector, market and macroeconomic controls; investigate non-conflicting decisions and negative cases too. Report selection biases and unavailable data.
5. Link policy decisions to household prices, wages, public costs or service quality only when a valid causal design exists, else label `unknown`. Avoid assigning criminal, corruption or legal liability labels from correlation.
6. Apply identical analytical standards to executives, presidents and legislators of *both* parties over comparable periods. Keep current law separate from reform proposals.

**Review criterion:** Presentation should tell a fast, readable story while always revealing definitions, data-source lineage, limitations, and sources, with no claim that trade counts prove illegality.
