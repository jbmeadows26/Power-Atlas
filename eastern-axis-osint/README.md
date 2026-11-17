# Eastern Axis OSINT — Vercel migration

This is the Nov 17, 2026 full OSINT source snapshot ported from AppDeploy to Vercel. It is staged on a branch until browser QA.

- Vite/React UI, Vercel Node Functions, Neon persistence via EA_DATABASE_URL.
- Independent collection documents use table ea_osint_documents. Existing Power Atlas data is unaffected.
- AppDeploy-managed database contents and WARC objects have not yet been transferred.
- Archiving and generative AI must not report success until independent providers are configured.
- AppDeploy is not used for builds or deployment.

## Scheduled collection
Vercel daily cron at 10:00 UTC runs official-source syncs and monitoring. CRON_SECRET bearer authorization is mandatory. The former six separate AppDeploy schedules are consolidated into one daily run for the Vercel Hobby plan; full coverage and collection freshness must be independently confirmed after the first runs. Archive objects and AI remain excluded.
