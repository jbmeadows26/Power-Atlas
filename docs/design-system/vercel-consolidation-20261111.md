# Power Atlas — one production Vercel project migration

Date: November 11–12, 2026
Status: implementation staged, **old Vercel projects not retired**.

## Canonical destination

- One public site: https://power-atlas-unified.vercel.app/
- Existing Vercel project ID: `prj_tHx9Vexet5tJjnAjcq0ZbeFoh4Er`
- One production branch: `jbmeadows26/Power-Atlas` → `main`
- Deployment root: `platform/unified`
- All new work reviewed with branch-based previews of the Unified project. Production aliases must resolve to the same reviewed `main` SHA.
- One global V6 editorial shell, with deep evidence preserved behind explicit Explore controls.

## Verified Vercel project inventory

| Existing Vercel project | Project ID | Existing public domain | Target |
|---|---|---|---|
| Unified | `prj_tHx9Vexet5tJjnAjcq0ZbeFoh4Er` | `power-atlas-unified.vercel.app` | Keep |
| Research | `prj_qTYTRaPd37w9JcW5lNbTixexlNr3` | `power-atlas-research.vercel.app` | Migrate then redirect/retire |
| Visual Review | `prj_bbLAV2ABCMJL6iWbfYNkVfzAB7Gn` | `power-atlas-visual-review.vercel.app` | Replace with Unified previews after reconciling unmerged action branch |
| Voting Access | `prj_Ehi2auVR2sVAu6HyOHQvGAy6SnYa` | `power-atlas-voting-access.vercel.app` | Migrate then redirect/retire |

The production Unified project is READY; three other project names and their deployments are confirmed in the Vercel account. The Visual Review project has additional Take Action work on `feature/action-accountability-language-20261111` relative to `main`. Preserve and reconcile that unmerged branch before retirement.

## Route-by-route preservation

| Previous location | Canonical route | Preserved components |
|---|---|---|
| Research frontend home `site/index.html` | `/research-archive.html` | Institutional trust, political authenticity, campaign promises, hyperpartisanship, legislative/public-money records, filters and original sources |
| Research economic-fragility investigation `site/economic-fragility.html` | `/economic-fragility.html` | Market stress, financing, pathways, cited observations and original snapshot JSON |
| Voting Access frontend `research/voting-access/index.html` | `/voting-access.html` | NCSL ID categories, early/mail voting, state-law verification coverage, source-attributed studies and date limits |
| Existing Unified homepage | `/my-life.html` | Location-first ZIP entry, stories, costs, original data methods and civic entry points |
| Existing Unified research dashboard | `/index.html` | Complementary compact research discovery |
| Other existing Unified modules | Existing paths under `/` | Dark Money, Market Power, Consumer Watch, Take Action, corporate ownership, cases, tax rules, etc. |

New routes use the canonical V6 introductory shell. Older charts and research tables remain interactive inside clearly labeled evidence disclosure; they must not reintroduce a second masthead or an alternative public theme.

## ZIP state migration

- `power-atlas:visitor-zip:v1` stores only a validated five-digit ZIP in browser `localStorage` under the canonical Unified origin.
- The saved ZIP is restored on `/my-life.html`, including its underlying data queries, without automatically scrolling to section 2.
- A sitewide ZIP chip links back to `/my-life.html#where`; the visitor can change or clear it.
- ZIPs are not put in the URL, server sessions, analytics payloads or public personal profiles. External postal/Census lookups follow the disclosed existing flow.
- Browser storage is origin-scoped: the older three sites cannot transfer previously saved ZIP data without explicit user action. Moving all future visits to the canonical origin resolves the fragmentation going forward.

## Go-live and retirement gate

1. Merge branch only after static contracts, all-route Chromium QA, desktop/mobile screenshots, ZIP preservation/clear, accessibility and working source links pass.
2. Build a **Unified project preview**, inspect the exact commit. Vercel SSO can block unauthenticated preview browser checks; use authenticated reviewer and Chromium CI as complementary evidence.
3. Compare old Research, Visual Review and Voting production routes and any remaining unmerged branch against canonical routes; add missing functions before retirement.
4. Deploy **only Unified** to production, verify the intended Git SHA at the canonical alias, and verify all canonical routes and third-party evidence access.
5. Replace old public domains with route-preserving permanent redirects to Unified. Preserve deep-link path mapping (Research root → `research-archive.html`, Voting root → `voting-access.html`, Visual Review root → `my-life.html`). Test each before pausing old projects.
6. Disable automatic production deployments for old projects and archive or pause them **after** redirect validation. Do not delete GitHub research data or unique evidence.
7. Keep the V6 visual acceptance test mandatory for all future page additions.

**Not yet done:** production cutover, redirect validation, old-project retirement, reconciliation of the unique unpublished Visual Review action branch. The branch itself is not a live release.
