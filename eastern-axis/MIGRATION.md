# Eastern Axis migration

Source snapshot: application version `1794894949348` (November 17, 2026). All 43 original source files are preserved unchanged in this directory; this document is additional.

This is a preservation snapshot, not yet a production-ready Vercel port. The React frontend imports `@appdeploy/client`. The backend imports `@appdeploy/sdk` and uses its router and database abstractions. Migrating requires replacing these dependencies with standalone Vercel API functions and equivalent durable storage; creating only a static frontend would leave the intelligence, country and Factbook APIs broken.

Do not use AppDeploy for new builds or deployments. Previous backend schedule definitions are preserved in `cron.json`. Verify evidence provenance, incomplete data warnings, and mobile navigation before production promotion.
