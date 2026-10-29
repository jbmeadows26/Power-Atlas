# Institutional decay — causal validation protocol (v1.0, 2026-10-29)

**Status:** Ready-to-analyze experiment protocol and simulated-method validation only.
**The N=3,000 representative experiment has not been fielded, and the longitudinal feedback mechanism has not been causally identified.** No actual respondent outcomes, randomized assignment history, incentive payments, ethical approval, or consent records are present in Power Atlas.

## A. Confirmatory 2×2 factorial study

**Target population:** US civilian adults aged 18+, recruited under a documented sampling plan. If a non-probability online panel is used, describe it as quota-matched or weighted, NOT literally probability-representative. Recruitment, consent, fielding, weighting, attrition tracking and privacy review must be performed before declaring the study complete.

**Sample:** N=3,000 planned, 750 randomly assigned per treatment cell, with preregistered replacement policy, strata and attrition target. Actual precision depends on population outcome variance, response patterns and weights. Rough *planning illustration*: if SD is 1.5 trust-scale units and allocation is balanced with complete data, normal approximation gives a two-sided 80%-power minimum detectable 2×2 interaction of about 0.31 points on the 1–7 scale (1.5 × sqrt(4/750) × (1.96 + 0.84)); no pilot variance or design effect has been verified. This does not imply 3,000 respondents can be recruited at zero cost.

### Treatment and measurement

All respondents receive the same baseline description of a hypothetical public service and the same conduct-severity facts about a public official. Randomize independently:
- **A: Impunity = 1**: an independent inquiry substantiates an ethics violation, but the normally prescribed consequence is not applied without a stated lawful justification.
- **A: Impunity = 0**: an independent inquiry substantiates the same violation and imposes the prescribed sanction under due process.
- **B: High burden = 1**: completion requires repeat contacts, multiple forms and a 45-day documented delay.
- **B: Low burden = 0**: the same request uses a single form and is resolved within two days.

Neither branch should manipulate facts unrelated to accountability or burden (severity, party, government efficacy beyond that specific service, emotional wording). Pilot for equal comprehension and credible controls. A hypothetical sanction is not evidence that a real named official committed misconduct. Vary randomized statement order or hold fixed, but preregister it.

Primary outcome: post-vignette national-government trust on 1–7 scale. Secondary outcomes (separately defined) are trust in civil service, procedural fairness, perceived legitimacy, self-reported willingness to use services and democratic commitment, with multiplicity control if used inferentially. Capture baseline trust **before treatment** for precision adjustment in a secondary ANCOVA; never adjust for post-treatment perceived fairness if estimating the total effect, because it may be a mediator.

**Prespecified saturated OLS model:**

`Trust_i = beta0 + beta1*Impunity_i + beta2*HighBurden_i + beta3*Impunity_i*HighBurden_i + error_i`.

With (A,B) encoded 0/1, the interaction is
`beta3 = mean11 - mean10 - mean01 + mean00`.
A negative beta3 is consistent with burden having a more adverse effect under impunity than under accountability. Significance must be judged against the preregistered confidence interval and sampling assumptions; one negative p-value does not establish external validity, a real-world feedback loop, or citizen behavior.

The accompanying **[factorial analysis script](../../scripts/institutional_decay_factorial.py)** uses the exact saturated OLS coefficients and HC3 heteroskedastic-robust variance; the latter exploits within-cell leverage 1/n. Accepts `--input` with CSV columns `impunity,high_burden,trust_score`. Blank outcomes are counted as assigned but missing and never silently imputed. `--input` without actual consented fieldwork must not be described as real empirical evidence. Full respondent data should remain private; aggregate/anonymized results can be published only after an ethical/privacy and reidentification check.

**Additional analysis requirements:** randomization balance, assignment fidelity, manipulation checks, proportion missing by arm, attrition bounds, preregistered exclusions, robust alternative ordinal model, pre-treatment covariate adjustment and survey weights for population generalizability. Cluster-robust errors are necessary if assignment or recruitment is clustered. Avoid post-selection significance fishing. If no valid recruitment channel is connected, publishing code does not recruit respondents.

## B. Longitudinal feedback mechanism: data and estimator eligibility

The source-backed trust dataset contains **407 country × year × institution measurement cells**, from 39 countries and mostly two years (2023 and 2025), not 407 country-period observations suitable for an Arellano–Bond dynamic panel. OECD also has a limited 2021 survey cohort, but that is **not included as a compatible annual observation in the current dataset**. There is no reliable 2010–2026 yearly OECD trust series; interpolation is explicitly prohibited.

The proposed model's `rho` on lagged trust measures *persistence*, NOT a causal feedback loop from distrust to lower government capacity. Establishing feedback requires both directions and credible temporal separation:

