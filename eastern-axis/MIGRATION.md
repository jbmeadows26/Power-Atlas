# Eastern Axis migration status

- Original 43 source files preserved from version 1794894949348.
- Vercel builds the React/Vite client and serves it through a Git-linked project.
- Local same-origin HTTP client replaces @appdeploy/client.
- Local Node API handler and Postgres-backed collection store replace @appdeploy/sdk; database is a dedicated table named eastern_axis_v2_records using EA_DATABASE_URL.
- AI-generated summaries remain explicitly unavailable unless separately integrated; no false AI analysis is produced.
- WARC object-lock storage is not migrated; evidence archival is explicitly marked unavailable rather than invented.
- Database source states and original scheduled ingestion are **not** automatically transferred. Existing cron.json is a record of the previous schedule, not a Vercel cron configuration.
- This migration is not production complete until API routes, country navigation, source collection, source provenance and security have been checked against the old version.
