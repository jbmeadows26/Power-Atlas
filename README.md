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

## Unified Power Atlas portal

[Unified public research portal](https://power-atlas-unified.vercel.app/) brings together the redistricting investigation, native Voting Access source comparisons, research-program directory, and evidence/coverage status. Source: [platform/unified/index.html](platform/unified/index.html). Original Vercel sites remain preserved and linked; embedded original content may depend on upstream frame policies. A unified navigation does **not** imply that every underlying data source has been fully ingested or independently validated.

## Money and influence: midterm donor intelligence

- [Interactive top-40 donor dashboard](platform/unified/donor-intelligence.html) — mobile-first 2014, 2018, 2022 and 2026 cycle comparison with party alignment, sector, dark-money share, search, year filters and ranked records.
- [Imported Brennan Center donor reference (160 rows)](data/money-influence/brennan-top40-midterms-2014-2026.json) — curated third-party snapshot from [Brennan Center research](https://www.brennancenter.org/our-work/research-reports/big-changes-makeup-biggest-midterm-donors) (updated October 29, 2026), with original source CSVs [here](https://github.com/zhangj-brennan/mip_top_40_donors). Data cut off on October 14 of each listed cycle. Dollar amounts are nominal, not inflation-adjusted.
- Donor rows may combine couples and company principals. **A listed donor, dark-money designation, sector or party alignment is not evidence of illegal conduct or a donor-to-candidate/policy causal link.** Recipients, FEC transaction IDs, spending vehicles and lobbying/legislative linkages are **not** populated by this dataset. No totals outside the top 40 should be inferred.

## Election funding across presidential and midterm cycles

- [Primary election money dashboard](platform/unified/election-money.html): source-attributed presidential + congressional cycle comparisons, donor extracts and availability signals.
- [FEC 2002–2026 cycle data](data/money-influence/fec-federal-cycle-overview-2002-2026.json): 13 even-year cycles, consistent first-18-month congressional receipts; 12 full congressional reporting cycles; presidential totals where documented. 2026 FEC statistics cut off at June 30, 2026 and are not final-cycle numbers.
- [OpenSecrets presidential donor excerpts](data/money-influence/opensecrets-presidential-donor-excerpts-2020-2024.json): 7 ranked 2020 donors and 11 ranked 2024 donors, **not** a full ranking. Keep separate from the Brennan Center’s curated top-40 midterm figures, which use different source and scope.
- Federal financial summaries cover primaries, general and certain special elections within the corresponding two-year reporting period; state/local/off-year elections and ballot measures are **not** represented in FEC federal totals. Do not add candidate receipts, PAC receipts, party receipts and independent expenditures to claim a total election cost: overlapping flows cause double-counting.

## Political-money source registry and evidence explorer (November 2026)

- [Money source explorer](platform/unified/money-sources.html) connects the Election Money dashboard to **17 curated source destinations**: FEC, IRS 527 disclosures, U.S. lobbying/LD-203, CA/NY/NYC/TX/NJ official disclosures, ProPublica Nonprofit Explorer, OpenSecrets, Brennan, Stanford DIME, Plural/OpenStates, Campaign Legal Center, Common Cause, California Power Search/MapLight and the historical Sunlight archive.
- [Source registry with status, topic, access and limits](data/money-influence/source-registry-v1.json) distinguishes **partially indexed** datasets (FEC, LDA), **curated research extracts** (OpenSecrets, Brennan), **source-linked but not ingested** (IRS, state, ProPublica, etc.), and research/archive references. A source link is not itself a completed data ingestion.
- [Existing evidence preview](data/money-influence/verified-record-previews-v1.json) publishes 135 compact FEC PAC/party committee cycle summaries (69 for 2024, 66 for 2026) and 56 LDA issue-related filing matches from existing files, with privacy minimization. The 2024 and 2026 committee summary reporting cutoffs differ. No state finance transaction import, original-donor determination, LD-203 contribution ledger or actual donor-to-recipient funding edge has been established by adding these links.
- Current [coverage](data/coverage.json) contains 1,269 FEC candidate/committee registration associations and **zero** validated recipient aggregates or committee-to-recipient payment rows. These are identity/registration links, not a financial-transfers graph.
- Academic reuse, state field redaction, provider terms, rate limits and current vs. archived status must be respected. Stanford DIME's public ODC-BY citation does **not** waive separate restrictions on its itemized data sourced from third parties. Watchdog complaints are allegations unless an adjudication proves otherwise.
