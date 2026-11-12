# Original-source gap closure — intake and execution

**As of 2026-11-12.** This is an execution register, **not** an assertion that nationwide research is complete. The machine-readable companion [ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json](./ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json) maps all **55 still-open sitewide local-life evidence gaps** and all **nine nationally blocking research gates** to source candidates, required joins and tool roles. The original [sitewide audit](../../data/health/sitewide-missing-sources-v1.json) and [completion gates](../../data/health/completion-gates.json) remain authoritative.

## Tooling already available

| Integration | Use | Boundary |
|---|---|---|
| GitHub | Build original-record collectors, version evidence, run source and join CI | A green build does not make a dataset complete |
| Parallel and Firecrawl | Discover, compare and retrieve government record portals and original filing schema pages | Do not pay for credits or equate portal discovery with ingested transactions |
| Legal Data Hunter | Search legal decisions and primary law | Published opinions are not a complete lower-court docket or final appeal chain |
| Scite / Consensus | Challenge causal claims with research and counterevidence | Published population associations do not prove effects in a specific ZIP |
| Data | Validate grain, record counts, temporal/geo joins, metric definitions and data quality | Keep benchmark, listing, contract and actual paid prices distinct |
| Quartr / SEC EDGAR | Locate public-company filings and ownership disclosures | EDGAR original source controls when determining legal ownership |

## Original source entry points checked today

1. **Federal committee contributions:** [FEC contributions from committees to candidates data dictionary](https://www.fec.gov/campaign-finance-data/contributions-committees-candidates-file-description/). The filer, recipient, amount and date fields are documented. This source is a *subset*, not a full PAC-to-PAC / committee-to-committee transfer census.
2. **Federal disbursements:** [FEC operating expenditure data dictionary](https://www.fec.gov/campaign-finance-data/operating-expenditures-file-description/) and [official bulk-data directory](https://www.fec.gov/data/browse-data/?tab=bulk-data). Operating expenditures alone must not be mislabeled as campaign contributions or verified influence.
3. **Virginia campaign finance:** [Department of Elections CSV archive](https://apps.elections.virginia.gov/SBE_CSV/CF/). The [2026-11 archive directory](https://apps.elections.virginia.gov/SBE_CSV/CF/2026_11/) exposed Report.csv plus ScheduleA–ScheduleI.csv as of 2026-11-12; **file bytes, row counts and schema remain unverified**. The [official reporting page](https://www.elections.virginia.gov/candidatepac-info/reporting/) links the original historical archive.
4. **Vermont campaign finance:** [Secretary of State transaction-level annual CSV downloads](https://campaignfinance.vermont.gov/public/cf/downloads), listed for 2014–2025 in the inspected portal, contribution/loan and expenditure categories. The portal states that large files and inadvertent errors are possible; no CSV backfill or completeness reconciliation has been performed.
5. **New Jersey campaign finance:** [Election Law Enforcement Commission search database](https://www.elec.nj.gov/publicinformation/searchdatabase.htm) lists searchable contributions to candidates, parties and PACs. An unrestricted bulk download is **not** confirmed.
6. **New Jersey election results:** [Division of Elections archive](https://www.nj.gov/state/elections/election-information.shtml) and [2026 year archive](https://www.nj.gov/state/elections/election-information-2026.shtml). Certified 2026 primary contest PDFs are indexed, while general-election reporting and municipal/county reconciliation require separate work; never conflate unofficial election-night results with certified canvasses.
7. **New Jersey roll calls:** [Legislature voting records](https://www.njleg.state.nj.us/voting-records). Individual legislator pages appear available, but a full machine-readable chamber/session census and redistricting-case selection are unverified.
8. **Washington roll calls:** [WA Legislature roll calls on a bill](https://app.leg.wa.gov/bi/RollCallsOnABill/RollCall?biennium=2025-26&billNumber=2618&initiative=False). Build on the already verified bounded WA pilot; do not classify all legislative votes as redistricting votes.
9. **Federal court files:** [Free Law Project RECAP coverage and ingestion description](https://www.courtlistener.com/help/coverage/recap/). RECAP can locate dockets and filed orders but is a **partial mirror**, not official PACER completeness. Link back to originating court, final disposition and appellate history.

All entry points were independently retrieved as pages or searchable catalogs. No candidate source in this intake was counted as a newly ingested original record. Source directory listings are *not* proof that their downloadable files were read, licensed or reconciled.

## First concrete collection wave

1. **Financial edges — federal:** Collect a limited set of original committee-to-recipient transactions with reporting committee ID, recipient identifier, date, amount, filing, amended-report status, unique record ID and source URL. Verify that a transfer is a real transfer (rather than an operating expense or refund), reconcile two ends when possible, and avoid duplicate counting. Only then update the federal financial-edge coverage gate.
2. **Financial edges — states:** Start Virginia (machine-readable public original monthly schedules) and Vermont (original transaction CSV exports); record source files, SHA-256 hashes, reported extraction time, schema and row counts. Identify whether public data may be reused before publishing raw or transformed records. NJ ELEC requires additional export discovery. Increment each state/domain source ledger only after successful retrieval and checks; a pilot never fulfills the nationwide gate.
3. **Vote and decision chain:** Pilot one official New Jersey certified contest/year, one official redistricting-related member vote, and one versioned enacted map with the associated court/legislative timeline. Validate office, jurisdiction, year and contest before joining.
4. **Local-life costs and ownership:** Work from the 55 existing questions in the JSON backlog, beginning with rental market asking-vs-contract prices, grocery baskets, actual utility tariffs and dated parent-company/property-operator joins. Public benchmarks and corporate lists must never be presented as the household's actual bill.

## Evidence acceptance rule

A local gap can only move to **resolved** if it has: (1) a directly accessible *original* dated record or authorized reproducible extraction, (2) explicit unit/geography/coverage boundaries, (3) deduplication and amendment handling, (4) independently checked joins and denominators, and (5) presentation that distinguishes verified fact, inference and unknown. National gates require a defensible defined jurisdiction/cycle census, not a few state pilots. Legally protected/private details must not be republished. No paid API credits, paid PACER retrieval or unlicensed copying are approved here.

**Implementation status:** Source-entry and worklist intake written; ingestion collectors, validation receipts, and empirical gap closures remain work to be done.
