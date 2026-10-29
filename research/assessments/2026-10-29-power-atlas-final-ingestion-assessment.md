# Power Atlas — ingestion and evidence readiness assessment

**Assessment date:** 2026-10-29 (UTC)  
**Repository:** [jbmeadows26/Power-Atlas](https://github.com/jbmeadows26/Power-Atlas)  
**Delivery target:** Complete broad ingestion by 2026-10-30 / before 2026-10-31, without paid services  
**Assessment disposition:** **NEEDS REVISION for nationwide completeness, causal accountability claims, and current production delivery.** The GitHub data pipeline and public-source research prototype are functioning within a limited, source-indexed scope.

## 1. What was independently checked

This review interrogated the connected GitHub repository, persisted source outputs, [machine-readable coverage](../../data/coverage.json), [ingestion health](../../data/health/ingestion-status.json), [2024 House source-key audit](../../data/health/house-2024-audit.json), state legislation records, recorded vote metadata, GitHub Actions run/job results, and Vercel's active production deployment. Source-coverage counts are **not** exhaustive-research completeness rates. The latest compact validation checks reviewed at the time of assessment succeeded; individual earlier jobs were mixed due to source restrictions, stale concurrent commits, and deployment settings.

Record counts below are dataset-specific grain counts and must **never** be summed into a count of unique people, unique events, verified allegations, or causes of redistricting.

## 2. Persisted coverage snapshot

| Domain | Persisted results | Assessment / limiting condition |
| --- | ---: | --- |
| Congressional office identities | 539 | CC0 registry; Bioguide with 627 FEC ID crosswalk edges; official current-service cross-check needed |
| State legislative office identities | 7,416 | CC0 roster for 52 jurisdictions including D.C./Puerto Rico; identities are not proven map-voters |
| State executive office identities | 170 | Includes 52 governor records; no inference of map approval |
| Documented redistricting/elections committees | 62 | 16 direct-title redistricting/reapportionment, 46 broader elections; 706 membership edges |
| Article III federal judge appointment rows | 4,777 | FJC index; not a judge ideology or conduct score |
| Selected Supreme Court redistricting dispositions | 9 | Selected official-source case records; not all federal/state litigation |
| DOJ / other core research source-indexed rows | 62 total | Mixed case/source records; not 62 verified unique lawsuits |
| Official FEC candidate-to-committee links | 1,269 | Registration/affiliation, **not** payments |
| FEC committee-master entries | 673 | Official public committee identities |
| FEC committee financial totals | 2 | Minimal sample; **not** comprehensive finance coverage |
| FEC intercommittee payment records | 0 | Missing collection, **not** verified zero money movement |
| FEC recipient aggregate records | 0 | Selected queries returned none, not proof of no spending |
| Senate lobbying issue-search rows | 56 | Source access intermittently HTTP 429; not a national lobbying census |
| Historical House district-year results | 3,461 | Distinct district-year observations, 2010–2024 |
| House state-year totals | 402 | Eight election years, different legislative boundaries and election conditions |
| Conservative descriptive seat-versus-vote state-years | 263 comparable of 402 | Only after indexed two-party contestant checks; not map-causal or partisan-bias scores |
| 2024 House key reconciliation | 436 accounted of 436 expected | 434 records with derived vote totals, 2 official unopposed-status-only; does **not** validate each vote total |
| Congressional geography editions | 2 | Generalized Census 116th and 119th Congress district polygons; no legal boundary history |
| Federal legislative search candidates | 34 | 14 direct redistricting title matches; secondary search, not bill enactment census |
| State legislative search candidates | 472 | 126 redistricting-specific title matches; **346 other keyword matches are unverified** |
| State legislative keyword searches | 49 of 51 jurisdictions first page | 2 first-page jurisdictions pending, **zero full-jurisdiction sweeps**; indexed bills appear in 45 jurisdictions |
| State recorded bill vote records | 15 | 14 lack reported/verifiable numeric tallies, 1 secondary positive tally; **zero officially verified tallies** |
| Primary official state-bill spot checks | 4 | Four identified records only; do not extrapolate to all 472 |
| Total indexed graph edges | 2,625 | 627 roster/FEC identity links, 1,269 FEC registration links, 706 committee memberships, 8 source-reported federal sponsorships, 15 third-party state bill/vote associations |

**Graph semantics:** An edge means that a specifically defined relationship was observed in a cited source. No edge establishes improper influence, legal culpability, donor intent, actual vote choice, campaign funding transfer, map authorship, or judicial partisan decisionmaking without separate evidence.

Source snapshots: [coverage.json](../../data/coverage.json), [House audit](../../data/health/house-2024-audit.json), [state bills](../../data/legislation/state-redistricting-bills.json), [state votes](../../data/legislation/state-redistricting-votes.json), [official bill spot checks](../../data/legislation/official-state-bill-spotchecks.json).

## 3. Critical gaps, severity, and precise meaning

### P0 — Public product release is behind GitHub source

The Vercel **production alias** `https://power-atlas-research.vercel.app/` was verified to resolve to a READY deployment built from commit `cf5c8442019c988aff756ffe85b5baba707fc28f`, **not** the latest repository commit. The API refused an attempted fresh production deployment with **HTTP 402 / api-deployments-free-per-day** after exceeding 100 free deployments in the daily window. GitHub Pages automatic creation also failed with **"Resource not accessible by integration"**, because GitHub Actions' repository token cannot create the Pages site. The Pages automatic trigger has been disabled to prevent repeated failed jobs. **Never describe new frontend tabs committed to GitHub as already verified in production.**

**Recovery:** After the daily free allowance resets, deploy the latest validated main branch once, inspect its ready status/commit SHA, and load the served frontend. Alternatively, a repository administrator can enable **Settings → Pages → Build and deployment → Source: GitHub Actions**, after which the prepared Pages workflow can be run manually. Do not upgrade, circumvent limits or rely on unverified preview URLs.

### P0 — The accountability / causality graph is still underpowered

The current graph captures **institutional affiliations**, not the actual decision chain from donor/lobbyist/private adviser → legislator/commission → hearings/amendments/votes → governor enactment → adopted map → litigation → court disposition and voter impact. No finding about a particular person's culpability, election manipulation or unlawful motive is warranted from these graph edges alone.

**Recovery:** Add provenance-aware, dated decision/event entities and distinct edge types for bill sponsorship, committee vote, roll-call vote, enacted law, map approval, veto/signature, legal challenge, injunction, judgment, appellate reversal, donor transfer, and verified lobbying contact. Require original records, a relevant date, jurisdiction, uncertainty/review status and source citation for each.

### P0 — State campaign money and actual roll calls largely absent

State campaign-finance transactions and lobbyist/private individual funding chains are not collected nationally. The 2 FEC totals and 0 payment rows are insufficient to conclude anything about money flow. State recorded vote metadata is only 15 rows and **0 vote tallies are primary-source confirmed**. A login-protected state legislative bulk archive is not a permissible source without granted access; direct Senate.gov CI XML was HTTP 403 and one House Clerk URL probe returned 404. No source restrictions were bypassed.

**Recovery:** Start with bounded, official-source finance exports (California Secretary of State and NJ ELEC are documented as probes), carefully exclude private addresses/donor-level sensitive fields, and collect actual roll calls from accessible official state archives. Keep search/index records separate from verified tally facts.

### P1 — Incomplete legislative, case, judicial and election coverage

- State bills: 49/51 first-page jurisdictions sampled, 2 pending, 0 full pagination sweeps; 346/472 potential off-topic keyword hits. Default app view should show 126 title-specific candidates first; broader matches should require opt-in and be clearly labeled.
- Court outcomes: 9 selected Supreme Court records do not replace nationwide district/circuit/state court dispositions, state supreme court panels, court selection systems or case-level status history.
- Electoral proof: 2024 House district keys are accounted for, but 51 state election-canvass authority reconciliations are pending, historical official returns are incomplete, and the 116th/119th generalized maps alone cannot establish gerrymandering.
- Historical state legislative district geometries, adopted map authorship, map dates, public hearing evidence and commission roles are not comprehensively ingested.
- Corporate/political consultancy ties, PAC transactions, independent expenditures, lobbying engagement and disclosed private actors cannot yet be connected into a defensible nationwide power map.

### P1 — Search selection, data quality and interpretation

A title keyword match is a **candidate** for examination, not proof of a redistricting bill. Broad search produced an unrelated D.C. bill in the 346 weaker-match bucket. With only 4 primary official bill spot checks, no audited precision estimate should be invented for all 472 records. Represent keyword hits, official-source verified bill facts and judicial holdings as separate confidence levels.

The 263 comparable House seat-vote state-years are descriptively filtered, not audited for complete official general-election totals in every year. Florida and Oklahoma 2024 are correctly marked incomparable due to official unopposed candidates lacking general-election vote totals. The descriptive seat-minus-vote measure is **not** a quantitative estimate of partisan intent, efficiency gap, partisan symmetry or legally actionable map discrimination.

### P2 — Licensing / refresh

Store only compact records, identifiers, source links and attribution; do not redistribute full third-party documents. The federal CC0 registries, FEC, DOJ, FJC, Census and mixed-license state-bill sources require **per-source** licensing and redistribution review. Source-indexed historical rosters can be stale; a publication timestamp is not a guarantee of current office status. Only state-specific official sources can confirm final enacted bill status, statewide election certification or individual legislative votes.

## 4. Completed repairs in this assessment window

1. Persisted separate title-relevance labels and conservative official-unopposed election exclusions.
2. Verified the derived House descriptive state-year export and clarified that it is not a gerrymandering score.
3. Built the federal bill sponsor-relationship graph, preserving secondary-source/primary-review labels.
4. Revised the mobile state-bills filter to default to **title-specific redistricting matches**; weaker keyword results are an explicit alternate view. This is committed in GitHub, not yet production-verified.
5. After a second no-cost GitHub Pages enablement attempt failed for integration permissions, stopped automatic Pages build retries pending authorized administrator setup.
6. Confirmed recent compact evidence CI validations and separate GitHub data publication success; Vercel remains a distinct deployment blocker.

## 5. Acceptance gates before claiming full nationwide ingestion

**Not satisfied as of October 29, 2026:**

- All 50 states plus D.C. have documented primary-source map/law version histories and full legislative vote records for relevant redistricting actions.
- Each salient legal challenge has a court/docket, claims, filing dates, status, primary filings and verified disposition with appeal history.
- Financial reporting is sufficient to resolve donor, committee, independent spending, lobbying and consulting pathways without guessing identity or causation.
- Every considered political actor is connected by a date-scoped, source-backed action/event rather than office-holding alone.
- State election totals reconcile to certified official returns; historical map shapefiles are tied to appropriate election cycles and geography.
- Frontend production serves the validated latest GitHub commit, and visual/manual smoke tests verify major tabs and citation links.
- Evidence-licensing constraints, per-source freshness, duplicate resolution and low-confidence uncertainty remain visible to end users.

**Supported current claim:** Power Atlas is a working, growing **source-indexed investigative research prototype** with validated compact datasets, scoped relationships, free recurring ingestion checks and explicit incompleteness labels.

**Unsupported current claim:** Power Atlas has fully ingested all sources nationwide, identified all influential individuals, or established who caused the nation's gerrymandering.

## 6. Deadline-prioritized next actions

1. **Delivery:** After the free Vercel daily deployment limit resets, perform one production deployment and verify commit SHA, mobile tab functionality and direct evidence links. GitHub Pages remains optional but requires admin configuration.
2. **Evidence:** Convert the 126 title-matched state bills plus four official spot checks into verified legislative event histories (adoption, committee votes, passage, veto/signature) from their cited official sources.
3. **Completeness:** Finish the two pending state first-page bill queries, then paginate each jurisdiction with stable checkpoint IDs and coverage flags; never describe mere API availability as complete legislative coverage.
4. **Money:** Probe/ingest bounded official CA and NJ committee-level finance records; preserve a clear zero-vs-missing distinction, and audit each monetary relationship.
5. **Judiciary:** Build case/docket/event histories for lower federal/state courts and state judicial selection/appointments.
6. **Elections and maps:** Source state-certified canvasses and additional valid map editions, then evaluate competing explanations and carefully define metrics before drawing causal conclusions.
7. **Quality:** Keep automated freshness, uniqueness, relationship provenance, per-source licensing, high-risk value consistency, and frontend feed/graph parity checks. Prioritize any CI failure showing a live publication defect over stale workflow-failure noise.

**Cost policy:** No new paid product, no forced deployment retries against an unchanged 402 limit, no bypass of 403/429/access restrictions, and no private individual contact details. No unverified misconduct or partisan assertions.

---

_This is an evidence-coverage and delivery-readiness assessment. It is not a comprehensive political-science finding, legal opinion, or proof of wrongdoing. The live, versioned dataset and original cited source always control over this dated snapshot._
