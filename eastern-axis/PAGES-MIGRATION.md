# Eastern Axis — GitHub Pages migration release record

## Architecture
- **Frontend:** GitHub Pages repository `jbmeadows26/Power-Atlas`, path `/Power-Atlas/eastern-axis/`. The existing Power Atlas site at the Pages root is preserved.
- **UI:** the current React/Vite Eastern Axis unified application, including the mobile navigation merged in PR #155 and country/social-indicator improvements merged in PR #156. The same country selector persists across major sections.
- **API:** the public Neon Function `eapublicapi` on the existing `Eastern Axis Intelligence` Neon project. The public, nonsecret HTTPS endpoint is recorded in `public-api-origin.txt`. Pages has no server-side execution and **does not** serve `/api`.
- **Database:** existing Neon PostgreSQL, isolated `eastern_axis_v2_records` table. The database and private credentials are never placed in public Pages assets or client-side `VITE_*` configuration.
- **Scheduled collection:** nine existing Neon Function schedules cover DOJ, FARA, CISA, OFAC, UK, Canada, energy, military reports, and World Bank snapshots. GitHub Actions handles source/connection/browser audits; these are not substitutes for real-time global monitoring.

## Verified gates (November 18, 2026 UTC)
- Current backend recompiled from the migration branch based on GitHub `main` after #156; Neon Function deployment **3** completed.
- Official source parser tests, Pages Vite build, and independent Neon backend compile passed in GitHub Actions.
- Fixture-backed mobile navigation passed **320px and 390px**, plus desktop.
- Live Neon audit returned expected JSON/CORS contracts for **21 routes**, including source summaries, sanctions, the Factbook, aviation/environmental signals, supply chain, evidence workbench, and country systems. Minimum observed indicator completeness for WLD, US, CN and IR passed; each nonmissing observation was checked for date/source.
- Independent browser QA passed at **1360px and 390px** against the live Neon API, including country selection across tabs and persistence after reload.
- An HTTP-200 response is not evidence that every upstream public feed is current. Data limitations and source dates must stay visible.

## GitHub Pages release gate
The existing `.github/workflows/deploy-pages.yml` now packages **both** websites into one Pages artifact and is configured to trigger on qualifying GitHub `main` pushes or manual dispatch. Before publishing it rechecks the live API, builds Pages-relative assets, reruns fixture mobile QA and real-API desktop/mobile navigation, and confirms that the Power Atlas root page remains intact.

**This document is not proof the Pages deployment succeeded.** Verify the GitHub Actions Pages deployment status and the actual Pages URL before describing the migrated frontend as live. GitHub repository Settings → Pages must use **GitHub Actions** as its publishing source; if that admin setting is missing, the deploy job will fail rather than publish an unverified page.

## Boundaries and rollback
- Preserve the existing Vercel production aliases until GitHub Pages is confirmed publicly reachable and navigable. No AppDeploy workflow or paid hosting upgrade is involved.
- GitHub Pages is a static origin; ongoing operational API and database work remains on Neon, not on the GitHub Pages server.
- AI-generated military comparison is intentionally unavailable until a separately reviewed provider exists. Immutable WARC custody and comprehensive global live feed coverage are not claimed.
- The `migration/eastern-axis-pages-free` branch retains a separately captured historical 53-file resource-dashboard snapshot as an archival reference, not the active merged dashboard.
- Existing Power Atlas content is not removed; rollback of the Pages release can be made by reverting the publishing workflow and rerunning the previous static-only Pages action.
