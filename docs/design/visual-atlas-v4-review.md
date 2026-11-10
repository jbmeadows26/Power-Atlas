# Power Atlas — visual atlas release handoff
Date: 2026-11-10

## Release scope

The approved editorial visual redesign is implemented across the unified and research frontends. This is a production-ready release candidate, sourced from `review/visual-atlas-platform-20261110`. Merge and deploy only after successful tests and a production deployment readiness check.

- Visual atlas: seven entry points, including **Consumer Class Actions**, built using the shared visual assets `atlas-visual-system.css` and `atlas-visual-system.js`.
- Shared story pathways, accessible chart selection, source and scope labels, evidence limitations, and responsive layouts.
- Consumer Watch: redesigned case explorer, true-cost story, and prominent class-action pathway.
- Consumer Class Actions: redesigned evidence-led page with interactive status distribution and an accessible, clickable claim-deadline timeline, official notice links, legal-status caveats, and source-directory cards.
- Four secondary discovery publishers are attributed via source-directory links: ClassAction.org, Top Class Actions, Consumer Action, and ClaimDepot. Publishing a case requires independent official source verification.

## Production safeguards

- The release scripts no longer inject a `DESIGN REVIEW · NOT PRODUCTION` banner, noindex metadata, or links to protected preview builds.
- Cross-site links from the research surface go to `https://power-atlas-unified.vercel.app/` where the destination page does not exist in research.
- Claims status is a **dated snapshot**, not a live status or eligibility guarantee; settlement amounts are not individual compensation.
- No evidence relationships or metrics are upgraded to causal conclusions, and no source feed is silently replaced.
- Old `redesign-preview.html` pages are clearly labeled archived design references and excluded from search indexing. The live design is the main homepage.

## Verification gates

1. `tests/test_visual_atlas_review.py`: all pages use shared assets; CPI matches the connected metric snapshots; chart bars work; preview-only behaviors are absent; class-action assets and routes exist.
2. `tests/test_consumer_class_actions.py`: data schema, legal classifications, discovery-source attribution, accessible visual timeline, JS syntax, and source-safe fallbacks.
3. Existing sitewide source/data/page-integrity audit, Consumer Watch suite and place-first story checks.
4. A Vercel production **READY** deployment with both canonical aliases mapped to the intended Git commit.
5. Public browser checks of navigation and responsive interactions where site access allows. An authenticated/protected preview cannot substitute for the public production smoke test.

## Related URLs

- Public unified platform: https://power-atlas-unified.vercel.app/
- Class actions: https://power-atlas-unified.vercel.app/class-actions.html
- Consumer Watch: https://power-atlas-unified.vercel.app/consumer-practices.html
- Research platform: https://power-atlas-research.vercel.app/
- Official settlement examples: https://www.personalcareproductssettlement.com/ and https://www.venuefeesettlement.com/

Data limitations remain visible in original source records. The release does not include unrelated open review branches (e.g. government-trading or market-power investigations).
