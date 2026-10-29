# Campaign pledges and electoral myopia — deep-gap audit and identification plan
Updated 2026-10-29. Evidence states are explicit; this document is a study design, not a numerical finding.

## Priority gap audit (fixes required before public scorecards)

| Gap | Why it matters | Resolution | Release gate |
| --- | --- | --- | --- |
| Partial promises conflated with policy attempts | A nationwide $15 minimum-wage promise is not satisfied by a $15 federal-contractor order | Atomize pledges and record separately whether a proposal was introduced, implementation occurred, population covered and whether it persisted | A |
| Unverified source URLs | Some previously imported PolitiFact deep links did not resolve | Remove or replace links with directly retrieved original sources; preserve link-audit notes | A |
| No exhaustive pledge denominator | A hand-picked set of obvious wins or losses gives arbitrary fulfillment rates | Freeze party/candidate and election document inventory; enumerate candidate sentences; independently adjudicate inclusions and duplicates; publish inclusion/exclusion counts | A |
| Intent conflated with observable events | A court ruling, legislative defeat, budget shortage or nonattempt does not prove deliberate deception | Attribute each dated action/constraint by institution; maintain rival causal explanations; do not score dishonesty without direct relevant evidence | B |
| Promise compound clauses | 'Rejoin and reform the WHO' and 'raise the minimum wage and end tipped minimum wages' are multiple testable claims | Preserve parent platform sentence and generate atomic child claims, with linked but independent outcomes | A |
| No durability timeline | Executive restoration can later be reversed by a successor; end-term fulfillment is not permanence | Track first fulfillment, term-end status and current durable status independently | B |
| Source-level copyright and licensing | A public web page is not an unrestricted bulk-text license | Store paraphrase, citations, passage locations and source metadata; seek/confirm authorized access for machine-readable manifestos | A |
| Election calendar endogeneity | Surprise parliamentary elections respond to the political economy and cannot be treated as exogenous | Record scheduled calendar, election announcement, actual poll, dissolution and caretaker dates; separate planned from snap cycles | C |
| Fiscal accounting mismatch | National federal budgets, whole-of-government accrual accounts and local disbursements are not interchangeable | Choose general-government sector for comparisons and verify valuation, time, fiscal year, deflators, GFCF definition, double-counting, and source revision | C |
| Small five-country sample | Annual country panel across five countries has too few independent clusters and differing parliamentary election rules | Primary fiscal test: within-US-state panel using official Census state finance and staggered gubernatorial elections; five countries descriptive/mechanism replication until broader sample | D |
| Salience and announcement timing | Politicians can front-load announcements while capital payments occur later | Four separate clocks: announcement, authorizing act, obligation/contract, realized outlay, asset delivery; do not infer ROI from a press release | C |
| Political accountability feedback | Promises are made to voters but publicity and visibility vary; nonfulfillment may not affect votes equally | Link visibility and comparable election outcomes only after valid crosswalks, and pre-specify electoral outcome models separately | D |
| Sourced blockers and statistical caveats | Unavailable data must not be zero or coded as unattempted | Record unobserved/unknown; report missingness by country, time and policy category; suppress low-coverage percentages | E |

## First concrete pilot evidence (purposive, NOT representative)

