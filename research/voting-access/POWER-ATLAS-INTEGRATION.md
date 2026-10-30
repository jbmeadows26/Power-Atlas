# Voting Access & Electoral Representation — Power Atlas integration
**Research date:** 2026-10-30 · **Status:** source-indexed research protocol; not a 2026 nationwide legal audit or proven causal finding.

## Product scope
Treat gerrymandering and voter access as complementary but analytically distinct pathways to representation. Map boundaries determine which voters are grouped into districts; election administration determines which eligible residents register, obtain and cast ballots, and have ballots counted. Do not infer unlawful intent from outcome disparities, party affiliation, a closure, an administrative rule, or an association alone.

### Navigation / user experience
Add a **Voting Access** investigative section alongside Redistricting, Courts, Campaign Finance and Influence Networks.
1. **United States overview:** 50 states + DC, latest verified law snapshot, source freshness, state-level completeness. Filters: state, cycle, policy, voting method, effective date, demographic group, evidence confidence.
2. **Policy tracker:** actual statutory requirements (in-person photo/non-photo ID, alternatives and cure, mail ID, citizenship proof, registration methods and deadlines, early voting, mail windows, dropbox rules, ballot collection, assistance, language/disability access, felony rights, residency).
3. **Access geography:** geocoded polling sites and changes with date-bounded denominator, travel/accessibility, precinct boundaries, registered voters per site, observed wait times. No automatic suppression flag based on closures alone.
4. **Participation & ballot processing:** CVAP denominators, registration, turnout, rejected and cured mail/provisional ballots, disaggregated where defensible; side-by-side trends with uncertainty and denominators.
5. **Court & legislation timeline:** law version -> sponsor/recorded votes -> effective/enjoined/overturned status -> case and holding -> operational rule; distinguish opinion date, effective date and current enforceability.
6. **Connections / causal investigation:** trace verified government actions, appointment records, committee memberships, lobbying/funding records and district changes; relationships never assert intent or coordination without direct evidence.
7. **Scenario lab:** transparent, labeled counterfactual models for turnout/access and alternative district plans; NEVER present simulated additional votes or seats as observed outcomes.

## Mechanisms for source ingestion
- District engineering: partisan/racial packing and cracking, at-large and multimember systems, prison-population allocation, annexation and local electoral structure, mid-decade redistricting and administrative boundaries.
- Voting eligibility: age/citizenship/residency, felony disenfranchisement and restoration, documentary proof requirements, registration barriers and citizenship checks.
- Roll maintenance: legitimate moves/deaths/duplicates versus erroneous removals; notice, timing, reversals, re-registration and matching error rates.
- In-person access: ID types and reasonable impediment options; polling-site locations, hours, staffing, equipment, lines, transport and ADA accessibility.
- Remote voting: early-in-person, absentee eligibility, mail ballot request/receipt deadlines, identification, signature matching, dropboxes, ballot assistance, rejection and cure.
- Ballot processing: provisional ballots, precinct mismatch, challenged ballots, recounts, litigation-driven rule changes.
- Representation and governance: county/state election officials, secretaries of state, boards, legislatures, governors, judges, DOJ and relevant organizations; source-verified official action only.
- Additional relevant access dimensions: language support (VRA §203), disability access (ADA/HAVA), Native/tribal geography, overseas/military voting (UOCAVA), natural-disaster emergency changes, election intimidation and misinformation (separate documented conduct from allegations), local elections and ballot access.
- Elections security: administrative rationale, documented fraud incidence and error control, chain of custody, registration integrity and the measurable burdens of each safeguard.

## Data contract (version 1)
One *rule version* per state, voting method, issue, election type and validity interval—not a single timeless strict/non-strict label. Use normalized records:
`jurisdictions(id, name, level, parent_id, geo_id)`;
`policy_rules(id, jurisdiction_id, topic, election_type, method, requirement, exceptions, effective_from, effective_to, legal_status, checked_at, primary_source_url, source_quote, review_status)`;
`legislative_actions(id, bill_id, sponsor_id, chamber, date, action, official_url)`;
`litigation(id, case_name, court, docket, filed_on, decided_on, holding, issue, disposition, appeal_status, checked_at, source_url)`;
`polling_sites(site_id, election_id, jurisdiction_id, lat, lon, active_from, active_to, accessibility_status, official_source_url)`;
`access_observations(id, election_id, geography_id, subgroup, metric, numerator, denominator, value, data_method, estimate_ci_low, estimate_ci_high, source_url, source_year)`;
`entities(id, type, canonical_name, authority_id)`;
`relationships(from_id, to_id, relationship_type, observed_on, source_url, evidence_status)`;
`research_claims(id, claim_text, jurisdiction, period, evidence_type, source_url, confidence, limitations, review_status)`.
All identifiers immutable; preserve raw sources, capture license terms, retrieval timestamp, source revisions, exact observation definitions, race-estimation method, uncertainty, and audit trail. Never expose individual voter records or private residential coordinates.

