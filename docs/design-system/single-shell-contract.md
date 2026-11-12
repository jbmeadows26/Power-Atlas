# Power Atlas | One visible design and navigation shell

Status: approved V6 visual-first system · November 2026. This contract is enforced by `tests/test_visual_atlas_production.py` and the production visual-atlas GitHub Actions gate.

## Approved interactive-documentary experience (2026-11-12)

The **visitor experience standard** is now the [Interactive Visual Documentary Standard](interactive-documentary-standard.md), with the approved [Why does everything cost so much?](../../platform/unified/why-costs-more.html) story as its working reference. The single V6 shell, brand, navigation, verified data pipelines and evidence preservation **remain required infrastructure**, but a consistent shell alone is not a finished experience.

**Every new or redesigned investigation must now tell a short visual story and support meaningful user-directed discovery**: initial visual question, working comparison/interaction, source-scoped explanation, evidence one clear action away, and relevant agency or action. Decorative charts plus paragraphs, fake interactive controls, and multiple visible design generations fail this acceptance gate. Conversion is progressive, not permission to delete research or break existing links.

## Default design policy for every future change
Every new page, section, chart, module, investigation and redesign **must use the approved V6 visual-first Power Atlas shell from its first implementation**, not just link its CSS or JavaScript. The canonical navigation, palette, visual introduction, interactive graphics, short summary and expandable evidence are mandatory release criteria. Standalone layouts or competing theme systems are defects. Merge/publish only after checking the visible result on desktop and mobile. Existing research data and citations must survive the visual conversion.

## Canonical presentation owners
- `visual-story-v6.js` and `visual-story-v6.css` own the homepage visual stories, every primary page's compact visual-first introduction, and the single mobile menu.
- `global-navigation.css` owns the shared primary-navigation styling. Keep identical copies in `platform/unified` and `site`.
- `atlas-visual-system.js`, V5 and older page-specific components may continue supplying reviewed charts, data, and fallback content. They must not produce a second visible masthead or alternative primary navigation above the V6 story.
- Use one brand wordmark/header. Detailed investigations can have contextual breadcrumbs, in-page tabs, and related links **below** the page introduction. Related research should be progressively disclosed when practical.

## Six canonical navigation destinations
All journeys resolve to `https://power-atlas-unified.vercel.app/` on either production site:
1. Start Here → `my-life.html#where`
2. Issues → `my-life.html#what`
3. Costs → `my-life.html#benchmarkStory`
4. The Why → `my-life.html#why`
5. Actions → `take-action.html`
6. Research → `index.html`

Community pages set the active item from their current section. Cost investigations use **Costs**; other research investigations use **Research**. The mobile menu must expose the same items in the same order.

## Visible layout and CSS rules
- Use the shared cream, teal, dark-ink and navy palette for the visual-first cover and global navigation. Topic-specific color accents in subordinate charts are allowed; do not replace the platform's outer shell.
- Public topic covers (Dark Money, Market Power, Consumer Watch), Take Action and expanded Research share a centered maximum-width cream or white editorial outer frame with common typography. Topic-specific colors belong in interior evidence graphics, not the overall page frame.
- Prefer one graphic and one clear takeaway initially. Place detailed charts, source notes, methods and unknowns behind an explicit action.
- Scope new CSS under a page or component class (e.g. `.mpx`); do not introduce global `header`, `nav`, `body`, `.hero`, `--paper`, or `:root` overrides that compete with the shared visual shell.
- Do not append late `!important` theme overrides duplicating a previous V6 selector. Recheck computed styles at desktop and 390px mobile, not just CSS source order.
- Legacy non-JS headings can remain as fallbacks. On enhanced pages they must not stack another hero over the V6 one.

## Evidence and route integrity
- Public `data/` under the repository root is **not automatically mounted** beneath the Vercel HTML project root. Client code should request the canonical public raw GitHub evidence file first, or a file explicitly shipped in the deployment. Avoid guaranteed local 404s.
- Maintain source timestamps, geographic and methodological scope, and separate observed ownership/influence relationships from proven household price effects.
- Never replace a unique evidence view with invented figures merely to match the visual style.

## Release gate
Before merging a design change, verify across `platform/unified` and `site`:
- Identical shared V6 and primary-nav assets; exactly one visible global header.
- Correct six-link labels, active state, and mobile menu behavior; no duplicate brand strip.
- No broken local routes or network errors, and no horizontal overflow at 390px.
- Source-backed controls still work after `Explore the evidence`; source links remain reachable.
- GitHub Actions tests pass, including real Chromium screenshots and computed-style checks at 390px mobile and 1440px desktop across the critical routes, plus evidence-reveal and navigation tests; inspect the exact revision in a review preview before release. If deployment quota blocks the preview, do not claim that untested code is live.

This does **not** require every investigation to have identical charts. Their data stories can vary; the interface's navigation and core visual hierarchy cannot.