- The 2020 Democratic platform explicitly promised to rejoin the Paris Agreement, end specific travel bans, restore Bears Ears protections, pursue Kigali ratification, reengage international institutions, and end the southern-border emergency. Sources: https://www.presidency.ucsb.edu/documents/2020-democratic-party-platform
- The Paris Agreement reentry was effective on February 19, 2021: https://2021-2025.state.gov/the-united-states-officially-rejoins-the-paris-agreement/
- The 2020 plan to withdraw from WHO was rescinded January 20, 2021; WHO membership had not legally ended, and the pledge to reform WHO remains a separate unscored atom: https://www.presidency.ucsb.edu/documents/letter-secretary-general-antonio-manuel-de-oliveira-guterres-the-united-nations
- Proclamation 10141 revoked specified discriminatory travel bans on January 20, 2021: https://www.govinfo.gov/content/pkg/DCPD-202100052/html/DCPD-202100052.htm
- Bears Ears Proclamation 10285 was issued October 8, 2021; a July 13, 2026 successor proclamation substantially reduced reserved monument acreage. These are different time-indexed policy states: https://www.govinfo.gov/content/pkg/DCPD-202100834/html/DCPD-202100834.htm and https://www.whitehouse.gov/presidential-actions/2026/07/modifying-the-bears-ears-national-monument/
- Kigali Amendment Senate advice and consent September 21, 2022, United States ratification deposited October 31, 2022, treaty in force January 29, 2023: https://2021-2025.state.gov/u-s-ratification-of-the-kigali-amendment/ and https://treaties.un.org/Pages/showDetails.aspx?objid=080000028048cd90
- United States elected to UN Human Rights Council October 14, 2021, beginning a regular membership term January 1, 2022; changing council governance is a distinct pledge: https://2021-2025.state.gov/election-of-the-united-states-to-the-un-human-rights-council-hrc/ and https://research.un.org/en/unmembers/hrcmembers
- Proclamation 10142 ended the southern border emergency January 20, 2021; a successor revoked it January 20, 2025: https://www.govinfo.gov/content/pkg/DCPD-202100053/html/DCPD-202100053.htm and https://www.govinfo.gov/content/pkg/DCPD-202500111/html/DCPD-202500111.htm
- Original 2020 Biden candidate promise: nationwide $15 minimum wage. Senate-printed H.R. 1319 included a proposed phase-in; Executive Order 14026 raised the minimum for *covered federal contractor* workers, not all U.S. workers. Nationwide minimum was not enacted during the 2021–2025 administration: https://www.presidency.ucsb.edu/documents/biden-campaign-press-release-fact-sheet-joe-bidens-plan-build-back-better-for-american ; https://www.govinfo.gov/app/details/BILLS-117hr1319pcs ; https://www.govinfo.gov/content/pkg/DCPD-202100345/html/DCPD-202100345.htm ; https://api.politifact.com/truth-o-meter/promises/biden-promise-tracker/promise/1575/increase-federal-minimum-wage-15hour/article/3012/
- The 2020 Republican National Committee did not adopt a fresh manifesto, instead retaining/reaffirming the 2016 platform. Separate candidate agenda material and inherited/obsolete pledge classifications before party comparisons: https://www.presidency.ucsb.edu/documents/resolution-regarding-the-republican-party-platform

## Defining the pledge denominator and unit

1. Freeze a **source manifest** with original campaign date, election date, speaker/party authority, publicly archived URL, version, official/archived provenance and licensing. Separate *party platforms* from *candidate press releases*, TV debates and coalition agreements. Coalition agreements are post-election implementation evidence, not original campaign promises.
2. Enumerate every sentence in in-scope primary texts, recording exclusion reason `noncommitment`, `not_testable`, `already_completed`, `not_attributable`, `outside_jurisdiction`, `duplicate`, `not_campaign_period`, or `requires_manual_adjudication`. Avoid deciding eligibility with an unreviewed AI classifier alone.
3. Atomize verifiable promises into child commitments. Keep parent sentence ID, normalized policy target, quantitative target, deadline, beneficiaries, jurisdiction, required actors, objective/conditional clauses and document offsets. For "rejoin and reform", membership and reform are separate children.
4. Freeze analysis cohort before revealing outcomes. A headline overall rate requires a stated denominator: all eligible pledges of governing parties in completed terms versus all parties including opposition. Do **not** mix incumbents and opposition.
5. Publish both unweighted pledge fractions and transparently specified robustness by salience, specificity and policy area. Unknown reviews are missing, not failures. Present interval estimates where sample design supports inference; do not compute confidence intervals from a purposive pilot.
6. Conduct independent dual coding for inclusion, source chronology, effort, result and attribution; adjudicate differences. Audit the same politicians and policies across multiple source documents to prevent double counting.

## Multi-state electoral short-termism design

**Primary empirical scope, contingent on data completeness:** 50 U.S. states, FY 2000–FY 2024; the 50×25 count is a **possible balanced panel, not an observed count**. Start by identifying individual state government capital expenditures using Census Annual Survey of State Government Finances and pre-2012 historical files: https://www.census.gov/programs-surveys/state/data.html . A 2012–2024 Census API endpoint is documented at https://www.census.gov/data/developers/data-sets/govsstatefin.html but now requires a key; use officially published bulk files where available without bypassing API restrictions. Data are *annual state fiscal years*, not quarterly observations. Since fiscal years differ by state, link each state-year to the precise FY start/end and months overlapping the election.
  