### Data pipeline and tests
1. Official law/case source discovery -> timestamped raw snapshots -> normalized, date-effective records; human review before labeling present law.
2. Ingest election returns (state election administrators), EAC EAVS, Census CVAP/ACS/CPS, district shapefiles and MIT Election Data + Science Lab / Voting and Election Science Team datasets when licensed.
3. Reconcile geographic identifiers, election-year boundary editions, denominators and changed sites. Separate missing from zero and no-observation from no-harm.
4. Validate citations/URLs, record IDs, overlapping effective periods, recognized legal statuses, election dates, denominator > 0, plausible turnout (0–100%), geographic joins and point-in-time snapshots.
5. Publish static compact **separate** `data/voting-access/` feed rather than silently inflating the main redistricting `app-feed.json`; expose via frontend only after its deployment is independently verified.
6. For causal effects preregister treatment/exposure, comparison unit, parallel-trend and spillover diagnostics; show associations separately from quasi-experimental estimates.
7. Constrain cost: public/free authoritative bulk downloads and bounded scheduled refreshes, use stable caches and GitHub Actions quotas, no paid API assumptions.

## Evidence review: publish with qualifications
- *Shelby County v. Holder* (2013) invalidated §4(b)'s coverage formula, disabling its use for routine §5 preclearance until a valid formula applies; §5 itself was not struck down.
- *Rucho v. Common Cause* (2019) held federal partisan-gerrymandering claims nonjusticiable as political questions; racial-gerrymandering and VRA claims remain distinct.
- *Crawford v. Marion County Election Board* (2008) upheld Indiana's particular ID framework, not every ID law.
- *Brnovich v. DNC* (2021) rejected the challenges to Arizona's specific out-of-precinct and ballot-collection provisions.
- *Allen v. Milligan* (2023) affirmed §2 vote-dilution analysis in the Alabama map dispute (not the erroneous case label “Merrill v. Milligan” as a final merits holding).
- *Husted v. A. Philip Randolph Institute* (2018) permitted Ohio's specific NVRA-compliant notice-based process, not arbitrary removal merely for nonvoting.
- *Moore v. Harper* (2023) rejected the strongest version of the independent-state-legislature theory while preserving a federal review role.
- **Milwaukee April 2020:** a cited study estimates an approximately 10.2 percentage-point **poll-closure component** for Black voters and another approximately 5.7-point pandemic-related component; do not attribute the full ~15.9 pp to closures.
- **2019 poll-site audit:** Leadership Conference documented 750 Texas and 214 Georgia *net closures or fewer sites in its studied time period*; do not label these current 2026 counts or automatically infer discriminatory intent.
- **2020 felony disenfranchisement:** Sentencing Project estimated ~5.17m people, and 6.2% of Black voting-age adults versus 1.7% non-Black; display explicit 2020 vintage, not 2026 present.
- **2020 participation gap:** Brennan estimate of 9.3 million additional voters if voters of color participated at white turnout rates is a statistical counterfactual, not verified ballots suppressed or an outcome prediction.
- *North Carolina Holmes v. Moore* and *Harper v. Hall* must have their subsequent state-court reversal and live legal status checked before any current-law display.
- **DO NOT INGEST AS FACT:** original report's claim that the Georgia 2022 attorney-general race was a “rigged outcome,” unsupported intent attributions, asserted party-driven motivation for the Milwaukee pandemic consolidations, and its erroneous account of `Veasey` or Wisconsin ID-law disposition. Also do not equate all NVRA maintenance with illegal purges or infer fraud absence from a single audit.

## Primary and high-quality discovery sources
- [NCSL state voter-ID rules](https://www.ncsl.org/elections-and-campaigns/voter-id) — comparative entry point; verify against enacted code and election authority.
- [U.S. Election Assistance Commission EAVS](https://www.eac.gov/research-and-data/studies-and-reports) — administration, registration and ballots.
- [U.S. Census voting and registration](https://www.census.gov/topics/public-sector/voting.html) and [ACS CVAP](https://www.census.gov/programs-surveys/decennial-census/about/voting-rights/cvap.html) — denominator context.
- [DOJ Voting Rights](https://www.justice.gov/crt/voting-section) — federal cases/enforcement.
- [Supreme Court opinions](https://www.supremecourt.gov/opinions/opinions.aspx) and [CourtListener](https://www.courtlistener.com/) — decisions and proceedings, with official PDF preferred.
- [Brennan Center racial turnout analysis](https://www.brennancenter.org/our-work/research-reports/growing-racial-disparities-voter-turnout-2008-2022) — published statistical study, not an official voter census.
- [Leadership Conference polling-place report](https://civilrights.org/democracy-diverted/) — historical studied jurisdictions, not a live inventory.
- [Sentencing Project 2020 analysis](https://www.sentencingproject.org/reports/locked-out-2020-estimates-of-people-denied-voting-rights-due-to-a-felony-conviction/) — historical estimate.
- [Brennan Center Rucho synopsis](https://www.brennancenter.org/our-work/court-cases/rucho-v-common-cause) — secondary case account.

## Completion criteria
Not complete until every state and DC has a dated official-law source per mechanism; source snapshots and effective versions are validated; elections data denominators reconciled; polling sites and case statuses cover stated cycles; analytics are independently tested; license gate cleared; deployed frontend reads new versioned feed; production smoke checks pass. **Current status: integration specification and carefully qualified research seed only. No comprehensive state ingest, live law verification, causal outcome estimation or frontend deployment has been performed by this document.**
