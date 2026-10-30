# Power Atlas — evidence-linked redistricting research

Power Atlas is a public, low-storage research index connecting redistricting cases, public officials, campaign committees, congressional elections, judicial appointments and geographic boundaries. **A source-indexed record is not a verified allegation of influence or misconduct.**

## Read-only datasets

- [Verified current coverage and known gaps](data/coverage.json)
- [Unified frontend JSON feed](data/app-feed.json) (compact; published separately from the frontend)
- [Original source-specific records](data/batches/) and [relationship evidence](data/relationships.json)
- [Federal judicial appointment index](data/judiciary/) and seven selected, official Supreme Court redistricting dispositions (three existing landmark records upgraded; four newly indexed)
- [2024 U.S. House district-key audit](data/health/house-2024-audit.json), distinguishing 434 reported-vote districts from two official unopposed-status-only districts
- [Voting Access & Electoral Representation integration plan](research/voting-access/POWER-ATLAS-INTEGRATION.md) and [source-attributed historical research seed](data/voting-access/evidence-seed-v1.json) — **not live state-law coverage**
- [Source refresh outcomes and preserved blockers](data/health/ingestion-status.json)
- [State finance and roll-call source probes](data/health/state-source-probes.json)
- [Frontend deployment health](data/health/deployment-status.json)

Data comes from public DOJ, FEC, U.S. Senate LDA, U.S. House Clerk, Census, Federal Judicial Center and Supreme Court records, plus explicitly attributed public/CC0 third-party sources. Each data product has a narrower scope than nationwide completeness; see its review status and limitations. Candidate-to-committee associations, memberships and judicial appointments are **not** findings of improper influence.

## Rebuild and verify

Run `python scripts/build.py`, then `python -m unittest discover -s tests -p 'test_*.py' -v`. GitHub Actions workflows collect bounded official-source data, publish compact JSON only after validation, and preserve existing source files when refreshes fail. A green collector run alone does **not** prove new rows were persisted: inspect source files, the coverage manifest and commit diffs.

## Deployment and free-service policy

[Production app](https://power-atlas-research.vercel.app/) is deployed separately from the GitHub-hosted feed. A READY Vercel deployment may serve an older frontend commit even while GitHub data is current; check [deployment health](data/health/deployment-status.json) before describing production as updated. No paid capacity, access bypass, rate-limit circumvention or unauthorized data redistribution is permitted.

The temporary deadline sprint ends after **October 30, 2026**. Remaining gaps include state campaign-finance transactions, state legislative roll calls, lower-court litigation dockets, state judicial-selection outcomes, and verified local/state election returns. The project intentionally excludes private addresses, contact details and unreviewed person-to-person allegations.
