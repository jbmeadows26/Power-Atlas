# Power Atlas — Interactive Visual Documentary Standard

**Decision:** Approved creative direction, November 12, 2026.
**Canonical working reference:** [Why does everything cost so much?](../../platform/unified/why-costs-more.html).
**Implementation status:** One working visual-story pilot on a review branch; not a claim that every existing page has been converted.
**Applies to:** Every new or redesigned public page, issue story, investigation, chart journey, comparison, and civic-action experience in Power Atlas.

## North star

**Make people experience an evidence-led story, not read a research paper.**

Power Atlas is an **interactive visual documentary about the systems shaping everyday life and the power people have to change them.** The visitor should be able to understand an issue without specialist vocabulary or scrolling through unbroken prose. Research is deep underneath, but the visitor's first contact is a visual question, interaction, and meaningful discovery.

Desired emotional arc:

**Curiosity → Discovery → Understanding → Agency → Constructive action.**

The design must inform and inspire without sensationalizing, guessing, manufacturing outrage, or claiming causation unsupported by records.

## Five non-negotiable experience rules

1. **Lead with a visual question.** A headline, illustration or evidence-backed comparison creates immediate curiosity. Do not start with a dissertation, dense dashboard, metadata table, or a pile of topic cards.
2. **Interaction must reveal knowledge.** Scrub time; choose a household cost; compare like-for-like units; follow a money trail; select a relationship; explore a location; uncover consequences. A click that only opens another wall of text is not an interactive discovery.
3. **Make complicated forces intuitive.** Build a short guided sequence. One clear visual insight per scene; progressively increase complexity only when the visitor requests it. Explain what the marks mean in plain language, without requiring a legend hunt.
4. **Separate story from proof without separating them intellectually.** Keep direct primary sources, reporting period, geography, definitions, calculation, limitations, and original records one accessible action away. Clearly distinguish **verified observation**, **plausible mechanism**, **inference/estimate**, **unverified lead**, and **unknown**.
5. **Give the visitor a meaningful next move.** Connect to their community where evidence permits. Offer the complete source, a relevant comparison, practical consumer choice, local civic process, or the existing Take Action journey. Avoid a generic 'learn more' dead end.

## Canonical storytelling structure

A chapter should normally move through:

| Beat | Visitor experiences | Implementation expectation |
|---|---|---|
| **The hook** | One striking, truthful question or comparison | Show first visual promptly. One short invitation to explore. |
| **The reveal** | A visual change they control | Slider, map, timeline, comparison toggle, selectable diagram, or causal-chain inspection. |
| **The connection** | Which institutions, markets, decisions, or trade-offs matter? | Allow taps on nodes/actors/decisions to see context. No unproven allegations. |
| **The consequence** | What is known about people and places? | Show actual source-scoped differences and uncertainty; don't invent personal bills. |
| **The evidence** | 'How do we know?' | Disclosure with dated source links, limitations and competing explanations. |
| **The agency** | What can people do next? | Contextual action linked to existing site routes and documented public resources. |

A story can have 3–6 scenes and may vary its visual form. Do not mechanically repeat a card template. The structure should guide pacing, not make every topic look identical.

## Interaction vocabulary

- **Time scrub:** Show exactly what changes with the chosen date; label initial and selected values and use consistent units.
- **Comparison:** Put values on a common honest scale, including a visible zero for magnitude bars. Say when periods, denominators, geographies or definitions differ. Respect [comparative chart standard](comparative-chart-standard-v6.md).
- **Follow the money / power:** Tap nodes/edges to reveal *documented* donor, corporate, policy or transaction relationships. Style and label unverified hypotheses differently; do not visually imply a proven causal chain from adjacency.
- **Choose your lens:** Let visitors switch between market, government and resident perspectives; keep each factual and acknowledge trade-offs.
- **Your place:** Reuse the site-wide saved ZIP through `pa-zip-persistence.js`. ZIP/ZCTA is neither exact address nor legislative district. Never guess local costs or representatives from a ZIP alone.
- **Evidence drawer:** Accessible source list, dates, methods, limitations, unanswered questions and raw figures. Disclosure must remain usable by keyboard and screen readers.
- **Action:** Relevant, bounded pathways that do not misrepresent legal rights or automatically send messages on users' behalf.