- Outcomes: state direct capital outlay share, capital construction share, transfers/direct-assistance share and education/prevention shares only if Census code definitions support the split. Do not assert investment quality or motive based solely on an accounting category. Use numerator/denominator from the same finance release vintage and government level.
- Clock: gubernatorial election held during state FY, months from budget proposal to scheduled gubernatorial election, years since prior election, and any unexpected special election. New Hampshire and Vermont use shorter gubernatorial cycles; account for institutional exceptions rather than assuming four years for every state.
- Controls: fiscal constraints, revenues, balanced-budget rules, federal transfers, disasters, unemployment, inflation, population, partisan control, legislator turnover, debt and prior election competitiveness. Test whether inclusion of revenue/compositional controls induces overadjustment.
- Main estimand: within-state difference in capital expenditure share between election-proximate and non-election fiscal years, adjusted for state and common-year effects. Pre-estimate covariate balance, outcome support, variation across years and sensitivity to FE/cluster specification.
- Model: `y_s,t = a_s + t_t + sum_k beta_k 1(event_time_s,t=k) + gamma X_s,t + error_s,t`; cluster by state and consider state- or election-level dependence, wild/bootstrap design-based sensitivity and panel serial correlation. Explicitly report actual calendar-year alignment and coverage.
- Separate a mechanism study using actual state budget proposals, appropriations and **cash** capital outlays to distinguish front-loaded publicity from implementation disruption. Annual Census data alone cannot determine within-year "election month" spikes.
- Robustness: omit recessions/pandemic years, presidential-cycle controls, real versus nominal values, function-specific classifications, lead/lag placebo windows, pre-trends, alternative normalizations, no-aggregation bias, state-by-time heterogeneity and leave-one-state-out diagnostics.
- **Do not claim causality** from fixed effects alone; gubernatorial cycle timing may correlate with local political/institutional histories. Pre-register plausible exogenous variants for testing only after examining assignment processes.

## Five-country comparative external validity

US, UK, Canada, Germany and Portugal are a targeted **most-different-systems comparison**, not a 5-country causal election budget model. The treatment is not comparable across presidential fixed schedules, parliamentary snap elections and coalition/single-party executives. Use Comparative Party Pledges Project (Thomson et al. 2017, DOI 10.1111/ajps.12313) as published methodological benchmark. Their reported >20k pledges across 57 campaigns and 12 countries **do not provide** our own total or validated row count. Manifesto Project 2026-1 corpus is available via registration/API key and versioned; the source is not unrestricted free redistribution: https://manifesto-project.wzb.eu/information/documents/corpus

Under matched accounting definitions, use annual **general-government** expenditure data IMF QGFS/Eurostat/OECD. Eurostat COFOG `gov_10a_exp` is an annual **functional** breakdown, not an overall capital investment series; match additional GFCF series separately. Parliamentary election-year analyses must use dates known at the time and exclude unexpected dissolutions from a fixed-time comparison unless modeled separately. Record fiscal data revision dates and election calendars.

## Hypothesis falsification and negative controls

- Electoral *targeting*: visible targeted transfers and credit-claiming announcements rise, with stronger effects in competitive jurisdictions. **Disconfirming case**: no composition shift after controlling for revenue and shock cycles.
- Administrative *capacity*: actual large-project spending falls while payment delays/contract processing lengthen, without necessarily more short-run transfers. **Disconfirming case**: new contracts/commissions are unchanged and expenditure changes reflect accounting relabeling.
- Institutional constraint: lower pledge enactment where effective governing agenda power is smaller; **disconfirming case** after matching on specificity, policy type and implementation timeline.
- Reverse causality/selection: incumbents choose more realistic promises in safe jurisdictions or ahead of favorable economic cycles; control specificity and competitiveness and assess matched pledge types before causal language.
- Policy durability: early executive-only achievements face reversal risk after partisan turnover, but observe repeal/mutation separately from term-end enactment. Avoid conflating successor rescissions with the original officeholder's honesty.

## Inference and access gates

A: primary texts and sampling frame licensed, deduplicated, versioned. B: two independent adjudicators for scored outcomes and dated official actions. C: numeric fiscal source downloaded, government-sector definition harmonized, revisions tracked. D: diagnostics and uncertainty estimates produced from observed data, minimum adequate independent clusters and preregistered model. E: public UI only shows dated evidence, confidence and missingness, with corrections, never unsupported bad-faith allegations.

Existing pilot: eight purpose-selected sources across two files, initially one human-readable review per record; one cannot infer population fulfillment rates or causal budget effects. Candidate queue: 24 additional **unscored** passages, NOT 24 failed/fulfilled pledges. Source registry: catalogs potential sources but records zero downloaded fiscal observations; no analyses until data actually ingested and validated.

## Primary literature and replication

- Thomson et al., AJPS (2017), https://doi.org/10.1111/ajps.12313 — pledges, government power-sharing.
- Drazen & Eslava, Journal of Development Economics (2010), https://doi.org/10.1016/j.jdeveco.2009.01.001 — electoral targeting by composition rather than necessarily aggregate expansion.
- Pierskalla & Sacks, Journal of Politics (2018), https://doi.org/10.1086/694547 — alternative capacity mechanism of capital-expenditure election cycles.
- Census Annual Survey of State Government Finances, https://www.census.gov/programs-surveys/state.html — fiscal panel; **2012–24 API key required**, but publicly available downloadable files exist.
- Eurostat `gov_10a_exp`, https://ec.europa.eu/eurostat/databrowser/product/view/gov_10a_exp — annual COFOG spending by function; not quarterly nor direct project ROI.
