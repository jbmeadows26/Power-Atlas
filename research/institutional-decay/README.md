# Institutional Decay — evidence baseline and empirical protocol

## Final assessment (2026-10-29)

**The evidence review is closed, but the interaction/causal hypothesis is not established.** Read the [final scientific assessment](FINAL-ASSESSMENT-2026-10-29.md) for the verdict, full evidence matrix, 2023–2025 institutional trend and cross-country correlation analyses, implementation-gap interpretation, country examples, policy decisions and explicit research limits. The claim scope is a **source-backed descriptive/literature assessment**, not a causal demonstration or full national performance index.


**Status:** Initial primary-source aggregate extracts verified and persisted on 2026-10-29. **No causal model or survey experiment has been executed.** This topic is a separate research track from Power Atlas's redistricting coverage. The extract is in [evidence-v1.json](../../data/institutional-decay/evidence-v1.json); it is **not** yet part of the redistricting `data/app-feed.json` and must not be represented as integrated into the production frontend.

## Question and neutral framing

How do **administrative burden** and **perceived elite impunity** separately and jointly relate to citizens' trust in (i) national elected government, (ii) local government and civil services, and (iii) democratic procedures? Do sanctions and demonstrable service improvements alter that relationship? Test against the counterhypothesis that accountability and service interactions preserve or restore trust despite scandals.

Avoid presuming a universal decline. The OECD 2025 survey (reported June 2026) found 40% high/moderately high trust in national government and 43% low/no trust, with average trust stabilizing relative to the previous wave. The same survey reports 68% of recent administrative-service users satisfied and only 31% believing people like them have a say in government. These are DIFFERENT questions and denominators.

## Source coverage actually in the baseline

