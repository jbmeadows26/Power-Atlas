# FINAL RESEARCH ASSESSMENT — Hyper-partisanship, Performative Outrage & Legislative Gridlock

**Power Atlas | U.S. Congress | Baseline 100th–118th (1987–2024) with separately censored 119th (2025–2026) | Assessment date: 2026-10-29**

> **Research completion standard:** The *descriptive historical baseline and data-quality assessment* are completed, backed by source-attributed extracts and tests. The proposed *causal research program* is **not** completed; constituent preference linkage, historical co-sponsorship, legislative-stage attrition, classification of Senate cloture by subject, and original rhetoric/FEC event studies remain necessary. A research-ready dataset is not an identified causal effect.

## Executive verdict

1. **Strong descriptive evidence that party-separated roll-call voting rose sharply:** the rate of *strict party opposition* increased from **7.7% to 48.7% in the House** and from **6.3% to 52.1% in the Senate**, between the 100th and 118th Congresses. This measures votes selected for the floor, not political motivation, party instructions, or conformity with the electorate.
2. **Bipartisan cooperation has NOT disappeared:** the 119th-Congress official H.R./S. bill snapshot contains **6,704 bills with at least one active known opposite-major-party cosponsor** among **15,241 classifiable bills**, or **43.99%**. **1,344 of 16,585 bills (8.1%)** cannot be conclusively classified. This single unfinished-Congress snapshot cannot establish a trend or substantive policy cooperation.
3. **Substantive pre-election enactments declined:** per-Congress average fell from **308.40 (100th–109th) to 170.67 (110th–118th)**, a **44.66%** decrease. The 102nd-to-118th comparison is 387 versus 84, a **78.29%** decrease. These are Pew's broad *substantive* laws, not Mayhew-quality landmarks. Packaging into omnibus vehicles changes the interpretation.
4. **Procedural cloture activity rose**, from an average **65.50 to 211.33 motions per full Congress**, or **222.65%**. This is all motions, **including nominations**. It is not a count of legislative filibusters or an independently valid causal explanatory variable in a model of Pew's differently timed pre-election laws.
5. **Attention and outrage must be distinguished:** peer-reviewed work finds sharply higher donations following extreme *viral attention*, but a separate 2026 study of **2.2 million statements** finds personal insults receive more attention **without a measurable average fundraising, election-margin, or legislative-productivity advantage**. These are different rhetorical treatments, populations, and designs—not contradictory findings.
6. **No independently supported global conclusion that politicians systematically prioritize party over constituents or that outrage creates gridlock** can yet be drawn. That requires documented constituent preferences, agenda/committee-stage records, behavior ordering, and credible causal identification.

## RQ1 — Party loyalty versus constituents

**Question:** How much did cross-party legislative behavior decline, and does party explain votes beyond constituent interests?

**Observed measure (high confidence, descriptive):** A roll call qualifies when both major parties have sufficient recorded Yea/Nay votes (minimum 100 per party in House, 20 per party in Senate). Strict party opposition occurs if at least 90% of one party votes Yea and at least 90% of the other votes Nay. It excludes present, absent, paired, and nonrecorded votes. This is *not* party-unity scoring or an individual-level constituent divergence measure.

| Chamber | 100th Congress | 118th Congress | Early mean, 100–109 | Later mean, 110–118 | Later minus early |
|---|---:|---:|---:|---:|---:|
| House | 7.72% | 48.74% | 17.84% | 45.36% | +27.52 pp |
| Senate | 6.29% | 52.12% | 17.79% | 36.43% | +18.64 pp |

Early/later averages use Congresses as equally weighted observations, not individuals or votes, and are sensitive to era selection. The first-dimension mean ideological gap (R minus D) rose in the House from 0.645 to 0.892 and in the Senate from 0.608 to 0.895. These are model-derived member means, not a moral grade.

