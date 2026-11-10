# Power Atlas — Visual storytelling redesign, exploration 01

**Status:** Review branch, homepage-first. Not published to production.

## Reference
Inspired by the editorial, explorable infographics of https://informationisbeautiful.net/ without copying branding, source code, imagery, layout assets, or graphic designs.

## Thesis
Power Atlas should feel like a visual atlas of *how power affects daily life*, not a dense filing archive. Every story should answer:
1. What happened?
2. How big is the effect, over what time and geography?
3. Who or what contributed, according to what level of evidence?
4. What are the uncertainties and available responses?

## Homepage visual experiment
- Large, highly legible editorial headline.
- Topic-specific color and icon treatments for the six story tiles.
- More inviting, less monotonous chart/card surfaces.
- Visible focus rings, readable controls, reduced-motion support.
- Narrow-screen single-column topic cards; two-column mid-size layout.
- Existing charts, narratives, evidence labels and links remain intact.

## Extend the pattern platform-wide after visual QA
- Design tokens shared in a real stylesheet instead of duplication.
- Graph-first modules for Consumer Watch, Corporate Ownership, Personal Cost Explorer, Political Influence, and Class Actions.
- Always put one-sentence takeaway directly beside a chart and a plain-language "Why it matters" explanation under it.
- Every quantitative mark requires an explicit metric, unit, baseline, geography, date, and source. Do not add decorative or invented numeric claims.
- Tooltip, legend, axis, button and tab behavior must work on mouse, touch, keyboard and screen readers.
- Scale and color use must never imply causation from correlation, imply a legal allegation is proven, or turn missing records into zeros.
- Show source and freshness at a glance; support "Explore evidence" for detail.
- Mobile: no sideways page scroll, >=44px touch targets when possible, legible default chart labels, responsive overflow for tables, and obvious chart drilldown affordances.

## Design QA acceptance checks
- Verify actual browser rendering at 390px, 768px, and 1440px before merging.
- Ensure all homepage links, story-card actions and chart controls work.
- Confirm the existing public source links and attribution are preserved.
- Check contrast, keyboard operation and screen reader headings.
- Check existing UI tests, mobile overflow regressions, and zero fabricated measurements.
- Publish only after visual review and approval.
