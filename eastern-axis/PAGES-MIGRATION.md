# Eastern Axis — GitHub Pages + Neon free-tier migration

## Current stage
This is a **staged** migration, not a claim of production cutover. The current Vercel dashboard remains unchanged until the Pages front end and Neon-backed API pass live tests. No Raspberry Pis or paid services are required.

## Reused source
- Existing React/Vite Eastern Axis interface: `eastern-axis/src`.
- Existing API contracts and intake logic: `eastern-axis/backend`.
- Existing connected Neon database: Eastern Axis Intelligence, with the `eastern_axis_v2_records` collection table.
- Existing source collection Actions: FARA and weekly source audit.
- Existing Power Atlas GitHub Pages publishing job: `.github/workflows/deploy-pages.yml`.

## Pages build
The release builds the Eastern Axis Vite app using `--base ./`, which supports the subpath `/Power-Atlas/eastern-axis/` without changing the Power Atlas home page. When a custom Pages domain is configured, relative assets still resolve.

The frontend calls the Neon Function HTTPS origin from the **nonsecret** GitHub Actions variable `EA_API_ORIGIN`. This must be configured to the verified Neon Function host before Pages can publish; it intentionally refuses a silent fallback to Vercel. Do not put database passwords, API keys, or private reports in `VITE_*` variables or the Pages artifact.

## Neon backend
`server/neon-function.ts` adapts the existing route handler to Neon's Fetch API and CORS for the Pages origin. `scripts/build-neon.mjs` compiles the existing backend to a standalone `index.mjs` bundle suitable for ZIP deployment through Neon Functions. Neon supplies `DATABASE_URL` internally. The existing driver expects `EA_DATABASE_URL`; the adapter sets that only **inside the server runtime**. Never publish the connection string.

Before cutover, validate every relevant GET/POST route: overview, intelligence, world signals, factbook, World Bank country brief, evidence, sanctions, supply chain, monitoring and collection health; validate cron auth (401 without secret); verify snapshot freshness and correct FARA/USGS behavior. A compiled bundle is not proof that the function is live.

## Monitoring and ingestion
Existing free GitHub Actions source collectors remain in place. Existing weekly audit must be retargeted after switching domains. Add an independent alert schedule only after official feed quality, rate limits, and source freshness are validated. GitHub Actions schedules are best-effort, not continuous real-time monitoring; show last checked timestamps and failures in the UI.

## Safety gates
1. GitHub Actions migration CI builds Pages and Neon artifacts successfully.
2. Deploy Neon Function and verify live database access, CORS and route contract.
3. Configure nonsecret `EA_API_ORIGIN` repo variable.
4. Confirm Pages is configured to deploy with GitHub Actions, then manually run the existing Pages workflow.
5. Run desktop/mobile, country persistence, navigation and data provenance QA before redirecting any existing public URL or disabling Vercel.
6. Keep charges at $0: do not enable paid Neon/Cloudflare features or purchase hosting.
