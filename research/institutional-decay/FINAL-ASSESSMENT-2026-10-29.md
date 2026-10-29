# FINAL EVIDENCE ASSESSMENT — Institutional Decay
**Power Atlas research | Evidence cut-off: 29 October 2026 | Version 1.0**

**Research disposition: Assessment of published evidence COMPLETE; proposed dual-driver causal hypothesis NOT ESTABLISHED.**
This is a final evidence synthesis of currently sourced material—not a representation that an original randomized trial, individual-level panel, or causal cross-national analysis has been conducted.

## Executive conclusion

The literature and audited public records support two independently important mechanisms for weakening political or administrative legitimacy: (a) perceived unequal treatment and weak practical enforcement of accountability rules, and (b) administrative burden and low public-service functionality. National-government trust varies widely among countries and can move differently from trust in the professional civil service. However, no evidence assembled here validly estimates an interaction between elite impunity and bureaucratic failure, let alone proves a superadditive or exponential erosion of trust. The strongest defensible decision is to **treat the combined effect as a research hypothesis, not an established finding**. Avoid any published institutional-decay or corruption score that uses unvalidated cross-domain combinations.

### Principal findings with their evidentiary status

| ID | Claim | Determination | Evidence and interpretation |
|---|---|---|---|
| F1 | Many governments have integrity rules whose implementation lags behind formal regulation | **Supported: administrative criteria** | OECD 2026 Public Integrity Indicators: OECD members average 19 percentage-point gap across assessed areas; 35 pp conflict of interest; 44 pp civil-service discipline. Scores are assessed regulatory/practice criteria, not percentages of corrupt officials. [OECD Overview](https://www.oecd.org/en/publications/anti-corruption-and-integrity-outlook-2026_16708b78-en/full-report/component-4.html) |
| F2 | Burdens in citizen–state interactions materially affect service access and unequal treatment | **Supported, including field experiments** | 119-study review, 51 field-experiment meta-analysis, and experimental evidence from nationwide French social-benefit outreach; outcome is benefit uptake, not automatically governmental trust. [Halling & Bækgaard](https://doi.org/10.1093/jopart/muad023), [Bendtsen](https://doi.org/10.1002/pam.70085), [Castell et al.](https://doi.org/10.1257/pol.20220786) |
| F3 | Administrative burden is related to government trust | **Observational support; not general causal proof** | US survey of 2,250 means-tested benefit applicants finds benefit loss associated with lower trust, especially among racially minoritized clients. [Bell, Wright & Oh](https://doi.org/10.1093/jopart/muae004) |
| F4 | National trust has continuously declined across democracies | **Not supported / contradicted as a universal claim** | OECD trust average stabilized 2023–25. Twenty-eight observed country-pair published values yield an unweighted +0.75 pp mean, median 0, 11 increasing, 13 decreasing, 4 equal at integer precision. [OECD Trust Survey](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/drivers-of-trust-over-time-lessons-from-the-third-wave-of-the-oecd-trust-survey_440749ab.html) |
| F5 | Trust in political leaders and administrative institutions can follow different paths | **Supported descriptively** | In 2025, 23/33 OECD countries have higher civil-service than national-government trust; 25/33 higher local-government than national-government trust. UK 2023–25: government +4 pp, civil service -6 pp; Norway +9/-4. [OECD Table 1.3](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/drivers-of-trust-over-time-lessons-from-the-third-wave-of-the-oecd-trust-survey_440749ab.html) |
| F6 | Political agency and partisanship are major explanations of national-government trust | **Strong observational association; confounder** | OECD: only 31% feel political voice; trust gap 47 pp by perceived voice, 26 pp by reported support for governing parties. These are not randomized effects. [OECD Political Agency](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/socioeconomic-conditions-political-agency-and-trust_bb385ad9.html) |
| F7 | Elite impunity plus administrative burden jointly reduces trust more than the sum of separate effects | **Not established** | No adequately aligned, measured person-level or comparative causal interaction estimate. Allegations, official sanctions, service backlogs and surveys cannot simply be aggregated to produce this result. |
| F8 | Low trust causes further bureaucratic stagnation and anti-democratic behavior | **Not established here** | Feedback may occur, but plausible alternative directions and mediators remain untested. Trust in incumbents must not be equated with support for democracy. |
| F9 | Transparency by itself restores public confidence | **Not universally supported** | Transparency may promote accountability or, in environments where people expect no consequences, resignation/disengagement. [Bauhr & Grimes](https://doi.org/10.1111/gove.12033) |

## 1. Audited quantitative evidence

Source data are held in [2023–25 institutional trust country-waves](../../data/institutional-decay/trust-country-waves-2023-2025.json), with 407 reported numeric country × year × institution entries across 39 countries (33 OECD countries in the 2025 wave, five accession countries in 2025, and Czechia with 2023-only data).

**Comparability:** Only 28 OECD countries have publicly tabulated national-government trust percentages in both 2023 and 2025. Although the OECD discusses a 29-country participation cohort, one national-government question value for Colombia in 2023 is absent from the published table. We never fill it. The US did not participate in the 2025 OECD Trust Survey; it is excluded from these 2025 cross-country computations.

Our **unweighted** calculation using 28 country values rounded to whole percentage points gives:

- National-government trust mean: **40.50% in 2023**, **41.25% in 2025**; change **+0.75 pp**.
- Median country change: **0 pp**. Outcomes: **11 increases, 13 decreases, 4 integer ties**.
- Five cases in which national-government and civil-service trust move in opposite directions at rounded precision: **Canada, Luxembourg, Mexico, Norway and United Kingdom**.
- Among 33 OECD members in 2025: civil-service trust higher than national-government trust in **23**, lower in **8**, equal in **2**; local-government trust higher in **25**, lower in **5**, equal in **3**.

**New descriptive cross-country calculations, from the same OECD Table 1.3 extracted values:**

| Relationship (Pearson's r) | Observations | Result | Meaning |
|---|---:|---:|---|
| 2025 national-government vs civil-service trust | 33 countries | **+0.7391** | Higher values often coexist cross-sectionally; **no cause implied** |
| 2025 national-government vs local-government trust | 33 countries | **+0.7267** | Similarly positive descriptive association |
| 2023–25 changes: national-government vs civil-service trust | 28 countries | **+0.4901** | Different institutions' changes are substantially less tightly aligned |
| 2023–25 changes: national-government vs local-government trust | 28 countries | **+0.6925** | More aligned than civil-service changes in this sample |

A one-country-at-a-time exclusion sensitivity check for the national-government versus civil-service **change correlation** yields **r = 0.4471–0.5602**. This is a sensitivity interval, **not** a probability interval or confidence interval. Because percentages are rounded, survey samples differ by wave, country units are not random draws from all democracies and key confounders are not controlled, no statistical significance claim or individual-level inference is appropriate.

The OECD's separately reported mean for its 29-country participation cohort (40.0% in 2023 and 40.7% in 2025) is not computed using exactly these public 28 item pairs. Do not silently equate the results. [OECD official comparison](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/drivers-of-trust-over-time-lessons-from-the-third-wave-of-the-oecd-trust-survey_440749ab.html).

**Survey design limitations:** The 2025 OECD survey has 76,927 valid responses across 33 OECD member and five accession-country samples. Most countries used nonprobability quota-based panels with post-stratification weights; some used other methods, and Mexico is urban-only. Surveys are repeated cross-sections, not followed individuals. The wording adapts to national institutions, and only published rounded aggregated percentages are in this repository. Respondents' partisan alignment and perceptions may affect trust responses independently of objective service quality. [OECD Technical Annex](https://www.oecd.org/en/publications/oecd-survey-on-drivers-of-trust-in-public-institutions-2026-results_9eb63fec-en/full-report/technical-details-about-the-data-collection-and-regression-analysis_0480737a.html).

## 2. Integrity and fairness evidence

OECD's 2026 *Anti-Corruption and Integrity Outlook*, assessing 37 OECD members and 25 partners, explicitly distinguishes de jure safeguards from de facto practice. Across OECD members, the average regulatory–practice criterion gap is 19 pp overall, 35 pp in conflict-of-interest management, and 44 pp in civil-service discipline. The OECD recommends risk-based verification and credible enforcement, not simply multiplying rules.

The research extract [integrity-implementation-2025.json](../../data/institutional-decay/integrity-implementation-2025.json) contains **three OECD averages and six selected country-area records covering Poland and Slovakia**. The selected cases illustrate heterogeneity, not a representative full PII panel. Poland's reported conflict-of-interest criteria were 89% regulatory and 11% practical; Slovakia's 78% and 0%. These percentages are based on assessed criteria. They are **not** estimates of criminal offending, corruption prevalence or the proportion of officials who escaped sanction. Missing validation records can be relevant to practical scores. The current extract cannot support a cross-country integrity/trust regression.

The [OECD Data Explorer PII dataset](https://data-explorer.oecd.org/) displays broader country-level data, and [Public Integrity Indicators portal](https://oecd-public-integrity-indicators.org/indicators/) provides some publicly readable series; an appropriately licensed, complete matched PII extract is **not persisted in this repository**. A direct machine-readable fetch of the OECD SDMX source was attempted but was inaccessible with the available public fetching route at assessment time. No attempt to bypass the source's terms or protections was made.

**Accountability chain for future claims:** Report allegation, investigation, substantiated finding, sanction or remedy, appeal, and final disposition separately. More investigations may reflect greater scrutiny; the absence of a suspension may reflect resignation or appellate processes. Neither financial disclosure, a public association, nor a late report alone proves illegal enrichment or impunity.

## 3. UK and US process-tracing verdicts

### United Kingdom

- The UK House of Commons Committee of Privileges concluded in June 2023 that former Prime Minister Boris Johnson deliberately misled Parliament and committed serious contempt. He resigned his parliamentary seat before a suspension could be imposed; the committee stated that a 90-day suspension would have been recommended if he had remained an MP. **This is a formal parliamentary finding, not an absence of investigation or a criminal conviction.** [Official Committee Report](https://publications.parliament.uk/pa/cm5803/cmselect/cmprivi/564/report.html).
- HM Passport Office received about **7.2 million applications** in January–September 2022; around **360,000** took longer than 10 weeks. The NAO attributed operational difficulty to the post-pandemic demand surge, digital/paper processing and contractor capacity. [National Audit Office](https://www.nao.org.uk/reports/investigation-into-the-performance-of-hm-passport-office/).
- These contemporaneous events show the practical coexistence of political scandal and administrative strain. **They do not establish that the misconduct caused passport delays or that their coexistence produced an identifiable change in trust.**

### United States

- US GAO's March 2026 report documents an IRS correspondence backlog of about **6.3 million pieces at FY2025 end**, of which **4.1 million (65%) were overdue**; the FY2019 comparator was about **1.8 million**. Paper-return average processing in the filing season improved from **20 days in 2024 to 16 days in 2025**, even while correspondence delays persisted. These are different workflows and must not be collapsed into one service outcome. [GAO-26-108116](https://www.gao.gov/products/gao-26-108116).
- STOCK Act trading and financial-disclosure rules create an oversight research domain, but this project currently lacks an adjudicated federal congressional transaction-to-enforcement panel. **No lawful trading disclosure should be interpreted as criminal misconduct merely because a trade occurred.**
- The US and UK cases are not a matched causal comparison: timing, surveys, national context and institutional roles differ.

## 4. Literature assessment and policy evidence

- **Procedural justice (Tyler):** Fair process and legitimate authority are theoretically and empirically connected; political rhetoric must not substitute for a specific measure of perceived fairness.
- **Impartial government (Rothstein and Teorell):** Administration can function promptly yet unequally. Effectiveness and impartiality are distinct dimensions.
- **Principal–agent and collective action:** Weak oversight permits moral hazard, but when corruption is systemic, citizens may not believe any single actor can correct it.
- **Administrative burdens (Herd & Moynihan, 2025; Halling & Bækgaard, online 2023 / print 2024):** Learning, compliance and psychological costs are not equivalent to simple processing delay; they fall unevenly on people with different resources. [JEP Review](https://doi.org/10.1257/jep.20231394), [JPART systematic review](https://doi.org/10.1093/jopart/muad023).
- **Trust and unequal burden (Bell, Wright & Oh, 2024):** Observational study of US applicants (n=2,250) finds benefit loss associated with lower trust, especially among racially minoritized applicants. **Not a randomized burden-to-trust test.** [JPART](https://doi.org/10.1093/jopart/muae004).
- **Reducing burden (Bendtsen, 2026):** Meta-analysis of 51 field experiments / 187 effect sizes finds compliance assistance more effective for actual benefit receipt than information-only interventions on average. The author separately reports an expanded 66-study update; the two sample sizes must not be merged as if identical. [Published meta-analysis](https://doi.org/10.1002/pam.70085), [Author's subsequent update](https://karlemilbendtsen.github.io/takeup_update.html). A separate France experimental study finds in-person benefit-eligibility assistance improved benefit take-up, while an online information simulator alone did not. [Castell et al.](https://doi.org/10.1257/pol.20220786).
- **Transparency with impunity (Bauhr & Grimes, 2014):** In environments of widespread corruption, transparency can discourage rather than mobilize citizens. Thus an information dashboard needs disposition and remediation, not just scandal exposure. [Governance](https://doi.org/10.1111/gove.12033).

## 5. Direct answer to the central research question

**Does elite impunity or bureaucratic inefficiency have the greater effect on national-government trust?**
*Unresolved.* OECD surveys associate national-level trust more strongly with political voice, governing-party support and high-level decision-making perceptions than with service satisfaction. This is **not** a causal estimate comparing scandal treatment with actual service delays. For trust in civil servants and local government, administrative experience appears more closely associated with the outcome.

**Does high elite impunity amplify the damage of bureaucratic friction?**
*Plausible, not demonstrated.* To establish H3 requires either a credible individual randomized 2×2 factorial design or an event/exposure design linking measured misconduct disposition, affected citizen service contact, and trust at the right time scale.

**Is institutional collapse inevitable?**
*No.* National trust averages stabilized and national-government and civil-service trust sometimes diverged. Evidence supports institutional differentiation and potential resilience, not a universal one-way collapse.

**Do citizens stop obeying laws when trust declines?**
*Not established by this dataset.* Survey-reported willingness to obey, actual tax compliance, lawful civic protest, service take-up and support for authoritarian rule are different outcomes. They cannot be used interchangeably.

## 6. Reforms worth implementing and testing

| Priority | Intervention | Outcome and verification | Evidence maturity |
|---|---|---|---|
| 1 | Publish complete accountability case dispositions with procedural protections and appeal outcomes | Time to final disposition, reversal rate, consistency for comparable violations, independently verified remedies | OECD implementation gaps support monitoring need; trust effects untested |
| 2 | Measure end-to-end citizen outcomes, not internal 'calls answered' or selective service-level metrics | Time from first request to final resolution, corrected error rates, repeat contacts and appeals | Strong audit-based performance evidence |
| 3 | Simplify compliance and provide practical application help | **Final benefit receipt**, unequal take-up, end-to-end burden hours; compare with information-only intervention | Stronger experimental support for take-up than for trust |
| 4 | Strengthen independent review and accessible appeals | Remedy success, access across socioeconomic groups, review independence | Mechanism defensible; implementation and trust gains need evaluation |
| 5 | Improve meaningful political participation, including low-resource groups | Validated political agency measures, uptake and representational responsiveness | Strong OECD observational associations; intervention effects not yet established |
| 6 | Digitize selected service steps with nondigital access and human appeals | Completion, exclusion, accessibility and erroneous denial metrics | Potential efficiency gains; avoid new algorithmic burdens |
| 7 | Evaluate reforms with prespecified counterfactuals | Actual behavior, trust in the relevant institution, costs and equity | Necessary to establish benefits rather than promise them |

**Do not publish a 'decay score' until both its validity and direction have been evaluated.** In particular, a zero practice score is not a percentage of people 'getting away' with corruption. Mark coverage and source uncertainty separately from severity.

## 7. What is complete versus what remains scientifically unanswered

**Complete in this evidence assessment:**
1. Literature synthesis and neutral theory with competing explanations.
2. Primary-source UK and US case evidence with correct event/legal-status separation.
3. 407 published trust measurements and 28 clean matched national-government trend observations.
4. Descriptive inter-institution differences, correlations and one-country-exclusion sensitivity.
5. OECD 2026 implementation-gap evidence and limited source-tagged country examples.
6. Research governance, transparent source listing, reproducible scripts and regression/experiment prerequisites.
7. Decision-ready distinctions among supported empirical findings, observational associations and untested hypotheses.

**Not completed; must never be reported as completed:**
1. A validated comprehensive OECD PII country-year panel with matched, time-consistent measures and coverage diagnostics.
2. Access to, or analysis of, restricted OECD individual trust microdata (application required).
3. An actual randomized survey experiment or causal quasi-experimental estimate of the impunity × burden interaction.
4. A demonstrated feedback loop from declining trust to administrative deterioration, and a robust quantified comparison of elite scandal versus service delay effects.
5. Production-app presentation of the research; the repository's redistricting `data/app-feed.json` remains separate.

These are **research identification limits**, not an excuse to invent findings. The conceptual and descriptive assessment can be closed with an informed conclusion without falsely declaring all causal questions solved.

## 8. Reproducibility and publication status

- Source extract: [trust-country-waves-2023-2025.json](../../data/institutional-decay/trust-country-waves-2023-2025.json).
- Supplementary primary-source records and case timeline: [evidence-v1.json](../../data/institutional-decay/evidence-v1.json).
- Accountability criteria extract: [integrity-implementation-2025.json](../../data/institutional-decay/integrity-implementation-2025.json).
- Calculations: `python scripts/analyze_institutional_decay.py`.
- Validation: `python -m unittest discover -s tests -p 'test_*.py' -v`.
- All numeric values from the OECD survey are **published rounded country percentage estimates**, and OECD is cited as source; this is an independent adaptation, not an OECD-endorsed interpretation.
- Data-licensing, source-vintage, bias and missingness checks remain mandatory before expanding the released data products.

### Final scientific statement

> Evidence indicates that procedural unfairness and administrative burdens are important, distinct risks to institutional legitimacy. Government trust is heterogeneous and strongly politically conditioned; public-service and political institutions may experience divergent trust trajectories. A compounding effect of elite impunity and bureaucratic inadequacy is a coherent, testable hypothesis, but remains causally unproven with the currently reviewed evidence. Accountability reforms should therefore be evaluated alongside end-to-end service outcomes, with due process, evidence provenance and measurable redress at the center.

**Readiness to publish:** This document is **ready as a source-backed descriptive and literature assessment, with the above limits clearly disclosed**. It is **not ready as a causal proof, a scandal-based guilt ranking, or a validated national/international composite institutional-decay index**.
