# Power Atlas visual atlas v4 — approved production release

This release uses the user-approved information-design direction and is rebuilt on top of the latest available main branch. It does not replace any canonical research data or automated ingestion.

## Scope

- Shared v4 editorial visual design layer in \`platform/unified/\` and \`site/\`.
- Visual storytelling on both homepages, interactive explanatory bars, six topic routes, responsive card layouts and related story navigation.
- Consumer Watch uses the shared design system.
- Consumer Class Actions gains an interactive, source-bound visual status summary and deadline timeline; lawsuit/claim status is not presented as an adjudication or guarantee of open eligibility.
- Neutral evidence and provenance captions remain in the legacy applications.

## Production-only safeguards

- No design-review ribbon, no \`noindex,nofollow\`, no review-site cross-links, no preview-only route markers, and no \`redesign-preview.html\` in the production tree.
- Research-to-unified links target \`https://power-atlas-unified.vercel.app/\`; local research pages remain local.
- Six story destinations exist in the unified application; original source data and ZIP privacy boundaries stay unchanged.
- New release tests check source-CPI values, JS syntax, visible page assets, class-action provenance and preview-artifact absence.

## Deployment

Reconcile the source branch with current main, run CI, deploy the exact approved commit to both Vercel production projects and verify public URLs. Stop and investigate if visual/story controls disappear, original evidence is missing, Vercel build fails or preview URLs leak into production.

## Result

This document records the release contract; actual deployment and smoke-test results must be verified independently rather than inferred from this file.
