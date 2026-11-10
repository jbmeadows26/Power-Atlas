# Money at Scale — Information is Beautiful research intake (review only)
As of 2026-11-10. Branch: `review/market-power-20261110`.

## Inputs
- [Information is Beautiful — The Billion Dollar Gram](https://informationisbeautiful.net/visualizations/the-billion-dollar-gram/)
- [Information is Beautiful — Trillions](https://informationisbeautiful.net/visualizations/trillions-what-is-a-trillion-dollars/)
- [Original Trillions data sheet](https://docs.google.com/spreadsheets/d/1_YoXOf1-5b30Rt0AOxO9O4XNd-JpBQWovM3z2W9QUuI/edit)

## Outputs
- [Audited comparison dataset](../../site/data/money-scale-v1.json): 12 source-linked observations and 11 corrections/exclusions, with years, stock/flow type, scope and interpretation.
- [Money at Scale prototype](../../site/money-scale-review.html): an original, mobile-friendly chart, with interactive source notes, linked from the [redesign preview](../../site/redesign-preview.html).
- [Review guards](../../tests/test_money_scale_review.py) check treatment of stock/flow, evidence, dates and no fake household effects.

## Read this before presentation
The original site is a *lead generator*, not a sole evidentiary source. Figures are independently verified to source publishers where possible.

**Stocks**: Forbes global billionaire net worth $20.1T (March 2026), U.S. billionaire wealth $8.4T (March 2026), IIF global debt $348T (end-2025), NY Fed U.S. household debt $18.8T (Q4 2025), World Bank 2025 developing-country external debt $9.4T. Global and regional subsets must not be added. Debt outstanding is not debt service.

**Annual output (separate from spending)**: World Bank 2025 world GDP $118.35T and U.S. GDP $30.77T. The original sheet's $112T world GDP figure fits 2024 ($111.67T), not 2025. GDP is annual value added, not discretionary cash.

**Annual flows**: Treasury federal FY2025 outlays $7.01T; CMS 2025 health spending projection $5.7T (not actual); IISS 2025 defense expenditure $2.63T; World Bank 2025 developing-country debt service $1.4T. These figures differ by geography and include overlapping categories.

**Alternative methodology**: SIPRI estimates $2.887T military spending in 2025, not an extra $2.887T to add to IISS. Display IISS as one option and mention SIPRI as an alternative with the named source.

**Holdouts**: The originating sheet's $5.3T U.S. 2025 healthcare figure should be the 2024 figure (CMS projects $5.7T for 2025). The source sheet also misdates the Forbes 2026 $20.1T billionaire statistic. Other holdouts include unverified Elon $1.2T, 2012 offshore wealth inflated to a purported current number, climate model scenarios shown like disbursements, $32.6T Medicare for All scenarios without gross/net context, inconsistent debt entries, and conflated billionaire-millionaire/1% definitions.

## How Power Atlas should use it
1. Add the scale chart to the **economic concentration/monopolies** story as context for control of assets, not proof of market power.
2. Link to **Consumer Watch** for actual cost-of-living mechanisms and to **Corporate Ownership** for sourced control relationships.
3. For **government spending**, keep fiscal year, historical-vs-projected status and policy choices visible.
4. For **economic fragility**, show debt *levels versus service flows* with geographic controls; never treat debt balances as annual costs.
5. For **who benefits, who suffers**, pursue actual ownership, margins, price-cost evidence, market structure, lobbying and localized pricing; comparisons alone establish none of those causal links.

**Not approved for production.** The user requested review before publishing; changes stay on a review branch.