| Source | Published evidence | Data limitations |
| --- | --- | --- |
| [OECD 2026 Trust Survey](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/executive-summary_4319a992.html) | Trust, voice, satisfaction and partisanship | Cross-national published aggregates; country microdata must be requested and may be restricted |
| [ONS 2022 UK Trust Survey](https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/bulletins/trustingovernmentuk/2022) | UK confidence in government, civil service and NHS | 2022 survey; differs from NHS performance satisfaction |
| [NAO passport investigation](https://www.nao.org.uk/reports/investigation-into-the-performance-of-hm-passport-office/) | UK 2022 waiting-time volumes and service conditions | Period-specific; cannot attribute cause to a political scandal |
| [Commons Privileges Committee](https://publications.parliament.uk/pa/cm5803/cmselect/cmprivi/564/summary.html) | Formal Johnson parliamentary misconduct findings and recommended sanction | Committee finding is not a criminal judgment; recommendation is not an implemented suspension |
| [GAO-26-108116](https://www.gao.gov/products/gao-26-108116) | US IRS FY2019/FY2024/FY2025 backlog and paper-return processing time | Multiple service operations; do not compare paper returns with correspondence as a single metric |
| [WJP Rule of Law Index 2025](https://worldjusticeproject.org/news/wjp-rule-law-index-2025-global-press-release) | Share of 143 assessed countries/jurisdictions with score deterioration | Expert/public opinion-based index; not a trust or administrative processing measure |
| [V-Dem v16](https://www.v-dem.net/data/dataset-archive/) | Candidate country-year checks and democracy data | **Listed only**, not downloaded or merged; check source-level license and uncertainty |
| [QoG](https://datafinder.qog.gu.se/downloads) | Candidate country-year governance data | **Listed only**, not downloaded or merged; harmonize versions/definitions before statistical use |

Each persisted observation has population, geography, period, metric, unit, source URL, evidence status and caveat. No cross-source aggregate has been computed. Values marked approximate are preserved as approximate.

## Specific hypotheses, including falsification criteria

- **H1 (administrative burden):** Individual adverse interactions (long elapsed waiting, repeated filing, erroneous decisions, denied appeals) predict reduced trust in the **serving institution** more strongly than national-government trust. **Null:** no relationship or positive relationships after covariate adjustment.
- **H2 (elite impunity):** Perceived absence of appropriately justified sanction after an official finding predicts lower trust in national government/legislature. **Null:** no distinctive trust effect after party/ideology/media exposure controls.
- **H3 (interaction):** The trust decrement under service failure is greater when **impunity is salient** than when oversight is effective. **Null:** additive, no effect, or trust resilient in either exposure.
- **H4 (differential outcome):** Political voice is more closely associated with national-government trust than service satisfaction, which is more closely associated with civil-service/local-government trust.
- **H5 (repair):** Independently validated improvements in enforcement and end-to-end delivery improve trust. **Null:** improvements are not noticed or only move service satisfaction, not legitimacy.
- **H6 (feedback):** Lower trust contributes to lower benefit take-up, complaint usage, compliance or oversight engagement; these outcomes can in turn shift institutional performance. **Null:** no behavioral mechanism.

Do not claim H3/H6 until an appropriately identified test is actually conducted.

## Measurable constructs

- **Elite misconduct:** separate allegation → investigation → substantiated finding → sanctions/referrals → appeal → final disposition. Compare sanctions for legally comparable conduct, with independent severity coding and right-to-respond. Higher investigation counts may mean improved oversight.
- **Impunity:** measure failure to impose a normally applicable sanction **after** substantiation with due-process-adjusted timing and exceptions; do not infer guilt from trade timing, wealth, political connections, dropped allegations, unproven or pending proceedings.
- **Administrative burden:** learning costs, compliance costs, psychological costs. Where objective records exist, measure end-to-end elapsed days, repeat contacts, formal error rates, reversals, complaints and appeal resolution. Government service-level attainment is not interchangeable with citizen experience.
- **Trust outcomes:** separate legislature, national executive, local government, civil service, judiciary, underlying democratic norms, actual participation and service take-up.
- **Confounders:** partisanship/incumbency, fiscal stress, unemployment, inflation, demographics, service usage, exposure to corruption reports, press conditions, political agency, crisis shocks and baseline trust.
- **Measurement:** preserve response wording, survey waves, sample/weighting, temporal granularity and uncertainty. Observations based on different populations must not be used as a shared denominator or differenced as if they were identical.

## Pre-analysis execution plan

1. **Data source licensing and availability.** Record version, permission, rate limits, public-use conditions, geographic coverage, source timestamp, response wording and error bands. Apply the existing repository's source-licensing checks before ingestion. OECD public aggregate Stat.Links may be accessible; OECD microdata require application for non-commercial academic/policy research and are not to be bulk copied into this public repo without permission.
2. **Harmonization.** Create a data dictionary and country-year/wave keys, retaining all missing values. Do not manufacture annual trust values by forward-filling or interpolating sparse survey waves. Check country boundaries, survey question changes, V-Dem measurement uncertainty and inconsistent meanings of 'corruption.'
3. **Objective service indicators.** Collect UK passports/NHS/appeals and US IRS/VA/benefits administrative records with the precise agency-level denominator, timing, reference standard, acquisition date and year.
4. **Case chronology.** For UK 2021–2024, record disclosure, misconduct finding, agency outcomes and trust survey fieldwork dates separately. For US, use substantiated ethics dispositions (not mere STOCK Act transactions) alongside administrative records.
5. **Observational models.** Country and year fixed effects, preregistered institution-specific trust measures, lagged predictors, controls, clustered errors, country exclusions, measurement harmonization and sensitivity analysis. Avoid causal language without credible identification.
6. **Event studies or quasi-experiments.** Only where timing, exogenous exposure and suitable comparison groups permit credible pretrend and spillover checks. Evaluate negative-control outcomes and unexposed populations.
7. **2×2 randomized survey.** Randomly vary effective service vs high service burden and justified sanction vs unjustified non-sanction, otherwise identical scenarios. Pre-register primary trust response, manipulation checks, ethical protections and power analysis. Secondary outcomes include perceived legitimacy, willingness to seek services and support for democratic checks.
8. **Policy trials.** Compare independent enforcement with publishing results alone; compare removal of compliance steps with informational messages alone; measure actual completion and appeal restoration, not only applications.
9. **Adversarial audit.** Search for counterexamples: scandals with resilient trust, high satisfaction with low national-government trust, good governance with partisan distrust, independent institutions that preserve legitimacy. Reviewer must be able to reproduce all final quantitative claims.
10. **Platform integration gate.** Only surface a dedicated institutional-decay domain feed after licensing, tests, design acceptance and source-level provenance pass. Do not mix unharmonized values into a composite index or accuse people of misconduct by association.

## Literature that directly informs the missing causal links

- Halling & Bækgaard (2023), *Administrative Burden in Citizen-State Interactions: A Systematic Literature Review*, `Journal of Public Administration Research and Theory`. Review of 119 articles/working papers; evidence of consequential, constructed and distributive burdens, with democracy-behavior links still in need of testing. [Paper](https://consensus.app/papers/administrative-burden-in-citizenstate-interactions-a-halling-bækgaard/93f84b5d817658db97302902dee19543/).
- Bell, Wright & Oh (2024), *Does Administrative Burden Create Racialized Policy Feedback?*, `JPART`. Observational study of 2,250 US benefit applicants; loss of access associated with reduced trust, particularly for racially minoritized clients. Not randomized exposure. [Paper](https://consensus.app/papers/does-administrative-burden-create-racialized-policy-bell-wright/26d82b6a7ad45bc2b23b7bca2d12c170/).
- Bendtsen (2026), *Increasing Take-Up of Social Benefits: A Meta-Analysis of Field Experiments*, `Journal of Policy Analysis and Management`. Synthesis of 51 field experiments and 187 effect sizes; final benefit receipt and applications are distinct outcomes. [Paper](https://consensus.app/papers/increasing-take‐up-of-social-benefits-a-meta‐analysis-of-bendtsen/30acbc794c1e5379a6c5ec78e8f59c02/).

**Research ethics:** No private contact details or identifying information of uncharged private individuals; do not infer corruption from social ties. Report unknown as unknown. Do not equate accusation, parliamentary finding, civil penalty, and criminal conviction. Distinguish direct quotes, documented numbers, estimates and hypotheses. 

## Newly validated empirical datasets (2026-10-29)

- [OECD country and institutional trust 2023–2025](../../data/institutional-decay/trust-country-waves-2023-2025.json): 39 countries with some observations, 33 OECD respondents in 2025 and 28 paired national-government trust estimates. Other trust series (civil service, local government, parliament, parties and courts) are kept separate.
- [OECD integrity implementation extracts](../../data/institutional-decay/integrity-implementation-2025.json): assessed **regulation versus practice** criteria, three OECD averages and curated country examples; not an inferred corruption or impunity probability.
- [Research findings and exact denominator checks](empirical-update-2026-10-29.md) documents sample limitations, contradictory institutional trust directions and source licensing.
- Run `python scripts/analyze_institutional_decay.py` for deterministic descriptive analysis; `tests/test_institutional_decay_country_panel.py` and `tests/test_institutional_decay_integrity.py` enforce sample and causal-language guardrails.

**Important:** These are descriptive published survey percentages, not microdata and not a completed causal study. The country pairs exclude the missing 2023 government trust cell for Colombia. Only 28 national-government trust item pairs are available even though 29 OECD countries participated in both waves. The repository's production redistricting feed is unchanged.