**Bipartisan participation (snapshot; moderate confidence):** The official source crosswalk identifies 6704 opposite-party-co-sponsored H.R./S. bills. The observed classifiable proportion is 43.99%. Without assigning the unresolved cases, the all-bill proportion is bounded between **40.42% and 48.53%**. The bounds reflect unknown identities, not an inferential confidence interval. The 119th is unfinished; only H.R./S. bills were indexed; a contemporaneous party crosswalk may not reflect the party at sponsorship date. Separately, academic work finds cosponsorship and floor voting need not track together because **leadership controls the agenda**. Research also finds opposite-party cosponsorship is associated with greater individual legislative effectiveness (93rd–114th Congresses).

**Unanswered / falsification:** The original claim that members choose party over constituents is **UNTESTED**. Obtain legislative-issue-specific district/state preferences (ANES, CES/CCES, documented surveys or calibrated MRP), estimate within-member predicted vote choice from party positions versus issue preferences, add bill and member fixed effects and uncertainty. Distinguish preference differences from party position alignment and record agenda selection: bipartisan bills that never reach a vote do not appear in roll-call data.

## RQ2 — Is political outrage rewarded?

**Question:** Does contentious performative communication yield attention, donation increases and primary safety?

**Published findings, different treatments:**

- **Böken, Draca, Mastrorocco & Ornaghi (JEEA, August 2026):** linked 2019–2020 member-level daily Twitter likes and campaign contributions. Reaching the top decile of attention was associated with a ~0.6 percentage-point higher probability of receiving a donation and ~5.3% more donations on the intensive margin. Benefits were highly concentrated among a few widely followed legislators. Authors report limited evidence that returns to attention directly induce an ideological shift on average. **Viral attention is not the same thing as personally insulting opponents.**
- **Jacob, Lelkes & Westwood (PNAS Nexus, March 2026):** coded **2.2 million statements** from the 118th Congress. Personalized insults garnered more media and social attention, but no positive adjusted association with fundraising, electoral performance or legislative activity; extreme rhetoric did not reflect mean constituent partisan animosity. Insult-containing posts averaged 606 retweets versus 244 for policy-critical posts, and 2,369 versus 760 likes. These are descriptive means, not a randomized trial. The study notes partisan differences in this sample; do not extrapolate to every member of either party.
- **Kim, Zilinsky & Brew (Party Politics 2025):** in 2020 Facebook candidate ads, donor-directed appeals were more toxic/negative than voter-directed ones. This supports **audience-specific rhetoric targeting**, not proof that negativity raises donations or induces gridlock.
- **Heberlig, Hetherington & Larson (Journal of Politics, 2006):** link fundraising redistribution and the selection of more ideologically extreme congressional party leaders, suggesting a distinct organizational incentive separate from daily clip virality.

**Verdict:** media visibility rewards for incivility = supported association; concentrated fundraising returns for virality = supported association/credible study design; *average fundraising rewards for personal insults* = not supported in the 118th-Congress observational study; *primary survival benefits* = unproven; *incivility causing a specific blocked bill* = unproven.

**Causal specification still required:** timestamp original posts/remarks, identify initial engagement (not reposted impression totals), classify insults versus policy criticism versus emergency messaging, blind double-code/holdout human audit, difference or event-study within member with day and topic effects, compare donation arrival before/after, FEC refunds and itemization thresholds, media schedule, presidential/news shocks, primary challenger quality and reverse timing of legislative blockage. Report zero outcomes only after verifying reporting completeness.

## RQ3 — Gridlock and legislative productivity

**Question:** Is lawmaking less substantively productive as measured polarization increases?

**Observed:**

- Pew public-law classifications: early mean **308.4**, later mean **170.7** substantive laws **before Election Day**; 44.7% lower in the latter cohort.
- U.S. Senate procedural totals: **65.5** versus **211.3** cloture motions **over each entire Congress**; 222.6% higher. The numerator includes nomination motions and repeated motions on the same issue.
- Time-window mismatch, nomination rule changes in 2013 and 2017, election-year and administrative changes, committee and Senate agenda selection, mega-bills, appropriations and national emergencies prohibit using these counts as a direct causal regression without harmonization.

