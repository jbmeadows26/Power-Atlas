# Power Atlas — visual atlas review handoff

**Branch:** `review/visual-atlas-platform-20261110`  
**Review-only public environment:** https://power-atlas-visual-review.vercel.app/  
**Research review:** https://power-atlas-research-git-review-vi-feb9f8-jbmeadows26s-projects.vercel.app/  
**Production status:** No change to `main` or the production Power Atlas aliases.

## What has been implemented

- An original, editorial visual atlas homepage with six topic routes and a dated, sourced consumer-price snapshot. The numbers are historical CPI index changes, not estimated household bills or attributed corporate/political effects.
- Consistent visual tokens for the shared navigation, story guides, chart cards, topic paths, source links, and evidence details.
- Accessible, keyboard-focusable chart bars that update source-scoped explanatory text when selected.
- Related-story navigation covering 21 named sections on both research and unified site surfaces, with Consumer Watch using the same shared components.
- Responsive gallery, chart labels, tap targets, focus outlines, and source-table safeguards; reduced-motion support.
- A separate Vercel review project to avoid login protection on the existing unified preview deployment.
- A source-preserving branch created from the latest available main baseline, incorporating all earlier data/research updates.

## Guardrails

- No verified evidence has been reclassified, no production data sources replaced, and no causal conclusions invented.
- The public preview is accessible to people with the link, so do not put private research or unpublished personal data in it.
- The review-only scripts carry a GitHub review banner, non-indexing browser meta tag, and internal preview URL rewrites. **Remove or disable these preview-only behaviors before a production merge**; do not copy preview hostnames into production.
- The six visual entry points are navigation to existing full pages. Each full page's local source, date, measurement units, caveats, data-gap labels, and applications must stay intact.

## Browser acceptance checks

- Unauthenticated review homepage opens; no Vercel login wall
- Six visual story cards route correctly
- Viewport 390px: no document-level horizontal scrolling on homepage, Everyday Life, Corporate Ownership
- Readable selected metric details and primary-source links
- Consumer Watch, Political Money, Accountability, Reforms and Class Actions navigate without 404s
- Confirm mobile category strip is scrollable only within its component, not the whole document
- No console errors and no missing required source data

## Remaining before publishing

Use the review preview for user approval. Then run the same visual and interaction checks on the final merged candidate, remove all preview-only redirects/banner/noindex and verify `main` is current. Production deployment must be a separate, explicit approval step.
