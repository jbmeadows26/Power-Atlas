# Market Power — visual-system correction

**Reference:** Power Atlas Dark Money story at deployment `43bd6e8c5cf077912bde4fa3114f196b0028fda0` (reference project preview). The preview is access-controlled, so the exact GitHub source files `platform/unified/political-money-story.js` and `.css` were used as the structural design authority.

## Root cause
The earlier Market Power implementation created a standalone `mpx-section` dashboard underneath the old hero, while the approved Dark Money module mounts directly inside the visual-first `vs6-topic` hero. In the collapsed state, the newly built market-power section was hidden behind the research CTA, exposing only the generic illustration and making the page unlike the reference.

## Correction
- Mount `PowerAtlasMarketPower.mount(section)` at the same lifecycle point as `PowerAtlasPoliticalMoney.mount(section)`.
- Mirror the Dark Money hierarchy: heading, six selector tiles, selected four-node process diagram, two-column evidence/unknowns, original-source actions, related-chapter bridge, methodology disclosure and the preexisting research expand button.
- Preserve mint-green Market Power color identity while matching grid geometry, typography, spacing, breakpoints, keyboard buttons and accessible evidence states.
- Read every selected market statistic, legal classification, period and original source from existing `market-power.json`. No invented national overcharge or wrongdoing findings.
- Remove the extra `mpx-section`, keep the existing full 12-case explorer and BLS spending baseline behind progressive disclosure, and add the same global navigation shell used by Dark Money.
- Route the home card to `market-power.html` so it opens the six-pathway story rather than jumping into deep research.
- Keep the two frontend Market Power assets and the visual story v6 module synchronized.

## Safeguards
- Market Power evidence module uses public original links, not a derived causal price-impact estimator.
- `?case=<id>#explore` still opens the original research record, including status and supporting sources.
- Automated source checks cover six case IDs, source JSON schema, nav links, component mount, mobile layout rules and original deep research preservation.
