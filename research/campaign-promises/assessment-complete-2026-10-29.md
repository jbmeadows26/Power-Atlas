# Campaign promises, governing constraints, and electoral short-termism: final evidence assessment

**Assessment cutoff:** October 29, 2026 · **Status:** assessment complete; underlying population pledge study and election-cycle causal estimation remain incomplete.  
**Project:** Political Promises / Power Atlas · **Scope:** U.S. 2020 source-checked pledge pilot; U.S. state finance FY2012–FY2024 and archived government-finance code families FY2000–FY2015; established comparative political-science research.  
**Evidence source:** This report can be reproduced using [the machine-readable assessment](../../data/promises/assessment-2026-10-29.json) and [its validator](../../scripts/build_campaign_assessment.py). It is not a finding that any politician knowingly lied.

## Executive summary

1. **The claim that parties generally break their promises is not established.** In comparative research, governing parties often fulfill meaningful portions of their commitments, and executive/governing control and coalition bargaining help explain variance. Thomson et al. (2017) examined **more than 20,000 pledges across 57 campaigns and 12 countries**. In a separate historical comparison of **14 countries and 69 elections (1977–2015)**, Matthieß (2020) reports a **60% mean governing-party fulfillment share**, with observed party-government rates from **23% to 92%**. These are **published external benchmarks**, not our own current U.S. rate. [Thomson et al., AJPS 2017](https://doi.org/10.1111/ajps.12313) · [Matthieß, EJPR 2020](https://doi.org/10.1111/1475-6765.12377).

2. **Pledge accountability needs at least four independent observations:** a time-stamped *campaign commitment*, what government *formally attempted*, what was actually *enacted/implemented*, and whether the result *persisted*. A failed bill, veto, resource shock or judicial constraint does not by itself prove bad faith. Our existing U.S. 2020 pilot has **eight purposively selected, singly reviewed cases**—seven provisionally coded *fully enacted*, one *attempted not enacted*—plus **24 candidate commitments whose outcomes are entirely unreviewed**. The pilot is **not** an exhaustive or representative denominator. Its superficially tempting 7/8 score must **never** be displayed as an 87.5% administration-wide fulfillment rate, nor given an inferential confidence interval.

3. **Election-related budget distortions are documented in research, but differ by mechanism and political context.** Drazen and Eslava find electoral shifts toward targeted spending in Colombian municipalities. Pierskalla and Sacks show election-related capital spending declines in low-capacity Indonesian districts due to administrative distraction—**not necessarily deliberate cash transfers away from infrastructure**. Brender and Drazen find aggregate fiscal-deficit cycles concentrated in newer democracies, undermining claims of a universal election-year deficit effect. [Drazen & Eslava 2010](https://doi.org/10.1016/j.jdeveco.2009.01.001) · [Pierskalla & Sacks 2018](https://doi.org/10.1086/694547) · [Brender & Drazen 2005](https://www.nber.org/papers/w10539).

4. **Power Atlas now has real descriptive public-investment observations, not an electoral manipulation estimate.** From an official public Census archive it ingested **273,258** source rows and retained **3,250** explicitly defined expenditure aggregates in a balanced panel of **650 state–fiscal-year rows (50 states × 13 fiscal years, 2012–2024)**. Its measure is **direct capital outlay / total direct expenditure**, using Census codes **SF0178 / SF0175**, both in reported USD thousands. Source: [official Census time-series ZIP](https://www2.census.gov/programs-surveys/state/data/api_dataset/GOVSSTATEFINTIMESERIES.zip); [dataset with checksums and annual observations](../../data/fiscal/state-timeseries/aggregate-capital-2012-2024.json). The provisional 650-record fiscal-date template **has no verified historical election matches**. No election-timing coefficient, confidence interval or causal claim is justified.

**Overall assessment:** the research questions are scientifically well posed and backed by credible literature, and the source ingestion phase has yielded usable fiscal evidence. The evidence *assessment* can be closed and published. The empirical questions "what proportion of the complete U.S. 2020 pledge population was fulfilled?" and "what is the causal effect of election proximity on U.S. state spending mix?" are **not yet resolved** by Power Atlas.

## 1. Pledge attrition: what is demonstrated

### External evidence is incompatible with blanket "all politicians lie" narratives

The [Comparative Party Pledges Project](https://comparativepledges.net/publications/) and Thomson et al. (2017) use cross-national, testable commitments rather than impressionistic approval ratings. Their key result is that governing-party fulfillment tends to exceed opposition-party fulfillment, and it varies with how executive power is shared. Single-party cabinets have particularly high rates; within coalitions, the chief executive portfolio and compatible pledges from other partners matter. These are empirical associations in historical political contexts, not proof every unfulfilled pledge was unavoidable.

A later analysis, [Matthieß (2020)](https://www.cambridge.org/core/journals/european-journal-of-political-research/article/retrospective-pledge-voting-a-comparative-study-of-the-electoral-consequences-of-government-parties-pledge-fulfilment/C8284CCABDC65D3F7DFFF549CC4446DA), reports a mean party-level pledge fulfillment of **60%** across a historical 14-country, 69-election sample and a **23–92%** case range. This is **not** an observation about the Biden administration or U.S. 2020 election, and it does not use the same denominator and status vocabulary as our pilot. It supports *heterogeneity*, not a fixed universal rate. The same work studies electoral consequences of pledges, conditional on voter knowledge and attribution; an observational fulfillment–vote association is not sufficient to prove voters caused politicians to comply.

An additional bargaining interpretation in [*Policy as a Bargaining Outcome* (2026)](https://doi.org/10.1017/S0007123426101641) evaluates coalition leverage in nine parliamentary democracies. This reinforces an important alternative to an intent-based explanation: a policy can fail in a coalition because the party lacks bargaining power even when it originally preferred the policy. Treat coalition configurations as endogenous, not randomly assigned.

### What the in-repository U.S. 2020 ledger actually contains

| Original campaign commitment (atomic outcome) | Provisional disposition at 2025 term end | Qualifying caveat |
| --- | --- | --- |
| Rejoin Paris climate agreement | Fully enacted | Reentry is distinct from later emissions performance |
| Rescind planned WHO withdrawal / restore participation | Fully enacted | U.S. withdrawal had not legally completed; *WHO reform* is a separate unreviewed pledge |
| Revoke named travel-ban orders | Fully enacted | Does not establish all visa remediation or later immigration policy |
| Restore Bears Ears protections | Fully enacted | Later successor actions must be treated as separate durability events |
| Secure Kigali Amendment ratification | Fully enacted | Senate consent, deposit and entry into force are separate milestones |
| Return to UN Human Rights Council | Fully enacted | Membership is distinct from promised institutional reform |
| Terminate southern-border national emergency | Fully enacted | Does not claim all wall expenditures ended; successor policy is a separate period |
| Establish nationwide federal $15 minimum wage | Attempted, not enacted | Covered-contractor wage executive action did not establish the nationwide statutory target |

Sources for each promise, official primary action, date, source locator and ambiguity are in [original two-case ledger](../../data/promises/us-2020-pilot.json) and [six-case expansion](../../data/promises/us-2020-source-verified-expansion.json); 2020 campaign text is archived at the [American Presidency Project](https://www.presidency.ucsb.edu/documents/2020-democratic-party-platform). The [24-source candidate queue](../../data/promises/us-2020-review-queue.json) covers additional healthcare, election law, civil rights, environment, taxes, employment and other policy pledges but is **not outcome adjudicated**.

**Release decision:** publish these eight as *dated provisional case files with source links*, never as a representative nationwide fulfillment rate. Independent second-coder/adjudication count is **0**. The denominator has **not** been frozen; headline "broken promise rates" would be selection-biased. The 24 unreviewed records are neither failures nor successes.

### Required research-quality distinction

A source-verified case identifies a *testable in-term action*. It does not prove an unobservable motive. A defensible pledge analysis must have separate fields for (i) commitment atom and date, (ii) policy actor and legal authority, (iii) legislative attempt, (iv) formal enactment, (v) implementation reach and expenditure, (vi) term-end outcome, (vii) later persistence/reversal, (viii) alternative explanations, and (ix) source confidence and independent reviewer decisions. Case codings must distinguish candidate vs party vs coalition commitments. Unknown, right-censored and truly unattempted are not interchangeable.

## 2. Electoral short-termism: findings and limits

### What the peer-reviewed causal/mechanism literature supports

- **Opportunistic composition changes:** [Drazen & Eslava, *JDE* (2010)](https://doi.org/10.1016/j.jdeveco.2009.01.001) show a municipal-level Colombian shift toward voter-targeted expenditures near elections alongside contraction in less-targeted categories. Their model also allows voters to interpret targeted spending as sincere preference, not exclusively manipulation.
- **Capacity/delivery disruptions:** [Pierskalla & Sacks, *JOP* (2018)](https://doi.org/10.1086/694547) exploit the timing/phasing of local Indonesian elections and document a drop in capital spending in low-capacity contexts associated with distraction and scrutiny.
- **Context sensitivity and counterevidence:** [Brender & Drazen, *JME* (2005)](https://www.nber.org/papers/w10539) find that election-year aggregate fiscal-deficit cycles are not universal to established democracies. [Shi & Svensson, *JPubE* (2006)](https://doi.org/10.1016/j.jpubeco.2005.09.009) report fiscal deficit expansion averaged across a broad historical country panel and stronger cycles in developing countries.
- **Portugal, non-universal timing:** [Castro & Martins, *Applied Economics Letters* (2016)](https://doi.org/10.1080/13504851.2015.1047084) find greater election-period expenditures in comparatively visible Portuguese government functions (general public services, social protection and healthcare), reinforcing that **composition** can matter more than total expenditure.

These studies jointly support *competing testable mechanisms*, not universal blame. A deficit increase, contract delay, pre-election spending announcement and an unfulfilled policy pledge are four different phenomena.

### What Power Atlas directly measured

Source: [Census state-only financial aggregates](../../data/fiscal/state-timeseries/aggregate-capital-2012-2024.json), original source SHA-256 **888dfbb3f8eeebce01b409e4e86178ac04c596c7fc355047beef2433a9b5be48**. The statistic below is the **arithmetic mean of the 50 separately reported state capital-outlay/direct-expenditure shares**, rounded to two decimal percentage points. The pooled share uses the sum of all capital amounts divided by the sum of all direct expenditure amounts in the same year's state panel; these two estimands are different.

| Fiscal year | Mean of 50 state shares | Pooled state expenditure share | Accounting regime |
| --- | ---: | ---: | --- |
| 2012 | 8.67% | 7.85% | Prior to 2022 |
| 2013 | 8.40% | 7.89% | Prior to 2022 |
| 2014 | 7.81% | 7.38% | Prior to 2022 |
| 2015 | 8.27% | 7.87% | Prior to 2022 |
| 2016 | 8.31% | 7.68% | Prior to 2022 |
| 2017 | 8.14% | 7.47% | Prior to 2022 |
| 2018 | 7.95% | 7.68% | Prior to 2022 |
| 2019 | 7.92% | 7.75% | Prior to 2022 |
| 2020 | 7.60% | 6.94% | Prior to 2022 |
| 2021 | 6.83% | 6.32% | Prior to 2022 |
| 2022 | 7.81% | 7.18% | **Reclassified methodology** |
| 2023 | 8.37% | 7.44% | After 2022 change |
| 2024 | 9.22% | 8.26% | After 2022 change |

**Descriptive, not electoral:** the equally weighted state average fell **1.84 percentage points from 2012 to 2021**, then rose **1.41 percentage points from 2022 to 2024 within the newer accounting regime**. The 2021–2022 jump must **not** be read as a seamless economic change due to the 2022 Census methodology break. The denominator also matters: in the pooled 50-state data, nominal direct expenditure increased **9.0% between FY2020 and FY2021**, while recorded nominal capital outlay decreased about **0.79%**. The pooled capital share consequently declined **0.62 percentage points** even though the capital spending level moved far less than the denominator. This example demonstrates why a lower investment *share* does not by itself prove capital-project cancellation, let alone electoral manipulation.

The modern panel's [Census original field dictionary](https://www2.census.gov/programs-surveys/state/data/api_dataset/GOVSSTATEFINTIMESERIES.zip) explicitly states that published monetary amounts are **in thousands of dollars**. Ratios are unit-invariant; dollar levels are nominal and must be deflated for real-growth claims. The official [2022 technical documentation](https://www2.census.gov/programs-surveys/state/technical-documentation/complete-technical-documentation/statetechdoc2022.pdf) and [2024 technical documentation](https://www2.census.gov/programs-surveys/state/technical-documentation/complete-technical-documentation/statetechdoc2024.pdf) identify reclassification: former construction F, other capital G and equipment K were consolidated in the new F coding, among other changes. Although the aggregate variable SF0178 remains defined as *total direct capital outlay*, we **have not independently reconciled pre/post-change accounting scope**. Any full-period causal time-series interpretation must first pass a bridge audit.

### Why the historical archive is not an interchangeable appendix

The [legacy archival source audit](../../data/fiscal/state-legacy/quality-audit.json) independently verified **65,554 raw historical F/G/K source-code rows across 2000–2015**, covering 50 governments per year and preserving **66 missing markers**. These rows are non-additive: historical G capital-outlay values can contain K equipment. Summing **F + G + K** would risk counting K twice. A raw row-count discontinuity occurs between 2012 (3,959 rows) and 2013 (4,656 rows); that **17.6% count increase is NOT a 17.6% spending increase**. Historical 2000–2011 source-code rows have not been harmonized into a consistent modern ratio. **The validated aggregated finance series therefore starts in 2012**, not 2000.

### Why the election effect has not yet been estimated

The date template contains **650 provisional fiscal start/end intervals**, reflecting modern state fiscal rules: 46 states July–June, New York April–March, Texas September–August, and Alabama/Michigan October–September ([NCSL](https://www.ncsl.org/fiscal/fy-2027-state-budget-status)). Their exact historical stability for each FY2012–FY2024 has not been independently proven in the project. **No gubernatorial election dates, offices or treatment exposure values have been joined to those records.** Annual Census records do not establish monthly pre-election spikes, and fiscal year outlays may have been authorized many months earlier.

The project therefore has:
- a **descriptive** 50-state × 13-year modern finance panel;
- **no approved election proximity variable**;
- **no identified election-cycle regression coefficient, CI or p-value**;
- **no evidence that a decline is caused by short-term electoral priorities**.

An automated test passing is not an empirical finding; it confirms that data versions and invariants match.

## 3. Causal designs and falsification requirements

**Pledges.** Predefine the denominator and inclusion algorithm using time-stamped party manifestos and candidate releases *before viewing government outcomes*. Atomize compound sentences; stratify by institution/policy domain; document exclusions, double-coded selections, Krippendorff alpha/weighted kappa and adjudication. For every completed term report full, partial, attempted-not-enacted, unattempted and unresolved separately. Distinguish passage from actual implementation and persistence. Competing risks event-time estimation may test completion speed versus legislative constraint or government turnover. Apparent party differences can be due to who gains office, policy difficulty, pledge specificity, selection, coalition compromise and exogenous crises.

**U.S. state finance.** With historically verified fiscal dates and official state governor election results, pre-register a within-state election-event design:

\`capital_outlay_share[s,t] = state_FE[s] + FY_FE[t] + sum_k beta[k] * election_event_time[s,t,k] + pre_treatment_controls[s,t-1] + error[s,t]\`

This is a **proposed specification, not an estimated equation**. The outcome can be analyzed both state equally weighted and pooled expenditure weighted. Important adjustments: New Hampshire and Vermont have two-year governor election cycles; biennial budgeting, term limits, incumbent/challenger status, governor and legislative control, pre-election budget proposal dates, recession/disaster/pandemic shocks, federal grant timing, and capital-project multiyear execution. Outcome construction must prevent denominator shifts from masquerading as an election effect.

**Causal tests:** pre-event leads, post-event lags, placebo years, announcement-versus-outlay differences, state and year fixed-effects diagnostics, clustering within states and election cycles, alternative fiscal-year overlaps, exclusions of COVID years and reclassification periods, and sensitivity by executive and administrative capacity. Politicians' competitiveness may be endogenous; controlled regressions do not prove intent. Distinguish *visible targeted transfers* (requires a different spending classification) from *capital outlay* (present) and *infrastructure/social ROI* (not measured).

**Comparative replication.** US, UK, Canada, Germany and Portugal provide useful institutional contrasts but not a sufficiently large independent-country sample for a convincing pooled cross-country political budget cycle causal estimate. Use comparable OECD/Eurostat/IMF measures only after verifying public-sector boundaries, national accounts vs budget outlays, clock timing, parliamentary snap-election endogeneity and licensing. Keep comparison exploratory until sample sizes and definitions pass audit.

## 4. Quality verdict and publication decision

| Evidence/claim | Verified in Power Atlas? | Decision |
| --- | --- | --- |
| Eight individually source-linked 2020 pledge case files | **Yes**, provisional, single-review | Publish with caveats |
| Exhaustive governing-party pledge denominator | **No** | **Do not publish fulfillment rate** |
| Independent adjudication of promise outcomes | **No** (0 dual-coded) | Keep provisional |
| Twenty-four queued pledges with independently determined outcomes | **No** | Mark unreviewed; never broken |
| Historical 2000–2015 Census F/G/K data source integrity | **Yes**, source-level audit | Publish raw-source audit only |
| Modern FY2012–FY2024 official state spending aggregates | **Yes**, 650 records | Publish descriptive measures |
| Harmonized 2000–2024 continuous investment panel | **No** | Do not join naively |
| Historically verified FY2012–FY2024 fiscal windows | **Only provisional modern-rule backcast** | Do not assign treatment |
| Governor election events joined to the fiscal data | **No** | No election-event model |
| Causal effect on public investment or electoral trust | **No** | Suppress coefficients and causal language |
| "Bad actor"/intent-to-deceive attribution | **Not established** | Do not accuse based on nonfulfillment |

### Data integration issue found

The older [promise-specific research feed](../../data/promises/research-feed.json) still states \`fiscalSeriesObservations: 0\`, and the [promise-source registry](../../data/promises/source-registry.json) retains \`recordCountIngested: 0\` for its Census pointer. Those counters were true *when the promise feed was created*, but are stale now that the separate finance collectors have published **650** state-year observations. The new assessment recomputes the verified fiscal count from the **actual persisted official finance records** and explicitly marks the old counters as stale; it does **not** rewrite them as if the pledge population were complete. A future feed rebuild should use separate, authoritative counts by domain and distinguish "source listed" from "source ingested."

### Recommendations, not confirmed interventions

An independent pledge registry, post-election milestones and source-link audits are defensible transparency tools because they reduce the informational ambiguity of campaign statements. Public capital-project lifecycle tracking may help distinguish meaningful long-run investment from election-period announcements. Pre-election independent fiscal costing, transparent long-horizon investment plans and procurement timelines are plausible reforms. **This study has not evaluated their causal effectiveness**; no reform should be marketed as proven by the current Atlas data.

For public UI and research communications:
1. Show the **case-level evidence and review status**, not an 87.5% "promise score."
2. Show the **descriptive fiscal panel** with equal-/expenditure-weighted definitions, 2022 coding breakpoint and annual frequency.
3. Keep **fulfillment percentages, politician motive classifications, election-cycle coefficients and policy ROI** unavailable until their distinct quality gates have passed.
4. Present institutional alternatives—divided government, coalition bargaining, courts, budget constraints, administrative capacity and shocks—before inferring a political actor's intentions.
5. Separate any published primary literature result from an original Power Atlas calculation and attach its geographic/time sample.

## Final scientific judgment

**Question A — What share of campaign pledges is fulfilled, and what drives attrition?**

*Answer from independent scholarship:* Fulfillment is often substantial, variable and shaped by the amount and configuration of governing power. The best cited historical party-level comparative average here is **60%**, but that figure cannot be transplanted to 2020 U.S. candidates or used to judge any particular party. *Answer from Power Atlas:* **Not yet estimable** because the full eligible pledge universe and independent coding are missing. The pilot has eight usable illustrative cases, not a representative rate.

**Question B — Does election proximity redirect effort and spending away from the long term?**

*Answer from published scholarship:* Such distortions occur in some settings; composition changes, administrative interruptions and headline budget expansion are different mechanisms. Effects vary by governance and democratic institutions. *Answer from Power Atlas:* It has established and validated a 50-state descriptive investment-outlay panel, but **no election-calendar join or causal estimator exists**. A pre-election trade-off **cannot yet be asserted or refuted** for U.S. states from these observations alone.

**Assessment complete. Original causal study incomplete.** The scientifically valid deliverable is the verified evidence inventory, calibrated conclusions, an explicit map of unresolved dependencies and a testable identification strategy—not an invented fulfillment percentage or regression coefficient.

---

## Original literature and source register

- Robert Thomson et al., [*The Fulfillment of Parties' Election Pledges*](https://doi.org/10.1111/ajps.12313), *American Journal of Political Science* 61 (2017), 527–542.
- Theres Matthieß, [*Retrospective pledge voting*](https://doi.org/10.1111/1475-6765.12377), *European Journal of Political Research* 59 (2020), 774–796.
- Allan Drazen and Marcela Eslava, [*Electoral manipulation via voter-friendly spending*](https://doi.org/10.1016/j.jdeveco.2009.01.001), *Journal of Development Economics* 92 (2010), 39–52.
- Jan H. Pierskalla and Audrey Sacks, [*Unpaved Road Ahead*](https://doi.org/10.1086/694547), *Journal of Politics* 80 (2018).
- Adi Brender and Allan Drazen, [*Political Budget Cycles in New versus Established Democracies*](https://www.nber.org/papers/w10539), *Journal of Monetary Economics* 52 (2005).
- Min Shi and Jakob Svensson, [*Political budget cycles: Do they differ across countries and why?*](https://doi.org/10.1016/j.jpubeco.2005.09.009), *Journal of Public Economics* 90 (2006).
- Vítor Castro and Rodrigo Martins, [*Are there political cycles hidden inside government expenditures?*](https://doi.org/10.1080/13504851.2015.1047084), *Applied Economics Letters* 23 (2016).
- U.S. Census Bureau, [public state-finance timeseries archive](https://www2.census.gov/programs-surveys/state/data/api_dataset/GOVSSTATEFINTIMESERIES.zip) and [technical documentation](https://www.census.gov/programs-surveys/state/technical-documentation.html).
- National Conference of State Legislatures, [fiscal year 2027 state budget status](https://www.ncsl.org/fiscal/fy-2027-state-budget-status).
- The American Presidency Project, [2020 Democratic Party Platform](https://www.presidency.ucsb.edu/documents/2020-democratic-party-platform).

*The audit is constructed from publicly accessible sources without paid APIs. Passing the repository CI confirms recomputation and structural gates, not that all substantive historical judgments have been independently adjudicated.*
