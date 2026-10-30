# Real U.S. gubernatorial fiscal-election associations, 2012–2024

**Power Atlas · October 30, 2026 · Actual-source econometric diagnostic, NOT an identified causal estimate**

The completed six-specification two-way fixed effects analysis uses real, linked U.S. Census, BEA, BLS and sourced gubernatorial election-period data. This is the **first actual observed-data regression** for the Power Atlas campaign-promise / electoral-short-termism track. Its key outcome is annual state direct capital outlay divided by direct expenditure. Any election-driven reductions remain *unproven*; in these analyses the coefficients are generally positive.

| Model | N | Election-FY association, percentage points (95% CI) | Pre-election FY association, pp (95% CI) |
| --- | ---: | --- | --- |
| FY2012–24, state and year fixed effects | 650 | +0.190 [−0.052, +0.433] | +0.288 [+0.081, +0.494] |
| FY2012–24, FE plus lagged real GDP growth and unemployment | 650 | +0.199 [−0.034, +0.433] | +0.277 [+0.061, +0.493] |
| Same, plus potentially endogenous contemporaneous federal transfers (sensitivity only) | 650 | +0.214 [−0.015, +0.443] | +0.296 [+0.072, +0.520] |
| FY2012–21 only, state and year fixed effects | 500 | +0.176 [−0.108, +0.460] | +0.313 [+0.027, +0.600] |
| FY2012–21 only, FE plus lagged macroeconomic indicators | 500 | +0.170 [−0.106, +0.445] | +0.286 [−0.005, +0.577] |
| Exclude FY2020–21, FE plus lagged macroeconomic indicators | 550 | +0.232 [−0.059, +0.523] | +0.283 [+0.025, +0.540] |

**Interpretation:** The estimated election-in-fiscal-year associations are positive but their intervals cross zero across specifications. The pre-election coefficients are also positive in most specifications, yet the 2012–21 controlled interval also crosses zero. Neither a general causal election-year investment decline nor a causal increase has been established. Significance tests across six specifications and two indicators are exploratory; multiple comparisons further limit inferences.

## Verified source and model ledger

Original state fiscal source: U.S. Census Bureau State Government Finances time-series public ZIP, SHA256 **888dfbb3f8eeebce01b409e4e86178ac04c596c7fc355047beef2433a9b5be48**, for **650 state-year observations and 3,250 official expenditure aggregates**. The capital-outlay share is official Census SF0178 divided by SF0175; both are reported in thousands of nominal dollars. Data: [official finance panel](../../data/fiscal/state-timeseries/aggregate-capital-2012-2024.json).

Election sources: [National Governors Association gubernatorial election record](https://www.nga.org/governors/elections/), [Ballotpedia historical governor schedule](https://ballotpedia.org/Governor), [NCSL on off-cycle state elections](https://www.ncsl.org/elections-and-campaigns/consolidating-election-dates) and [Oregon's 2016 special gubernatorial election](https://ballotpedia.org/Oregon_gubernatorial_special_election,_2016). The generated [168-event election calendar and 650-row fiscal join](../../data/fiscal/state-timeseries/governor-elections-fiscaljoin-2012-2024.json) explicitly labels **secondary-source dates and provisional backcast fiscal-year boundaries**.

Actual controls: 50 state real GDP BEA annual series, accessed via FRED, one series per state with the two-letter state abbreviation followed by RGSP; 50 state BLS monthly unemployment series, two-letter abbreviation followed by UR. For each outcome FY, the growth rate and unemployment average are taken from calendar year FY-minus-2; BEA growth uses FY-minus-3 as its comparison. Source CSV URLs and byte-level SHA256 values are in [the 650-record state economic control dataset](../../data/fiscal/state-timeseries/economic-controls-2012-2024.json). The current FY federal general intergovernmental revenue share is Census SF0004 divided by SF0002; this variable **is contemporaneous**, may be a mediator and is not certified as pre-treatment.

Reproducible [model implementation](../../scripts/analyze_state_election_association.py) uses statsmodels OLS with state and fiscal-year fixed effects and state-clustered covariance, small-sample correction. For each fiscal year a governor-election dummy records whether the decisive election took place within the provisional fiscal window; a distinct indicator measures an election in the following fiscal year. Every number above comes from actual state spending, election summaries and source-linked economics, never from the synthetic TWFE architecture test. Source-linked [full numerical model output](../../data/fiscal/state-timeseries/governor-election-fiscal-associations-2012-2024.json) retains exact coefficients, confidence intervals and p-values.

## What limits the validity of these findings

1. **Fiscal clock and exposure:** Many states hold November elections in the fiscal year ending the next calendar year; for example a November 2024 election falls in FY2025 for a July-to-June state, outside these FY2012–24 outcomes. Historical fiscal-year legal boundaries still require state-by-state verification. The election data reflect secondary research summaries, not an audit of all state-certified canvasses. The 2012 Wisconsin recall is excluded from regular election exposure; Oregon 2016 and Louisiana's primary/runoff dates are special cases.
2. **Outcome accounting:** The Census 2022 classification changes can cause state-specific discontinuities that year fixed effects cannot repair. Models restricted to FY2012–21 avoid this particular cross-regime jump, but do not identify causality.
3. **Confounding, anticipation, and policy timing:** Gubernatorial cycles are periodic rather than randomized and may track budget cycles, term limits, partisan control, policy commitments, macro shocks or administrative capacity. A November election usually sits part-way through a fiscal year, and outlays can reflect budgets from the previous administration. No validated lead/lag pre-trend designs or independent exogenous election-date instruments are yet available.
4. **Controls:** BEA and BLS annual lagged records are from later-revised datasets; their public information vintages at the actual budget-adoption dates are unconfirmed. Federal transfer shares are from the same fiscal year as spending and are omitted from the main adjusted model, appearing only as an endogenous sensitivity.
5. **Measurement:** Capital outlay as a proportion of direct expenditure is not long-term capital quality, completed infrastructure, actual social return, or voter-targeted short-term transfers. When total direct spending rises sharply, the capital share can decline without much change in the real capital spending level.
6. **Political intent:** A fiscal association cannot show deception, fraud, planned abandonment or individual officials' intentions. Independent original campaign pledge denominator adjudications also remain incomplete.

**Disposition:** The actual six-model observational analysis is complete and reproducible. A verified *causal* electoral-short-termism estimate is **not established**. Under the candidate exposure definition, the observed negative-capital-spending hypothesis is not supported in the first regressions; this observation is not a universal absence-of-effect proof and should not be conflated with successful campaign pledge adjudication.
