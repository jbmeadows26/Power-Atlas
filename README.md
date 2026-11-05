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

## Dark Money Tracker — first-stage cross-jurisdiction evidence engine

- [Visual Dark Money Tracker](platform/unified/dark-money.html): six election-type choices, 2024/2026 FEC committee-cycle charts, source status, original filings, and a documented-payment discovery view. [Unified portal](https://power-atlas-unified.vercel.app/dark-money.html) may lag source commits until deployed.
- [Reproducible graph](data/money-influence/dark-money-graph-v1.json) generated by `python -m scripts.build_dark_money`: 135 existing source-attributed FEC committee-cycle snapshots, 76 distinct indexed committee IDs, and **zero imported itemized transfer edges** as of this initial build. No original hidden donors are identified.
- [Privacy-gated organizational transfer staging ledger](data/money-influence/reviewed-organizational-transfers-v1.json): deliberately empty. Only public organizational endpoints, stable IDs, filing ID, HTTPS evidence, and explicit human review are accepted; no private individuals or addresses.
- The graph flags possible **sequential payment leads** only when there are two *actual* filing-backed edges joining the same verified entity, within 45 days and within 5% of the incoming amount. Such a pattern is not proof the same dollars moved, misconduct, or shared ownership. **Fuzzy names, matching vendors, registered agents and GNN output never create direct financial edges.**
- Federal FEC disbursement collectors rebuild this graph when new official committee-to-committee records pass their source checks. Existing [source registry](data/money-influence/source-registry-v1.json) remains authoritative on state, IRS and local ingestion limits. State/municipal/ballot portals currently provide links, not itemized cross-jurisdiction transactions.
- Next data phases require audited local PDF table extraction, state and IRS 990 Schedule I outbound-grant connectors, human verification of entity identity, and a jurisdictional licensing review before publication. Donor Schedule B names of most 501(c)(4)/(c)(6) groups are not public; the engine cannot reveal them by inference. No OCR/GNN models or fifty-state transaction ingestion are claimed complete.

Run `python -m unittest discover -s tests -p 'test_dark_money.py' -v` after rebuilding. The `.github/workflows/validate-dark-money.yml` workflow also checks dashboard JavaScript syntax and graph reproducibility.

## Itemized dark-money investigation follow-up (November 5, 2026)

The official federal FEC OTH 2026 collector scanned 10,006,076 source rows and published a capped subset of **1,200 registered-committee receipt-side records** from 3,429 eligible items involving selected PAC/party committees. The graph includes 449 distinct committee identifiers and 10 time/amount similarity leads. These are not a national census or proof of money laundering, donor identity or coordination.

- [FEC reported registered-committee receipts](data/finance/fec-committee-transfers.json) include the archive SHA256, filing IDs, category codes and sampling limits; no personal donor names, addresses, memo items or unauthorized inferred LLC owners.
- [Updated source-backed money graph](data/money-influence/dark-money-graph-v1.json).
- [Official FEC bulk format](https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/) and [receipt-type codes](https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/).

**State context (not transfer edges):** scripts/collect_wa_2026_aggregate.py fetches PDC 2026 financial summary rows grouped by filing class on the state server, publishing only classes with >=5 rows. It never downloads or republishes person-level datasets. PDC noncommercial restrictions on individual lists remain applicable. Figures are not reconciled individual transactions or election-cost totals; the source and license gate are visible in the output.

**IRS pilot (parser available, not backfilled):** scripts/parse_irs_schedule_i.py accepts selected official IRS Form 990 XML and filters for Schedule I grants between organizations with explicit EINs. It retains ZIP archive/member provenance, excludes personal information, and labels grants as non-campaign transfers. **No IRS documents or IRS↔PAC funding edges have been verified or ingested yet.** Nonprofit Schedule I grants do not identify original dark-money donors.

Regression tests include tests/test_fec_oth.py, tests/test_irs_schedule_i.py, tests/test_wa_2026_aggregate.py and tests/test_dark_money.py; GitHub CI also checks frontend JavaScript and graph reproducibility.

## 2025 New York City municipal campaign financial analysis

`python -m scripts.collect_nyc_cfb_2025` queries official [NYC Open Data, Campaign Financial Analysis](https://data.cityofnewyork.us/City-Government/Campaign-Financial-Analysis/m3tj-a2pb), a Campaign Finance Board candidate/campaign-level dataset. The resulting `data/finance/nyc-cfb/campaign-financial-analysis-2025.json` shows per-source-row 2025 net contributions and matching-fund claims, with office, candidate ID, source query and SHA-256. These are **not itemized PAC transfer edges, hidden-donor identities, awarded public matching payments, or audited citywide totals**. Source rows may be borough/district-specific and cannot be added without reconciling their grain. The city dataset is scheduled for a no-cost weekly refresh and the dashboard shows office filters, plain-language labels and source links.

## Targeted IRS Schedule I outbound organizational-grants pilot

Power Atlas can now retrieve the indexed **2024 tax-year Sixteen Thirty Fund Form 990** from the official IRS 2025 XML ZIP batch, parse its public Schedule I organizational grants using recipient EIN, and publish only `data/finance/irs-schedule-i-grants-v1.json`. The audited filing inventory is `data/finance/irs-focused-filing-inventory-2025.json` (2 known 501(c)(4) organization entries selected after checking 748,906 official IRS index entries). The pilot collector deliberately limits its first run to one independently source-verified EIN (`264486735`), checks batch and XML checksums and official archive membership, keeps recipient EIN and organization name, and omits private donor lists, addresses, officers and other personal details. The pilot never turns a Schedule I nonprofit grant into a proven PAC donation, lobbying act or original hidden-donor attribution. If downloading or parsing the original IRS ZIP fails, the workflow fails without publishing fabricated financial links. Source provenance, completeness and the unverified political purpose of grants must be disclosed in the dashboard.

## Civic Power & Reform Lab (November 5, 2026)

- [Interactive civic-power dashboard](platform/unified/reform-lab.html) joins the current [Dark Money Tracker](platform/unified/dark-money.html) in the unified portal. Four plain-language themes group **16 candidate reforms** across disclosure, concentrated donor access, citizen financing, and enforcement.
- [Versioned reform catalog](data/money-influence/civic-power-reforms-v1.json) records current-law baseline, proposal, potential benefit, tradeoff or legal obstacle, measurable outcome, and original-source URL for each option. All entries are **policy proposals, not already-enacted nationwide rules**.
- The page uses an illustrative $5–$200 donation slider and no-match, 6:1 or 8:1 options; results are **arithmetic illustrations only**, not eligibility assessments or fiscal predictions. NYC public matching and Seattle vouchers are current local examples with rules that vary by office and election.
- The $200 federal contributor itemization threshold is not a universal 24-hour disclosure requirement. Certain federal independent expenditures already require 24-/48-hour reports; most nonprofit Schedule B donor identities are not public. Broad caps on independent political spending face constitutional precedent obstacles. The app never imputes undisclosed original donors or illegal influence.
- Run `python -m unittest discover -s tests -p 'test_civic_power_reforms.py' -v` to validate policy-card coverage, source links, legal distinctions, dashboard links and interactive arithmetic. This adds no collector or paid dependency. As with other frontend changes, **a repository commit is not proof of a production Vercel deployment**.
