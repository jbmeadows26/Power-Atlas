# Dashboard release — November 2, 2026

Production: https://power-atlas-unified.vercel.app/
Application commit: 1368f7c0ca8f61d33a58d85425894a308379fc01
Vercel deployment: dpl_J3joNjg7D8BP4KkYTVhJmCJmF31J

The React application in this directory replaces the previous unified landing page. Original research deployments and data ingestion remain intact. Build: npm ci && npm run build. Vercel root: platform/dashboard; output: dist; framework: Vite.

## Implemented visual investigations

- Voteview strict party opposition, Congresses 100–119; chamber filter, exact-value table and CSV. Congress 119 remains incomplete.
- NCSL voter-ID categories, August 2026, 50 states plus DC. Secondary classifications, not verified current statutes.
- MIT-derived votes versus seats, election-year filter 2010–2024; comparable indexed state returns only. Unreviewed descriptive measures, not causal bias estimates.
- OECD national-government trust, country selector, 2023 versus 2025; underlying country evidence table and publication attribution.
- FEC indexed committee receipts, cycle selector 2024/2026; top six within the selected subset, not a national ranking. Official summary records remain unreviewed; 2026 partial.
- ACS resident/House roster age comparison, ages 25–34; explicit distinct population and date denominators; not an authenticity score.
- Eight provisional promise case timelines with original commitments and dated evidence; 24 unscored candidates are identified, not scored as broken.

Search covers indexed cases, congressional members and state committees. Source data is bundled in public/data for reliable same-origin loading. The copies are release snapshots and need deliberate refresh from repository data, not automatic reinterpretation of source status.

## Validation

TypeScript and Vite production build passed. Nine Playwright tests passed. Live production Chromium checks at 375, 768, 1280 and 1440 pixels verified five charts, politician search, mobile navigation, Senate selection and URL persistence, CSV downloads, no page overflow, and no captured runtime errors.

## Remaining scope

District maps, network diagrams, full entity profile pages, complete universal search, early/mail-voting dashboards, chart-image exports, reset controls, ingestion-driven snapshot refresh, complete source registry normalization, performance tuning and comprehensive accessibility certification remain unfinished. Do not represent this release as completing the original full platform specification. Vite reports a large JS chunk (~192 KB gzipped); Lighthouse scores have not been established. Data availability is not a substitute for primary-source verification.
