# Eastern Axis: standalone GitHub and Vercel deployment

## Source migration

- Archived the **entire 43-file** original snapshot from revision `1794894949348` into `eastern-axis/`; subsequent commits port the runtime to Vercel.
- GitHub source: `jbmeadows26/Power-Atlas`, folder `eastern-axis`, Vercel project `eastern-axis-unified` (root directory `eastern-axis`).
- React/Vite frontend uses a same-origin API, not AppDeploy browser auth or runtime.
- Vercel Node API bundles the TypeScript backend; public source methods use their original provenance and caveats.
- `EA_DATABASE_URL` points to the user's Eastern Axis Neon database and uses isolated table `eastern_axis_v2_records`. Never publish this secret.
- Exported and imported **57** public historical source-index records, four dated source health snapshots, and OFAC metadata on November 17, 2026. The historical timestamps are preserved; this import is not presented as a new source check.
- Nine Vercel Cron Jobs refresh four primary feeds, military report metadata, UK and Canada sanctions, energy, and World Bank snapshots **daily**, secured by `CRON_SECRET` and returning 401 to public requests. The prior rotating allied ingestion interval is changed to daily due to Hobby limits; schedules are UTC with hourly-level timing precision.
- Mobile country selection scrolls to the selected Factbook dossier while preserving the country between tabs. Verified on 390-pixel mobile viewport for France, Connections and Global Systems.

## Caveats and open capabilities

- AI-generated military report comparison remains disabled until an independent approved AI provider is configured; requests must report unavailable, not invent reports.
- Immutable WARC object storage is not migrated; the storage adapter intentionally refuses archive writes and no immutable custody is claimed.
- The public original platform's collection snapshot is a **bounded sample**. Other unpublished/private backend state and previous binary objects have **not** been imported.
- Individual source endpoints can still fail independently; the UI labels them partial, unknown or unavailable and retains source dates.
- Cron execution is configured, but scheduled-job success must be verified from subsequent source health observations and Vercel runtime logs. Build validation alone cannot establish ingestion success.
- The existing `eastern-axis-resources-power` Vercel production project and any older AppDeploy app were not deleted or overwritten.

## Release verification

- Preview build succeeded, independent healthcheck and 10 additional intelligence/Factbook endpoints returned valid JSON.
- France historical profile and World Bank indicators loaded; mobile selecting France scrolled to the dossier.
- Cross-section state persisted on mobile. Unauthenticated scheduled collection request returned `Unauthorized`.
- Production release should be checked again after the GitHub branch merges to `main`; confirm production domain aliases and server logs.