**Substantive law does not mean landmark law.** Pew codes any real-world effect as substantive, potentially a modest technical change. Add Mayhew or independent, documented importance classification and the Center for Effective Lawmaking's detailed stage-weighted effectiveness data for the House and Senate through the 118th Congress. Consider the number of unique substantive policy provisions in large packages; filter enacted and introduced bills by 12+ issue classes and measure time-in-stage, appropriations deadlines, vetoes and bicameral compromise.

**Institutional explanation under active test (not proven):** agenda-gating (leaders decline floor time), negative agenda power, committee bottlenecks, Senate cloture/procedural requirements, interchamber differences, policy demand, presidential veto threats and strategic electoral incentives may account for differing parts of the gap. Do not equate increasing cloture with increasingly successful filibusters.

## Historical crosswalk — all completed Congresses

**Columns:** strict opposed-party recorded-vote share (House and Senate); Pew pre-election substantive laws; Senate *all-topic* cloture motions across the **entire** two-year term. The differing time windows forbid joint causal estimates.

| Congress | House | Senate | Substantive laws (pre-election) | Cloture motions (whole Congress) |
|---|---:|---:|---:|---:|
| 100 | 7.7% | 6.3% | 388 | 54 |
| 101 | 6.0% | 4.4% | 299 | 38 |
| 102 | 12.2% | 7.6% | 387 | 60 |
| 103 | 20.1% | 17.3% | 324 | 80 |
| 104 | 23.4% | 23.0% | 286 | 82 |
| 105 | 18.4% | 17.0% | 306 | 69 |
| 106 | 16.4% | 29.5% | 344 | 71 |
| 107 | 19.3% | 14.2% | 199 | 71 |
| 108 | 28.4% | 34.1% | 304 | 62 |
| 109 | 26.4% | 24.7% | 247 | 68 |
| 110 | 35.6% | 16.0% | 286 | 139 |
| 111 | 25.3% | 36.8% | 194 | 137 |
| 112 | 43.3% | 20.2% | 143 | 115 |
| 113 | 47.4% | 41.7% | 141 | 252 |
| 114 | 56.7% | 34.1% | 172 | 128 |
| 115 | 53.8% | 41.1% | 206 | 201 |
| 116 | 51.8% | 40.3% | 150 | 328 |
| 117 | 45.6% | 45.6% | 160 | 336 |
| 118 | 48.7% | 52.1% | 84 | 266 |

**119th Congress:** excluded from these completed-term comparisons. Its ongoing 2025–2026 statistics are a partial snapshot, not full-term observations.

## Attribution and quality gates

**Source-of-truth datasets:**
- `data/hyperpartisanship/voteview-party-divisions-v1.json` — derived from Voteview current and per-Congress CSVs; 40 chamber-term slots, **38 of 38 completed slots verified** and 119th appropriately incomplete; 26,401,508 main bulk vote rows processed. Earlier missing values for 114th–117th were traced to inconsistent serialization of party and ICPSR identifiers, now fixed with exact-code normalization and regression tests.
- `data/hyperpartisanship/govinfo-119-bill-cosponsors-v1.json` — GovInfo's 119th H.R./S. BILLSTATUS collection; 16,585 bill records; retains original dated events and withdrawn participation; 1,344 unresolved cross-party classifications.
- `data/hyperpartisanship/baseline-v1.json` — Pew substantive/ceremonial law counts and Senate cloture aggregates, with independent crosswalk to `congress-baseline-v1.json`.
- `data/hyperpartisanship/app-summary-v1.json` — compact, no-private-data mobile UI feed; updated to 38/38 completed periods.

**Confidence rubric:** `high` = reproducible source-attributed descriptive evidence; `moderate` = observational associations with study limitations; `not_identified` = causal or normative conclusion requires missing individual, topic or event-level data. No individual or organization is characterized as corrupt merely because a sponsorship, donation, party position or lobbyist communication exists.

