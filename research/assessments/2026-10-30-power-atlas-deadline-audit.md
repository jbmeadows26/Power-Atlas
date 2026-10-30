# Power Atlas — 30 October 2026 ingestion and release audit

**Evidence cutoff:** 2026-10-30 UTC. **Disposition:** `NOT NATIONWIDE COMPLETE`.  
**Repository:** https://github.com/jbmeadows26/Power-Atlas  
**Public interface:** https://power-atlas-research.vercel.app/  
**Validated release:** Vercel deployment `dpl_TcTBwU1x6SLXGG4mREeYLqzdSPxN` marked **READY**, production alias assigned, Git commit `1d01a78795e1a6cfb3bbb1370ec7e47461d7a573`.  
**Policy:** Free services only; respect provider licensing, rate limits, authentication and robots; source provenance and uncertainty required for all links.

## Completed and persisted components

| Evidence layer | Confirmed result | Meaning / caveat |
| --- | ---: | --- |
| Current members of Congress | 539 | Office identities; no inference of district-map participation |
| State legislators | 7,416 | 52 jurisdictions; public third-party roster requires state crosschecks |
| State executives | 170 | Includes governors; officeholding does not imply wrongdoing |
| Federal Article III judge appointments | 4,777 | FJC historical service appointments; not partisan decision ratings |
| State elections/redistricting committees | 62 | 706 source-listed membership roles; only 16 committees directly titled for redistricting/reapportionment |
| Research source records | 62 | Source-indexed; not 62 unique adjudicated cases |
| Graph edges | 2,625 | 1,269 official FEC candidate-committee associations; 627 third-party roster ID crosswalks; 706 committee memberships; 8 bill sponsor links; 15 secondary state bill-vote links |
| FEC committee identities | 673 | Official master data |
| FEC PAC/party financial cycle summaries | 135 | Official bulk 2024/2026; not evidence of payee-level transfers |
| FEC committee financial total records | 2 | Sample only; not complete candidate/campaign finance |
| Verified FEC intercommittee transfer records | 0 | Not collected; **not** a finding of no transfers |
| State redistricting legislative candidates | 568 | 136 direct redistricting title matches, others broader keywords / false positives |
| State/DC bill search first pages | 51 of 51 | One keyword, one page; **not** a complete state legislative history |
| Additional state bill search pages | 6 | IL, TX, MS, DC, OR, FL; more pagination remains |
| Secondary state legislative vote records | 15 | Only one official staff-summary aggregate crosscheck; no nationwide member-vote census |
| Official state election-office source links | 51 | Official directories only; **zero** certified statewide canvasses downloaded and reconciled |
| Historical House district-year results | 3,461 | Research election returns, 2010–2024 |
| House state-year totals | 402 | 263 derived descriptive seat-vote observations pass conservative checks; no gerrymandering scores |
| House 2024 district-key accounting | 436 of 436 | 434 vote-return rows, 2 officially documented unopposed-status-only; vote totals not certified |
| Census congressional map editions | 2 | Generalized 116th and 119th Congress cartographic geometry; not every enacted legal plan |
| Official 2025 House roll-call XML | **150 of 150** | Requested bounded House roll window complete, primary-source indexed; not all years, not state-level votes |
| Selected Supreme Court map/elections decisions | 9 | Selected cases, not national litigation census |

## Repaired blockers

1. **Rhetoric CI fraction:** corrected test expectation of 2 hedge tokens / 5 words to 40%; full validation subsequently passed.
2. **Frontend validator:** accepts external JS modules as distinct from the single inline application script, and checks separate JS syntax.
3. **State pagination:** source-backed incremental pagination now reconciles staged bill indexes before executing cross-domain integrity tests, then safely publishes checkpoints; first extra six pages succeeded.
4. **House votes:** primary House Clerk XML uses `Aye/No` for some procedural votes, plus named candidate selections for the Speaker vote. Parser now correctly normalizes procedural labels while preserving Speaker choice and original vote-label counts. All 150 target rolls published, with source hashes. A claim about partisan alignment or constituent preferences requires separate evidence.
5. **Publishing:** GitHub Actions workflows persist compact files with source URLs and conflict-safe updates. Daily free Vercel rate caps remain a constraint, but the latest public UI release was verified READY.

## Nine still-blocking nationwide evidence gates

See [machine-readable completion gates](../../data/health/completion-gates.json), which are maintained by a free scheduled GitHub Actions audit:

- Exhaustive state legislative redistricting bills, pagination and session history
- Actual state-certified election vote totals and reconciliation by year/contest
- Nationally comprehensive state campaign contributions and recipient identities
- Official individual state legislative roll-call/member voting records and map votes
- Verified financial transactions, not just PAC/party monetary totals
- Full federal lower-court and state-court redistricting dockets and dispositions
- State judicial selection, appointment, retention and election histories
- Legal version histories of enacted, superseded, enjoined and court-ordered maps
- Primary-source-proven actor-to-decision causal relationships connecting financiers, advisers, officeholders, lawmaking and litigation

**Interpretation rule:** A successful collector run or membership edge cannot establish corrupt intent, improper conduct, a causal effect of district design, or exhaustive coverage. Public first-page search results are **not** complete jurisdiction coverage; the absence of rows is not evidence of no political activity.

## Operational status

- Source-independent GitHub data validators and frontend syntax checks have most recently completed successfully on the corresponding commits.
- Official House roll-call collector has a complete bounded 150-roll 2025 window with cryptographic completion receipt: [political-authenticity CI health](../../data/health/political-authenticity-ci.json).
- State search pagination and evidence reconciliation continue under bounded free source schedules. The [GitHub Actions dashboard](https://github.com/jbmeadows26/Power-Atlas/actions) is authoritative for subsequent run outcomes.
- The UI provides on-demand primary House roll-call research and an explicit readiness panel on the **Evidence & gaps** tab, with direct access to source data.
- **No scientific field experiment, complete national gerrymandering attribution network, or peer-reviewed causal gerrymandering determination has been produced.** These cannot be truthfully marked complete without relevant additional primary sources, peer review, and in some cases real-world data collection.
