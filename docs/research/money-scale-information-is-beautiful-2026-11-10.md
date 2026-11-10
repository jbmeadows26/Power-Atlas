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


## Household-cost research bridge — November 10 follow-through
The Information is Beautiful graphics supply **economic scale**, not a monopoly-cost estimate. The connected Power Atlas presentation now separates three steps:

1. **Scale:** `platform/unified/money-scale.html` and `site/money-scale.html` offer 12 independently sourced, dated metrics with distinct wealth/debt/spending/GDP tabs.
2. **Exposure:** `platform/unified/household-market-bridge.json` and its `site/` mirror give BLS **2025 national average annual spending**: housing $27,790; transportation $13,492; food-at-home $6,491; healthcare $6,470. This is household expenditure, *not a measured anticompetitive surcharge*. BLS 2025 total spending was $81,905 per consumer unit. The U.S. average consumer unit and a Census ZIP household are different statistical units.
3. **Mechanisms:** The click-ready bar chart in `market-power.html#household-bridge` links these four categories to the existing 12-case `market-power.json` register: housing (rental algorithms/regulated utilities), transportation (airline competition), groceries (meatpacking buyer concentration), and health (PBMs/hospitals). Each case retains the original research type, agency citation, date, alleged-versus-measured status, beneficiaries, affected parties, and unanswered questions. Employment concentration links separately to the BLS average income figure—not a spending bar.

The hosted research project deploys **`site/`** at the URL root. Its market-power and money-scale assets are mirrored from `platform/unified/` and checked for data parity in `tests/test_market_power_household_bridge.py`. The review UI is `noindex` and does not require any paid data source, sign-in, ZIP, or browser location. Deployment creates a **non-production Vercel preview** only.

**Primary expenditure source:** [BLS Consumer Expenditures—2025, published 2026-10-29](https://www.bls.gov/news.release/cesan.nr0.htm). BLS noted adjusted weights after the 2025 federal data-collection interruption. Spending changes include price, volume and basket changes.

**Explicit non-findings:** No ZIP-level concentration effects, documented typical monopoly premium, exact share of consumers affected, or causal attribution of the spending baseline to political donations. The four categories are not asserted to be all essential spending, and the figures are not suitable to infer a personal budget.

**Quality gates:** `tests/test_money_scale_review.py`, `tests/test_market_power_household_bridge.py`, JavaScript syntax, and `.github/workflows/validate-market-power-household-preview.yml`. Browser-based visual and interaction checks should be reported separately from static and source checks.

**Approval rule:** This review work is not merged or published to production without the user's explicit approval.

## Public release
November 10, 2026: integrated into both production-oriented Power Atlas source trees and the nine-story visual system, with exact BLS consumer-unit definitions and explicit causal limitations. Review-only artifacts in the previous branch remain archival evidence, but production pages omit review banners.

## Selected billion-dollar primary evidence added
- Amazon FY2025 consolidated net sales: **$716.924 billion**; net income **$77.670 billion** ([Amazon 2026 release](https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Fourth-Quarter-Results/)). Revenues, gross profit and net income are materially different measures; none alone identifies anticompetitive rent.
- Stargate **$500 billion** announced investment *intention* over four years, originally announced January 21, 2025 ([original announcement](https://openai.com/index/announcing-the-stargate-project/)). Not an actual expenditure figure; no automatic energy-bill implication.
- These examples are separately selectable in the billions chart; each carries its own classification, vintage, scope, source and evidence limit.
