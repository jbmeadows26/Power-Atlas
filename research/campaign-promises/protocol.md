# Campaign pledge attrition and electoral short-termism — preregistration-ready protocol
Version: 0.1 (2026-10-29) · Status: research protocol, NOT empirical findings

## Scope and inferential targets

The objective is to distinguish (A) promise enactment, (B) process/effort, (C) implementation and durability, and (D) causal responsibility. These are separate, noninterchangeable constructs. The pilot is the US federal 2020 campaign evaluated through the administration ending 2025-01-20. The comparative expansion is US, UK, Canada, Germany, and Portugal, 2000–2025 where matched coverage is available. Australia is a *candidate extension*, not part of the cited 2017 Comparative Party Pledges Project 12-country sample. The period 2024–2026 is right-censored for promises not yet due. No zeroes should be silently generated for absent data.

**Population:** explicit, testable public election pledges by parties or candidates from timestamped *pre-election* primary campaign materials. Distinguish party pledge from candidate pledge; government coalition agreements are post-election actions, not campaign pledges. **Unit:** an atomic pledge×maker×election with multiple actions, obstacles, owners, policy dates and independent evidence. Split multiple concrete commitments into atomic records, retaining shared parent pledge id. Do not count repeated campaign statements twice. Define denominator before scoring and record all exclusions.

## Questions and falsifiable hypotheses

RQ1: What fraction of matured governing-party promises achieve their specified outcome by the declared deadline or fixed term end? Why does fulfillment vary? RQ2: How do enacted appropriations, actual expenditures, policy starts and policy announcements differ by months to election? RQ3: Which policies persist after a change in government?

- H1: Conditional on specificity and policy area, a single-party government with effective agenda control has a higher enactment hazard than a coalition partner with the same pledged policy.
- H2: At short electoral horizons, the share of visible targeted transfers rises relative to hard-to-credit spending, with heterogeneous effects by media exposure and electoral competitiveness.
- H3a: Pre-election public capital investment falls where administrative implementation capacity is weak; H3b: pre-election *announced* infrastructure rises even if actual capital payments do not.
- H4: Exogenous shocks predict renegotiation/partial delivery; their effects vary by debt headroom and legislative control.
- H5: Exposure to independent campaign-platform costing is associated with fewer unsupported numerical promises; causal claims require exogenous variation.
- H6: Voter knowledge moderates any relationship between pledge performance and subsequent electoral support. Do not interpret a raw fulfillment/vote association causally.

## Pledge identification and completion

Eligibility requires a future, observable policy commitment by an attributable party/candidate made during the campaign. Record source language as licensed/permissioned snippet, otherwise keep a brief paraphrase and an exact source URI and passage location. Record objective, affected population, amount, temporal deadline, jurisdiction, institution necessary, enforceability, and conditional clauses.

Outcome codes: `fully_enacted`, `partially_enacted`, `attempted_not_enacted`, `unattempted`, `unresolved`. `unresolved` is NOT a failure. For each pledge record binary and categorical dimensions separately: formal attempt, legislative floor vote, statute signed, regulation final, executive order, budget appropriation, payment, implementation reach, repeal, litigation, explicit deadline, actual term end and evidence strength. A narrowed action **does not automatically satisfy** a specific nationwide target. `attempted_not_enacted` indicates observable formal action without meeting target; it does NOT establish that an institution was solely responsible. Classify `unattempted` only after a complete, documented source search. Opponents' policy positions and committee inactivity are not by themselves proof of obstruction. Later rescissions measure persistence separately from term-end delivery.

**Attribution:** use `executive_discretion`, `legislative_rejection`, `coalition_compromise`, `court_constraint`, `subnational_competence`, `external_shock`, `administrative_delay`, `mixed_or_unresolved`. Allow multiple nonexclusive factors with event-level citations. Distinguish what occurred, inferred mechanism, and normative bad-faith allegation; never code motive without direct evidence. Contemporaneous evidence outranks retrospective political claims.

## Sampling plan

1. US baseline: all eligible and pre-declared atomic commitments from the 2020 Democratic national platform and the 2020 major candidate policy release corpus, with candidates, publication cut-off and duplication hierarchy frozen beforehand. Avoid using PolitiFact's editorially selected 99 as a representative denominator. Use that tracker as an external reliability/face-validity benchmark only; its labels do not directly map to our five statuses.
2. UK/Canada/Germany/Portugal: specify the winning party (and relevant coalition partners) for each election and all extant machine-readable party manifesto documents. Record missing documents and unsupported languages explicitly. Use the Comparative Party Pledges Project only with actual authorized access; the scholarly paper's 20k+ pledge observation count is not an ingestible dataset license.
3. Stratified two-coder validation: 10% of each country's pledges, no fewer than 100 per country where available; oversample ambiguous/blocked/partial cases and report both stratified and reweighted agreement. For small strata, double-code all. Require Krippendorff's alpha or weighted Cohen's kappa, raw agreement and adjudication log; target >=0.80 for key outcomes as a quality goal, not a substitute for review.
4. Freeze coding guide, election cohort, time windows, data versions and primary specifications before inspecting outcomes. Separate exploratory case studies and confirmatory estimates.

## Election-time budget and policy measures

Unit country×quarter where harmonized actuals are available; annual-only budget series cannot establish within-year election-quarter effects. `months_to_election` is measured using the election date **known at the time**, not the ex-post eventual date when election timing is endogenous; record announcement and dissolution dates for parliamentary systems. Main outcomes: realized general-government gross fixed capital formation / total primary outlays; visible targeted transfers / primary outlays when directly classified; R&D and human capital investment as separately reported dimensions. Also track announced commitments, authorized appropriations, contractual obligations and realized payments as distinct event types. Do not classify all transfers as short-term or all investment as high-ROI: horizon and visibility are independent, coder-validated dimensions. For each law, record expected *benefit-realization horizon* (0–1, 2–5, 6–10, >10 years, unknown), target population, salience and credible independent cost/impact appraisal. Uncertain long-run ROI remains unknown, not zero.