## Member-contact exception — intentional, narrow

The **Take Action / contact your members** flow is the **only intentionally different treatment** from the visual documentary's usual exploration panels. It stays in the same Power Atlas palette, typography, navigation, and evidence-led design. When the visitor transitions from discovery to personal advocacy, use a tactile, legible **letter/email composition** motif so the intent and next step are unmistakable.

- Choose one actual office, one issue, and one bounded request; no free-text bulk campaigning.
- Present a real email subject separately from a short, assertive-but-factual message; keep message length limited and reveal the full content before any handoff.
- Preserve the verify-your-district warning, official source links, alternate public contact channel, and appropriate caveats for state/local issues.
- **Temporary test mode:** route the email action into `platform/unified/contact-tester.html`, using tab-scoped `sessionStorage` solely for preview. This is an internal tester route, **not** a verified external tester plugin and **not** an email send. Do not imply delivery or fabricate recipient email addresses.
- When user login and the actual tester provider are configured later, replace the test-only adapter only after explicit integration, secure authentication, consent, recipient validation, rate limits and delivery QA. Do not send automatically or claim connectivity until a real integration exists.
- Deep public records, source review and other parts of Power Atlas continue using the common interactive documentary storytelling form, not separate design variants.

## Visual language

- Keep the **one canonical global navigation shell**, current floating desktop pill and mobile dock. Use the existing Power Atlas brand, cream/teal/deep-ink foundation, and a single shared header; use topic accents inside the scenes.
- Use generous whitespace, strong editorial typography, simple high-contrast illustrations, purposeful movement, and mobile-first visual hierarchies.
- Large data marks need visible values and readable labels. Icons and color are *supplements*, never the only explanation.
- Default to concise visible copy. Put definitions and nuance in accessible expandable evidence. Do not truncate a necessary safety/accuracy qualification simply to hit a word-count target.
- Scroll direction, animation, and transitions should support understanding, never conceal information. Respect `prefers-reduced-motion`.
- Implement actual `button` and `a` controls with focus styles, semantic states (`aria-pressed`, `aria-expanded` as appropriate), and a meaningful visible response.
- Preserve existing ZIP persistence, issue routing, evidence deep links, and bug-report control. No standalone nav theme, duplicate masthead, or hidden path to existing material.
- Use clear `scope` in CSS (story class or page prefix); avoid later global overrides that silently break other screens.

## Evidence / integrity requirements

Before a graphic makes an empirical claim, document: primary URL, original value, unit, timeframe, geography/population, transformation/denominator, retrieval or release date, and missingness. Use an existing source registry when possible.

- National CPI **does not** equal a ZIP-specific shopping basket, wage trend or market rent. Benchmark distinctions must be visible.
- HUD fair-market rent **does not** equal current asking rent; distinguish bedroom size, listing market, sample, vintage and limits.
- Donation records **do not prove** purchased votes, policy outcomes or price changes.
- Correlation, timing, affiliation and ownership links **do not prove** misconduct or causation. Show confirmed facts, suspected mechanisms and gaps separately.
- Bailout amounts, losses, repayments, penalties, shareholder gains and personal liability require separately sourced values and legal distinctions. Never infer who was 'held liable' from a settlement alone.
- Missing or outdated data stay visibly missing/outdated. Never use placeholder numbers that could be interpreted as measured facts.
- Avoid partisanship or misleading false balance: present credible evidence, relevant alternative explanations, and confidence proportionate to the sources.

## Acceptance gate for every migrated chapter

A chapter is **not finished** simply because its layout loads. Verify, on the actual preview revision:

