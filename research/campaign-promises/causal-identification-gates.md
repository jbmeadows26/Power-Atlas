# Transition audit: valid causal questions versus unverified causal claims

**Power Atlas, Political Promises | October 29, 2026**  
**Status:** Implemented and automatically tested research architecture; the **original causal estimates are not completed** until independently verified identification inputs exist. An architecture test with invented observations is not a study of real elections.

## 1. Final pledge denominator: cohort, inclusion, negative checks

The research question is about verifiable *pre-election commitments*, not party talking points. A correct 2020 cohort must freeze the set of primary sources before viewing outcomes. The known manifest in [adjudication source inventory](../../data/promises/adjudication-2020-template.json) currently includes archived 2020 Democratic platform, RNC August 24 2020 resolution foregoing a new Republican platform, Biden/Trump nomination acceptance speeches, and one Biden campaign release. **Five primary texts are a starting manifest, not the complete promised corpus.** The election date is November 3, 2020. The outcome window for the Biden administration ends January 20, 2025. The Republican candidate did not win in 2020; evaluating the 2016 Republican platform as if it were the 2021–25 governing party would be a mistaken denominator.

**Census procedure:**
1. Declare which nominee-authored texts, campaign releases, party manifestos, and nominee speeches were binding before the election; document exclusion of surrogate and post-election material, and version/legal usage conditions.
2. Build a source hash or version map, sentence/paragraph boundaries and deterministic IDs. Export every candidate claim and exclusions with exact passage locator, speaker, date, time window, jurisdiction and original source. Scrape or republish licensed text only with lawful authorization; cited short paraphrases are default.
3. Two coders independently mark whether each forward-looking claim is *specific, testable, attributable, not already completed, and not duplicate*. Atomize one-to-many compound claims but retain shared parent ID. Every duplicate has a canonical parent and reason; technical reproducibility tests do not substitute for coders.
4. Freeze the eligible atom count and explicitly separate governing-party from opposition commitments before scoring the outcomes; do not count a candidate's repetition as another pledge.
5. Independent coders view contemporaneous statute, bill, executive order, rule, budget, treaty/agency implementation records and decisions to reconcile outcomes. Record original promise *scope, deadline and intended target*, and link the adjudicated status to primary dated events.
6. For publication report \`eligible_total, adjudicated_total, unknown_total, full_total, partial_total, attempted_unachieved_total, documented_no_formal_effort_total\`, with review agreement and duplicate/exclusion counts. The denominator must match the chosen estimand (all commitments or all matured and adjudicated commitments) with unknowns shown separately. Do **not** interpret an "unknown" as abandoned.

**Current verified count:** eight *purposive singly reviewed* illustrated cases and 24 additional *unreviewed candidates*. There are **no independently dual-adjudicated claims and no exhaustive denominator**. Consequently 7/8 is **not** a valid politician-wide fulfillment rate.

### Rubric: four ordinal states plus unknown

| Score | Label | Required observable evidence |
|---|---|---|
| 3 | Fully achieved | The exact atomic commitment's promised policy target has been substantively attained *within scope and deadline*. A successful executive action may fully satisfy an executive-action pledge. |
| 2 | Partly achieved | Material but narrower or incomplete target achieved; partial implementation/adoption or reach separately quantified. Lack of statute alone does not make a promised executive action partial. |
| 1 | Attempted, not achieved | Dated formal legislative/executive/administrative action occurred, but the original pledged target was unmet by deadline. A separately coded institutional veto point is needed to label it "blocked." |
| 0 | No formal effort found | **Exhaustive, dated, documented negative search across applicable official action systems** and no formal action. Even this does not establish intent to deceive. |
| null | Unreviewed / indeterminate / right-censored | No sufficient evidence, incomplete search, conflicting sources, pending deadline or insufficient authority to reach decision. Do not convert to 0. |

Score labels are ordinal; avoid a mathematical arithmetic mean unless research justifies equal distances between qualitatively distinct states. Report category percentages and sensitivity with/without unknowns. Measure actual policy reach, effort, permanence and successor reversals **separately**. A filed bill is not the same as enactment. A successor reversal is not proof the original pledge was never fulfilled.

### Independent adjudication safeguards

Each case stores reviewerOne and reviewerTwo as separate identities, their independently submitted decisions and original source URLs, the reconciled decision, evidence/date/target. The code **fails** if a numeric score lacks two distinct independent raters and explicit adjudication. A zero score also requires five completed negative-search checks over Congress bills, Federal Register, budgets, executive actions and agencies (specific agencies/jurisdictions must additionally be covered). The generated template intentionally sets all scores, effort indicators and intent conclusions to null. The actual case study remains provisional until independent reviewers exist; code execution is not a second human reviewer.

## 2. Legislative effort index: useful evidence, invalid deception classifier

Separate effort variables: agenda/budget mention, formal allied bill sponsorship, and funded administrative/preparatory work. Applicability depends on jurisdiction: a federal treaty pledge, an executive-only proclamation and a capital spending promise have different implementation levers. The provided index implementation:
- returns null if an applicable dimension is unknown or applicability is unreviewed;
- excludes genuinely inapplicable components;
- counts only sourced positive action, with its possible range **0..number of applicable components**;
- never labels a politician dishonest by itself.

**Crucial correction:** the proposed deterministic matrix "\`LEI=0\` + unified government = deception" is not an identified psychological or legal finding. Examples of rival causes include competing crises, agenda congestion, subnational or judicial constraints, party faction vetoes, Senate rules even under nominal unified government, discretionary powers, insufficient fiscal capacity, agency bottlenecks and public issue priority. **Absence of action evidence is not proof that action did not occur**; even a genuinely zero effort score cannot establish knowing misrepresentation without direct contemporaneous contradictory evidence. Label the result \`no_documented_formal_attempt_despite_effective_control\`, with evidence and uncertainty, not "dishonesty."

## 3. U.S. state capital outlay and a tested TWFE model

Original source: [U.S. Census official finance ZIP](https://www2.census.gov/programs-surveys/state/data/api_dataset/GOVSSTATEFINTIMESERIES.zip). Persisted [50-state × 13-year data](../../data/fiscal/state-timeseries/aggregate-capital-2012-2024.json) contain **650 actual state-year observations and 3,250 official government expenditure aggregate lines**. Our dependent variable is **100 × SF0178 / SF0175** in percentage points, not a currency amount. Real descriptive fiscal outputs are already supported.

Proposed observational specification:

\[
Y_{st}=\alpha_s+\lambda_t+\beta_1\,ElectionFY_{st}+\beta_2\,PreElectionFY_{st}+
\gamma_1 GDPGrowth_{s,t-1}+\gamma_2 Unemployment_{s,t-1}+
\gamma_3 FederalTransfersShare_{s,t-1}+\epsilon_{st}.
\]

The implemented [TWFE estimator](../../scripts/estimate_electoral_twfe.py) uses \`statsmodels.formula.api.ols\`, state fixed effects, fiscal-year fixed effects, and state-clustered standard errors with small-sample correction. The response metric is *percentage points*. A separately tested \`--simulate\` mode generates **synthetic** state/year effects, cyclical elections and known injected regression coefficients \`beta_1=-1.50\` and \`beta_2=-0.70\`, so the tests can verify that the estimator recovers what was deliberately inserted. **Those numerical values are fictional test inputs, not U.S. findings.** Simulated rows are not persisted in the research feed.

The \`--real\` mode fails closed until a separate \`power-atlas.verified-governor-fiscal-controls.v1\` source file supplies **all 650** historically verifiable state–fiscal-year treatments, state statutes or official fiscal-year calendars, certified gubernatorial election dates, BEA state GDP controls, BLS unemployment controls, and reconciled Census federal transfers as a share of state revenue. Source links, pre-budget timing, nonmissing values, historical verification flags and exact unique FIPS/FY join keys are required. No evidence file is currently available with that validated content, so **no real model has been estimated**.

**Notable methodological qualifications:**
- Annual FY labels do not always contain November elections. New York, Texas, Alabama and Michigan have non-July fiscal starts. Elections late in the calendar year often occur in a fiscal year labeled with the following calendar year, so \`FY2024 == 2024 general election\` is wrong in many states.
- Two-year election cycles in New Hampshire and Vermont, off-cycle years for VA/NJ/KY/LA/MS, extraordinary elections and the Louisiana primary/runoff system must be handled with actual dated ballots. Election-year and pre-election-FY dummies should not both be 1 for one observation.
- Common year FE absorb a *homogeneous* national 2022 accounting change but **do not repair heterogeneous state-by-year reclassification**, differences in expenditure functions, or an endogenously changing denominator. At minimum present 2012–2021 and 2022–2024 regimes separately; 2022–24 is too short for a credible full election cycle within most states.
- Covariates measured contemporaneously after an election may be *mediators*; strict pre-budget/lags reduce but do not eliminate endogeneity. Federal transfers may themselves be election-related, so adjustment can absorb genuine effects. Report both pre-specified controlled/uncontrolled designs, justified assumptions, and avoid post-treatment conditioning.
- Plain TWFE periodic election dummies + clustered standard errors provide conditional associations, **not necessarily causal effects**. Identification also depends on anticipation, plausibly fixed electoral timing, absence of calendar-correlated shocks, spillovers and measurement quality. Falsify with pre-trends, leads/lags, placebo dates, within-regime and COVID-excluded fits, multiple fiscal-year assignment rules, state-by-time drift and state-level heterogeneity. For dynamic effects, inspect collinearity and variation before fitting.
- A shift in recorded capital outlay as a share of direct spending could result from changes to the *denominator*. It does not establish long-term opportunity cost, contract delays or high/low social return. Trace **announced commitment, appropriated budget, legally obligated money, actual outlays and delivered asset** separately.

## 4. Research publication gates

| Requirement | Verified status (2026-10-29) | UI/statistical release |
|---|---|---|
| Original source-linked illustrative pledge examples | 8 provisional | Show dated case evidence; not a population rate |
| Exhaustive source sentence inventory and deduplicated atomic denominator | Not completed | Rate suppressed |
| Two independent human reviews and reconciled pledge scores | 0 completed | Adjudicated score suppressed |
| Documented action/negative search and appropriate LEI denominators | Template only | No policy actor motive labels |
| Census 50-state annual expenditure data, 2012–2024 | **650 verified** | Descriptive charts permitted with 2022 break |
| Governor-election dates precisely joined to historical fiscal windows | Not completed | No real election-cycle coefficient |
| Complete pre-treatment state GDP, unemployment, federal transfers | Not completed | No real controlled TWFE coefficient |
| Statsmodels regression algorithm / synthetic recovery tests | Implemented, pending CI verification | Display only as architecture validation |
| Quasi-experimental causal identification and robustness | Not completed | No "causal" label |
| Intent-specific documentary evidence | Not evaluated | Do not label "deception" |

### Exact commands

\`\`\`bash
python -m scripts.prepare_pledge_adjudication
python -m unittest discover -s tests -p 'test_pledge_review_2020.py' -v
python -m pip install numpy==2.3.5 pandas==2.2.3 statsmodels==0.14.6
python -m unittest discover -s checks -p 'twfe_architecture_checks.py' -v
python -m scripts.estimate_electoral_twfe --simulate
# Intentionally blocked without independent validated official controls:
python -m scripts.estimate_electoral_twfe --real
\`\`\`

**End state:** testable, executable and explicitly nonpartisan research framework with an honest separation among (1) official measured finance, (2) artificial regression test data, (3) provisional pledge judgments, (4) not-yet-estimated causal relationships and (5) unsupported claims about intent.

The methodology uses [the American Presidency Project's 2020 platform index](https://www.presidency.ucsb.edu/documents/app-categories/elections-and-transitions/party-platforms), including its [August 24, 2020 Republican platform resolution](https://www.presidency.ucsb.edu/documents/resolution-regarding-the-republican-party-platform), and [official 2020 nomination speeches](https://www.presidency.ucsb.edu/documents/address-accepting-the-democratic-presidential-nomination-wilmington-delaware) and [Republican acceptance speech](https://www.presidency.ucsb.edu/documents/address-accepting-the-republican-presidential-nomination-2). For Census classification cautions see [official 2022 state-finance documentation](https://www.census.gov/programs-surveys/state/technical-documentation/methodology/annual-methodology/2022.html). See [the completed baseline assessment](./assessment-complete-2026-10-29.md) for the separate established comparative political science results.