**Primary sources:** [OMB historical tables](https://www.whitehouse.gov/omb/information-resources/budget/historical-tables/) investment table series 9.1–9.9 and outlays; [CBO historical budget data](https://www.cbo.gov/data); [GovInfo bulk laws and bill status](https://www.govinfo.gov/bulkdata/); [Manifesto Project versioned corpus](https://manifesto-project.wzb.eu/information/documents/corpus) (API key and daily quota); [ParlGov](https://www.parlgov.org/data-info/) cabinet/election series; IMF GFS and OECD/Eurostat for internationally comparable government accounts after verifying coverage. Track general vs central government, budget vs accrual, fiscal vs calendar year, revisions, inflation, spending double counts and country-specific accounting breakpoints. A ratio built from dissimilar definitions is INVALID.

## Identification and estimands

Pledge baseline: cumulative incidence of *enactment* by 48 months/term end, with censoring, competing risks for government turnover, and clustering at party-election level. Logistic/multinomial models are descriptive secondary specifications; use an event-history model for timed implementation, competing-risk sensitivity and survival plots. Within-party and coalition-status comparisons must control pre-election salience, policy specificity and severity of shocks; do not assume coalition assignment is random.

Budget baseline: within-country panel with country and time fixed effects, time-to-election indicators, election-system strata and preregistered shocks (inflation, GDP gap, unemployment, debt ratio, pandemic/war, disasters). Report standard errors clustered at country and/or election with caution for few countries (wild bootstrap or design-based alternatives). Compare quarterly and annual aggregations separately. Plot leads/lags; reject parallel trends if pre-trends fail. Controls measured after treatment may be mediators; distinguish necessary pre-treatment controls from post-treatment outcomes.

**Causal identification:** pre-scheduled US executive elections as one clock (presidential and midterm separately); unexpected parliamentary dissolutions are not exchangeable with scheduled elections. Exploit plausibly exogenous election timing changes only when constitutional rules and historical setting support the assumption, testing balance and anticipation. Audit candidate quasi-experiments (close elections, redistricting shocks, fixed-term rule adoption) rather than promising they are valid. Mechanism comparison: publicity/announcements vs obligations vs realized payments; opportunism predicts targeted visible transfers/announcements, administration-capacity predicts delayed capital implementation and procedural bottlenecks. Placebo election dates, nonpolitical fiscal categories, event window exclusions and sectoral comparison are mandatory robustness checks.

## Process tracing: three sectors

- Energy/grid: campaigning commitments → bill introduction → permitting/appropriation → obligations → commissioned assets; separate long permitting from political abandonment.
- Pension/social insurance: numerical benefit or retirement-age pledges → actuarial costing → coalition negotiations → statutory amendments → coverage.
- Preventive health/public health: proposed funding/coverage → budget authorization → implementing regulations → population reach over 5–10 years.

For each case keep a chronology of dated primary documents and competing mechanism tests: hoop evidence (necessary but insufficient), smoking-gun evidence (discriminatory where available), disconfirming evidence. Label motive as unproved absent direct credible evidence. Use within-sector mismatched government comparisons only as illustrative if no causal design is available.

## Reproducibility, safety and licensing

Immutable source URL, source organization, retrieval timestamp, original publication timestamp, source revision, content SHA-256 when lawfully archived, claim passage locator, language, access tier, license, link status, source confidence and code version for each event. Version transformations and raw-to-curated exclusion decisions. Third-party trackers may be linked and *compared*; do not bulk scrape or republish their proprietary text without permission. Manifesto Project requires an API key and has daily quotas. Do not leak tokens to public GitHub files or logs. No invented counts, sample sizes, categorical blame or guilt by association. Public policy positions do not by themselves establish misconduct.

## Release gates

Gate A: source access, licensing, primary text date, denominator, and uniqueness validated. Gate B: independent action verification, at least two coders/adjudication, confidence and contested cases. Gate C: consistent fiscal denominators and dates, matching accounting standards, audit of fiscal revisions. Gate D: registered models, diagnostics, alternative explanations, and uncertainty intervals. Gate E: public-facing records have clickable evidence links, transparent corrections/versioning and data coverage warning. A successful CI run checks format; it cannot certify factual completeness.

## Source and theory anchors

- Thomson et al. 2017, *AJPS*, doi:10.1111/ajps.12313 — comparative pledge fulfillment, government power sharing.
- Drazen & Eslava 2005, NBER w11085, https://www.nber.org/papers/w11085 — electoral shifts in expenditure composition.
- Pierskalla & Sacks 2018, *Journal of Politics*, doi:10.1086/694547 — Indonesian election timing and capital spending capacity mechanism.
- Party pledge materials: https://www.presidency.ucsb.edu/documents/2020-democratic-party-platform and https://www.presidency.ucsb.edu/documents/biden-campaign-press-release-fact-sheet-joe-bidens-plan-build-back-better-for-american
- Primary implementation: https://2021-2025.state.gov/the-united-states-officially-rejoins-the-paris-agreement/ and https://www.govinfo.gov/content/pkg/DCPD-202100345/html/DCPD-202100345.htm
- Independent *editorially selected* verification, not full electorate sample: https://www.politifact.com/truth-o-meter/promises/biden-promise-tracker/