1. **First impression:** the opening screen expresses the investigation visually, not as a text article. The question and visual are legible on 390px and 320px mobile and 1440px desktop.
2. **Working discovery:** every promised slider, selection, chart, node, map or reveal visibly changes the relevant content. Tap and keyboard controls work; selected states are announced.
3. **Truthfulness:** interactive values match cited datasets; every scale, baseline, date, jurisdiction and denominator is unambiguous. Unsupported links do not masquerade as proven causal facts.
4. **Progressive depth:** a visitor can get the basic story without opening the research; an investigator can reach original evidence in no more than a clear single action from the relevant claim.
5. **Agency:** a useful next step exists and reaches the correct working destination.
6. **Consistency:** one shared navigation, correct active state, saved ZIP, bug report, no legacy hero, no competing layout or hidden section.
7. **Resilience:** no broken resource requests or routes, console-breaking errors, jank, clipped labels or horizontal overflow. Verify no-JS fallback where appropriate, reduced-motion behavior and accessible focus.
8. **Source preservation:** do not delete or silently rewrite the original datasets, research methods, citations, or substantive content while converting the visual layer.

All site-wide regression tests remain required; see [single-shell contract](single-shell-contract.md). Browser QA is mandatory: static source checks alone are not proof of a finished interaction.

## Rollout sequencing

**Stage 0 — approved reference (completed in review):** `platform/unified/why-costs-more.html`; interactive price comparison, causal mechanism exploration, power lenses, source disclosures, local/community and action links. Featured entry inside 'What matters most right now?' on `my-life.html`.

**Stage 1 — unify the visitor journey:** retain one shell, simplify the My Place / What Matters Most / Follow the Power transitions, remove duplicate legacy presentation and ensure story entrypoints remain discoverable. Convert the high-traffic homepage scenes before converting deep research archives.

**Stage 2 — signature investigations:** Dark Money, political influence, Market Power, Banking/crashes/bailouts, Wealth Advantage. For money-flow and liability investigations, favor interactive traceable records over dramatic unsupported claims.

**Stage 3 — everyday costs / consumer power:** Housing and current asking rents (with bedrooms), transportation and freight pass-through, groceries and shrinkflation, telecommunications promotions, workforce automation, class actions and service accountability.

**Stage 4 — civic action and comparison:** Representative-contact journey, fair comparisons, local/municipal stories, economic fragility, voting and electoral reforms, accessible research archive.

Each stage must preserve deep links and research while converting visual storytelling; migrate screen by screen with preview QA. No new Vercel frontend or production merge purely for visual exploration.

## Anti-patterns — immediate redesign triggers

- Prospectus, white paper, journal article or long-scroll text with decorative charts.
- Massive dashboard / metrics grid as the first screen.
- Unexplained percentages and mismatched bar scales.
- 'Click to explore' that only reveals several dense paragraphs.
- Source citations detached from the graphic's actual claim.
- Two unrelated UI generations visible on one page.
- Localized or causal claims inferred from a ZIP, a donor list, or a corporate ownership list without adequate evidence.
- Unreadable mobile graphics, inaccessible hover-only discovery, or controls that appear clickable but do nothing.

## Implementation references

- Approved pilot: `platform/unified/why-costs-more.html`.
- Featured discovery: `platform/unified/my-life.html`, 'What matters most right now?'.
- Shared shell: `platform/unified/global-navigation.css`, `platform/unified/visual-story-v6.css`, `platform/unified/visual-story-v6.js`.
- Privacy: `platform/unified/pa-zip-persistence.js`.
- Existing acceptance tests: `tests/test_product_acceptance.py` and `tests/test_visual_stories_v6.py`.

**Status note:** The creative direction is approved. The pilot is implemented and has passed core live-preview interaction checks, but a platform-wide conversion and full visual acceptance suite have **not** been completed. Publish each reviewed migration deliberately; do not describe pending work as deployed.
