# Freight as an embedded cost driver — visual-first review

This addition clarifies that transportation is both a direct household expense and an input to the production and distribution of goods. It is intended for the visual-first redesign **review branch only**; it is not an assertion of a quantified cost pass-through in every household category.

## Verified source evidence

- BTS, Transportation Producer Price Index – August 2026: truck freight transportation PPI was up 14.3% year on year in August 2026. https://www.bts.gov/newsroom/transportation-producer-price-index-august-2026
- BLS CPI Transportation via FRED: existing Power Atlas September 2026 7.77% year-over-year consumer transport CPI snapshot. https://fred.stlouisfed.org/data/CPITRNSL
- USDA ERS Food Dollar, revised 2026 edition: for *domestically produced food at home*, the 2024 farm share was 18.5 cents and the **total post-farm marketing share** was 81.5 cents. Processing, transportation, storage and retail are all included; this is not the freight share. https://ers.usda.gov/data-products/charts-of-note/114103
- BLS: PPI freight transportation and goods CPI cover different transaction concepts. https://www.bls.gov/opub/btn/volume-13/misconceptions-ppi.htm

## Interface

- New `freight-impact.html` on both research and unified surfaces, offering interactive supply-chain pathways for groceries, medicine, construction materials and other products.
- A concise card linking to this evidence is injected into the visual homepage and selected everyday-life, consumer, market-power and economic-resilience pages.
- The homepage's Transportation line is spelled out and spotlighted above the fold for mobile readability.
- Dense methodology remains inside expandable disclosure controls.

## Analytical limits

- **No double counting:** freight is already embedded in observed retail prices and is not a new surcharge to add to retail CPI.
- **No direct PPI/CPI addition:** 14.3% freight producer inflation and 7.77% household transportation CPI cover different baskets and months.
- No product-specific or local freight pass-through coefficients are claimed for groceries, healthcare or housing.
- Data model stored in `data/place-impact/freight-embedded-costs-v1.json` for auditability.
- Further work for actual price decomposition: USDA Food Dollar industry-group shares, BEA input-output exposure, BTS mode series, EIA diesel, and category-specific retail prices on compatible time bases.

Before production, verify in live browser at 390px, test four sector controls, direct source links, navigation from homepage and cost pages, and keep any ongoing source updates from `main`.
