# Market Power — interactive visual evidence expansion (2026-11-10)

## User story
The visual-first home card shows two separate, documented market concentration measures rather than an unsourced conceptual drawing. The deep dive at `market-power.html#market-power-pathways` includes five single-tap story lenses (prescriptions, beef, hospitals, labor markets, search), an illustrative or documented operating-company map, a measure with denominator and date, a possible leverage mechanism, outcomes to investigate, and links to the underlying case, owner relationship and source.

The original twelve-case `market-power.json`, BLS household expenditure bridge, case filter and research explanations remain intact. New consumer-cost values, inferred sector-wide overcharges or individualized price penalties **are not invented**. Concentration ratios across different markets, locations and years must not be compared as if they were the same denominator. Allegations are not court findings.

## Evidence sources and interpretation

- **Meatpacking:** USDA Economic Research Service, Jan 25, 2024, reports 85% of U.S. steer and heifer purchases handled by four large firms. This is cattle procurement, not retail beef sales, and does not quantify the household beef surcharge. https://www.ers.usda.gov/amber-waves/2024/january/concentration-in-u-s-meatpacking-industry-and-how-it-affects-competition-and-cattle-prices
- **Prescription pharmacy benefit managers:** FTC, July 9, 2024 interim report, top three processed nearly 80% of approximately 6.6 billion prescriptions in 2023. No claim that 80% of drug spending is an overcharge. https://www.ftc.gov/news-events/news/press-releases/2024/07/ftc-releases-interim-staff-report-prescription-drug-middlemen
- **PBM parent-company relationships:** KFF 2026 explains Caremark / CVS Health, Express Scripts / Cigna and OptumRx / UnitedHealth Group. https://www.kff.org/other-health/what-to-know-about-pharmacy-benefit-managers-pbms-and-federal-efforts-at-regulation/
- **Hospital affiliation:** GAO Sep 22, 2025 review finds physician hospital consolidation increased since 2012; this is not a national hospital price markup. https://www.gao.gov/products/gao-25-107450
- **Jobs and Google search:** Named measured and court-finding cases preserve the dates, geographic definitions and legal status already in the versioned `data/market-power/evidence-v1.json`. No national employer concentration score is implied.

## Engineering
- Source register is read at runtime from each frontend's existing same-origin `market-power.json`.
- Independent local files in both `site/` and `platform/unified/` have matched bytes and avoid external build dependencies.
- Accessible tab buttons expose pressed state; panel content uses an `aria-live` region, native anchor links, keyboard focus styles and reduced-motion CSS.
- Home card links to the start of the expanded evidence story.
- The publish decision is separate from this review branch; validate preview + CI before merging.