**Sources:**
1. [Voteview historical member/roll-call documentation](https://voteview.com/data); [Voteview polarization series](https://voteview.com/articles/party_polarization).
2. [Pew Research Center, public-law types through October 14, 2026](https://www.pewresearch.org/chart/congress-productivity-continues-to-dwindle/).
3. [U.S. Senate official cloture counts](https://www.senate.gov/reference/clotureCounts.htm); [Senate cloture explanation](https://www.senate.gov/about/powers-procedures/filibusters-cloture.htm).
4. [GovInfo BILLSTATUS bulk source](https://www.govinfo.gov/bulkdata/BILLSTATUS/119).
5. [Harbridge, Congressional Agenda Control and the Decline of Bipartisan Cooperation (2010)](https://www.ipr.northwestern.edu/our-work/working-papers/2010/ipr-wp-10-11.html).
6. [Harbridge-Yong, Volden & Wiseman, The Bipartisan Path to Effective Lawmaking (2023)](https://doi.org/10.1086/723805).
7. [Böken et al., The Returns to Viral Media (2026)](https://doi.org/10.1093/jeea/jvag045).
8. [Jacob, Lelkes & Westwood, Entrepreneurs of Conflict (2026)](https://doi.org/10.1093/pnasnexus/pgag038).
9. [Kim, Zilinsky & Brew, Donate to Help Us Fight Back (2025)](https://doi.org/10.1177/13540688241235901).
10. [Center for Effective Lawmaking legislative effectiveness datasets (93rd–118th)](https://thelawmakers.org/data-download).
11. [Lugar Center–Georgetown bipartisan index methodology](https://www.thelugarcenter.org/ourwork-44.html).
12. [Heberlig, Hetherington & Larson, The Price of Leadership (2006)](https://doi.org/10.1111/j.1468-2508.2006.00485.x).

## Final answers, without overclaiming

**RQ1:** Strong floor-partisanship increase confirmed; opposite-party bill sponsorship continues; a long-run co-sponsorship decline and party-versus-constituent dominance are not shown by the current panel.

**RQ2:** Visibility incentives around personal attacks are supported; extreme virality can yield concentrated small-donor returns. Neither a generic financial payoff to insults nor greater primary survival is established, and this research does not prove that sensational rhetoric *causes* legislative gridlock.

**RQ3:** Fewer substantive enacted laws and greater overall Senate cloture activity confirmed descriptively. Exactly how much gridlock is caused by polarization, agenda control, the filibuster, social platforms or fundraising cannot yet be allocated quantitatively without aligned event-level data.

**Bottom line:** The empirical hypothesis that American congressional politics has shifted toward more partisan floor conflict and slower legislative throughput is strongly corroborated. A universal story of *party over country*, a uniformly lucrative *outrage machine*, and a single cause of gridlock is **not established**. The stronger mechanism hypothesis is that **party-driven floor selection and media visibility compete with surviving bipartisan policy cooperation**, while multiple procedural and electoral institutions shape what becomes law. This is a falsifiable framework, not an accusation against one party.

## Remaining work — explicit research limitations, not missing source fixes

- Complete 100th–119th sponsor/cosponsor historical panels with **party-at-date**, committee/floor transition histories, same-issue companion bills, withdrawals and an identity resolution quality audit.
- Match bill-level rollcalls against **measured constituent issue preferences** and track whether differences vary by party, committee, leadership or election timing.
- Separate nomination motions from legislation in Senate cloture and align all stage counts to a common pre-election or full-term window.
- Estimate substantive **landmark/provision-weighted lawmaking**, stage attrition and the health of low-salience FAA, defense, agriculture and technical legislation.
- Collect primary-election outcomes, individual time-stamped media material and FEC donation receipts, and conduct blinded rhetoric coding and event-study/negative-control tests.
- Test competing model predictions and interventions; include sensitivity to party/chamber changes, omitted issues, macroeconomic shocks, social-platform ranking changes and lawmaking distribution.
- **Production delivery:** research tab code passed frontend checks but the Vercel project is not live. The project's 100 free API deployments/day quota previously blocked new production release; GitHub Pages was unavailable to the current integration because Pages administration was not authorized. The one-time free-retry workflow exists but **future deployment success must be independently verified**. No paid plan or bypass is represented as approved.

**Status:** descriptive study complete; corroborating literature assessed; **causal research incomplete**; source exports and internal computations reproducible; live web deployment unverified.
