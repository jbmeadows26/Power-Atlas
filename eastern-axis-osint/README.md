# Eastern Axis OSINT — Vercel migration

This is the Nov 17, 2026 full OSINT source snapshot ported from AppDeploy to Vercel. It is staged on a branch until browser QA.

- Vite/React UI, Vercel Node Functions, Neon persistence via EA_DATABASE_URL.
- Independent collection documents use table ea_osint_documents. Existing Power Atlas data is unaffected.
- AppDeploy-managed database contents and WARC objects have not yet been transferred.
- Archiving and generative AI must not report success until independent providers are configured.
- AppDeploy is not used for builds or deployment.