`Trust_it = rho_T*Trust_i,t-1 + beta_B*Burden_i,t-1 + beta_A*Accountability_i,t-1 + countryFE + timeFE + error_it`

and

`Burden_it = rho_B*Burden_i,t-1 + theta_T*Trust_i,t-1 + controls + countryFE + timeFE + noise_it`.

Even jointly estimated temporal associations need external shocks, exogenous instruments, or stronger identification before interpreting `theta_T` as a causal effect. Trust is often measured from survey perceptions, whereas administrative burden must ideally use actual citizen waiting times, repeated contacts, reversals and appeals; generic public digital maturity or WGI government-effectiveness scores are not substitutes.

Arellano–Bond difference GMM requires usable real consecutive or uniformly spaced lag histories, many independent units and credible sequential moment restrictions. At least three waves may permit extremely sparse differenced moments mathematically, but **the current effective T=2 cannot even construct the dynamic estimator**, and a small, heterogeneous three-wave country panel would still be a poor basis for robust inference. A credible implementation must specify predetermined/endogenous/exogenous status for every regressor, limit collapsed instrument count, and report Arellano–Bond AR(1)/AR(2), Hansen/Sargan (with appropriate caveats), instrument count relative to country count, and sensitivity to lag-depth and measurement error. See [Arellano-Bond and instrument proliferation discussion](https://doi.org/10.1177/1536867X0900900106).

**Unsupported substitutions:** World Bank *Doing Business* was discontinued in 2021; GovTech Maturity Index measures digitization capacity and uses non-annual waves, not citizen-level administrative friction. WGI or V-Dem indicators may support separate institutional-capacity work only after definition, version, year, scaling and uncertainty reconciliation. Their 0–100, ordinal, and −2.5…+2.5 scales cannot be merged without a defensible measurement model.

The [pure-Python one-step difference-GMM demonstration](../../scripts/institutional_decay_gmm_demo.py) generates artificial panels with independently known true autoregressive and regressor coefficients. It illustrates moment mathematics, **not an estimator with applied inferential diagnostics**. Without `--simulate`, it returns `not_estimable` for the real OECD trust extract. There is no 'verified feedback cycle' finding.

**Alternative feasible next study:** use existing 2021/2023/2025 OECD repeated cross-sections only for transparent descriptive robustness; use national administrative sources with true annual service records and independent trust fieldwork where they exist; consider event studies around plausibly exogenous service failures and documented sanction decisions. Pre-register link keys, field dates, negative controls, source eligibility and observable comparison groups.

## C. Deployed frontend: architecture and verification boundary

**Actual stack:** GitHub `site/index.html`, a static, single-file JavaScript/HTML dashboard, not Next.js or React/Recharts. The official Vercel project's recent attempted deployments were canceled at the time of implementation. No upgrade or paid deployment has been authorized.

Implementation uses an inspectable static API-like JSON file, [`site/api/trust-metrics.json`](../../site/api/trust-metrics.json), derived from the OECD rounded country-level table and retaining all 407 non-null cells, 39 country rows and explicit missingness. The read-only [`site/institutional-decay.js`](../../site/institutional-decay.js) computes Pearson correlations from the visible 2025 values and 2023–2025 differences in the browser. The visualization includes country SVG scatter points, chart accessibility labels, an accompanying table, proper denominators, data provenance and the causal limit.

**Deployment success gates:**
1. Commit source with unchanged redistricting feed, unique tab/panel markup and no new paid dependency.
2. GitHub Actions `validate.yml` passes dataset-to-UI mapping, source non-null cell count, external JS syntax, synthetic GMM guard and factorial arithmetic tests.
3. GitHub frontend syntax workflow passes. This existing workflow checks exactly one inline script; the external script is dynamically loaded so it does not alter its inline-script assumption.
4. Verify that a **new production deployment** is READY and serves the new tab and JSON, not merely that the GitHub source changed. A deployment in CANCELED or BLOCKED status is **not success**. The GitHub Pages workflow is manual and may require an authorized repository admin to enable Pages; do not claim live availability without independent proof.
5. Display 'descriptive trust association', not a causal claim or verified impunity ranking. Do not label a source-backed Markdown report as a PDF.

## Final study status

- **Verified:** published OECD trust extracts, distinct political/administrative cross-national correlations, three primary-source case events and curated integrity implementation gap observations.
- **Code complete in repository:** repeatable descriptive comparisons, pilot-ready 2×2 analysis with input guard, synthetic-only GMM demonstration, static scatterplot feed and source-linked frontend.
- **Not complete:** a representative N=3,000 randomized field experiment, causal longitudinal feedback identification, a complete comparable PII/agency-burden country panel, or proof of READY production deployment.

For a legitimate scientific finding, the conclusion remains: both unfairness and poor state performance are potentially damaging, but a *superadditive interaction* and self-reinforcing trust/capacity cycle have not yet been estimated from valid empirical data.
