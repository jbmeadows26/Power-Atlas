# Power Atlas — V6-only platform QA audit
Date: November 11–12, 2026
Release status: **Not approved for production until browser QA and visual review pass**

## Scope and evidence

The public website was inspected in a read-only browser at 1440×900 desktop and 390×844 mobile, including opening the mobile menu. The five captured routes were:
- https://power-atlas-unified.vercel.app/my-life.html (root redirects here)
- https://power-atlas-unified.vercel.app/dark-money.html
- https://power-atlas-unified.vercel.app/market-power.html
- https://power-atlas-unified.vercel.app/consumer-practices.html
- https://power-atlas-unified.vercel.app/take-action.html

The GitHub source inventory comprises 27 Unified HTML pages, 27 importing the old `atlas-visual-system.js` initializer; page-level styles remain extensive. This is **not** a full 27-page visual review. No messages or real ZIP lookups were submitted.

## Findings and required remedies

| Priority | Finding | Evidence | Release criterion |
|---|---|---|---|
| P0 | Four older generations coexist | `atlas-visual-system.js` injects V5, V5 injects V6; page-specific rules may override V6 | Exactly one *visible* V6 shell on all routes, despite retained legacy data code |
| P0 | Contradictory topic covers | Dark Money has a lilac/purple outer cover, Market Power a cream/mint full-width cover, Consumer Watch navy, Actions bespoke cream | Cream editorial covers with identical width, typography and headline hierarchy across routes |
| P0 | Inconsistent widths | Market Power almost viewport-wide at 1440px while Dark Money/Consumer Watch centered ~1160px | One centered max-width cover, no horizontal overflow at 390px |
| P1 | Consumer Watch evidence seems absent | Initial page visibly ends just past its ~550px hero, and deeper sections are behind the reveal button | Clearly discoverable evidence CTA and working content reveal with controls |
| P1 | Actions differs | ~84px desktop heading and separate frame versus other ~73px topic headings | Same V6 headline scale and frame; preserve citizen action controls and congressional links |
| P1 | Old-style deep chapters | Toggling evidence displays per-page cards and original research interface | V6 editorial outer surfaces when expanded; original charts, citations and research data retained |
| P1 | QA tests only assert file presence | `test_product_acceptance.py` and `test_visual_stories_v6.py` do not check computed styles | Desktop/mobile browser checks for covers, active navigation, chapter controls, ZIP behavior, evidence accessibility |
| P2 | Regression process too permissive | Design policy exists but relies on static marker matching | CI must reject visually divergent covers and absent evidence controls; avoid new page-scoped global root/theme overrides |

## Remediation in `fix/v6-one-design-qa-20261111`
- Harmonize the shared V6 page cover surface, width, fonts, and accents for primary topic pages.
- Remove the purple alternative Dark Money *outer* shell without removing its investigative pathways.
- Align the Actions headline to V6 scale.
- Normalize expanded evidence and research archive frames without altering the underlying sources.
- Add real-browser regression checks at desktop and mobile; verify Consumer Watch expands into accessible chapters.
- Enforce V6 integration on all 27 Unified HTML routes through a static inventory contract.
- Update the canonical design contract to point Actions to the dedicated action page.

## Validation and release conditions
`python -m unittest discover -s tests -p test_product_acceptance.py`, Playwright smoke suite, JS syntax checks, the full relevant V6 visual suite, a live preview desktop/mobile walkthrough and a source/link check must all pass before production. A green build alone does not establish visual fidelity. New sources and economic claims remain separately validated. Any failed check is a release blocker.

## Important limitation
Existing research/UI components remain in the tree for evidence preservation; **V6-only refers to the visible product design, not deletion of data pipelines**. The five visited pages support the visible findings. The other 22 HTML routes need browser sampling/coverage as part of the release gate.
