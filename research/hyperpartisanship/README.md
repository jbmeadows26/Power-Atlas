# Hyper-partisanship, performative outrage and gridlock — Power Atlas

**As-of 2026-10-29. This is an attributed, descriptive 20-Congress baseline, NOT a causal finding or a claim of complete ingestion.** It is independent of the gerrymandering and institutional-decay tracks; the dataset is **not yet wired into the app feed/UI**.

## Completed reproducible extract

- Files: `data/hyperpartisanship/pew-pre-election-laws-100-119.csv`, `data/hyperpartisanship/senate-cloture-100-119.csv`, `data/hyperpartisanship/baseline-v1.json`.
- Sources: [Pew's substantive/ceremonial public laws, before Election Day](https://www.pewresearch.org/chart/congress-productivity-continues-to-dwindle/), published Oct. 15, 2026; [official Senate cloture counts](https://www.senate.gov/legislative/cloture/clotureCounts.htm), retrieved Oct. 29, 2026.
- Across complete Congresses 100–109, mean substantive laws enacted **before Election Day** = 308.40 per Congress. Across complete Congresses 110–118 = 170.67, **44.66% lower**. The Senate's **whole-Congress** average cloture motions were 65.50 versus 211.33, **222.64% higher**. These have mismatched time cutoffs and are SEPARATE DESCRIPTIVE SERIES, not pooled causal regression observations.
- For 102nd vs 118th, Pew reports 387 vs 84 substantive pre-election laws (−78.29%). Do not equate substantive with landmark.
- 119th is unfinished: Pew 109 substantive + 12 ceremonial through 2026-10-14, Senate 294 motions filed, 294 cloture votes, 247 invoked from live official table retrieved 2026-10-29. Always display these distinct as-of dates; never compare the 119th to a completed term without a matching cutoff.
- Total cloture **includes nominations and regime shifts**; it is not the number of legislative filibusters. Pew's classifies modest technical laws as substantive; counts are not a quality score.
- Rebuild: `python scripts/analyze_hyperpartisanship.py`. Run: `python -m unittest discover -s tests -p 'test_*.py'`. No API key, paid dependency or network request.

## Research questions to answer with proper panels

**RQ1 — Party vs constituents.** Estimate (a) party alignment at member × roll-call level using [Voteview member-vote codes](https://voteview.uga.edu/articles/data_help_votes) with time-varying party membership and neutral controls; (b) dated sponsor/cosponsor cross-party ties using [Congress.gov API] (https://api.congress.gov/); (c) procedural gate transition hazards from introduction to committee, report, floor, conference and enactment with censoring of pending bills. Compare district issue preferences (independently measured with survey/MRP uncertainty) to party positions. **Agenda-gating and endogenous roll-call selection** are fundamental competing explanations. Test technical vs salient issues and compare chambers.

**RQ2 — Outrage economy.** Code original speech/posts for provocation, ordinary policy criticism, policy substance, negative sentiment, fundraising appeals, media impressions and original timestamps. Double-code blind across parties; retain disagreements and inter-coder reliability. Link dated posts to FEC **net** contributions, refunds, committee transfers, district/size bins, race competitiveness and primary outcomes. Study unusual attention with member/event fixed effects, matching, pretrend/placebo tests and post-deadlock reverse-causality lags. Viral attention is NOT equivalent to outrage. Published study: [Böken et al., JEEA 2026](https://doi.org/10.1093/jeea/jvag045), on 2019–20 Twitter attention and donations; not evidence that outrage caused a primary victory.

**RQ3 — Gridlock and productivity.** Beyond count of laws, measure stage elapsed time, unreported bills, committee hearings, House special rules, blocked scheduling, legislation-only cloture, omnibus provisions, government funding deadlines, substance significance, and bicameral negotiations. Distinguish appropriations, defense, FAA, agriculture and other technical policy from high-salience conflict. Benchmark separately against [Mayhew's landmark legislation approach](https://yalebooks.yale.edu/book/9780300142561/divided-we-govern/) but do NOT republish unlicensed classifications. The 2013/2017 nomination precedent changes and 2021 earmark revival affect structural comparisons.

## Actors and evidence protocol

Build an attributed graph linking lawmakers, floor/committee leaders, whip positions, sponsors and cosponsors, FEC committees/donors and *disclosed* transactions, lobbyist registrants/clients and issues, independent expenditures, and verifiable media intermediaries. Edges distinguish relationship, communication, transaction, procedural authority, observed decision and allegations. Wealth, donations, lobbying or angry content alone must not be labeled corruption or proof of vote control. Preserve chronology, uncertainty, source, scope, right-to-reply and adjudicative status; exclude sensitive personal donor addresses from publication.

## Unfinished gates and high-priority next ingestions

1. **Voteview panel:** member × roll call across both chambers (exclude non-votes per documented rules; party-switch crosswalk); raw sources versioned, limit bulk file sizes.
2. **Congress.gov:** dated sponsors/cosponsors + action history by Congress with pagination, dedupe and missing-to-null; correct institutional bill lineage (companions and omnibus).
3. **Senate:** classify cloture by nominations vs legislation, by rule era, per session day; incomplete 119th right-censored.
4. **FEC/social:** harmonize daily donations and platform engagement; report unitemized/suppressed historical data as unavailable, never zero.
5. **Validation:** repeated periods, opposition parties, alternative law classifications, technical-policy controls, bounded uncertainty and placebo timing.
6. **Integration:** add source-linked charts with visible denominators and cutoff dates to Power Atlas after review. Existing app-feed format has *not* been modified.

**Research standard:** Resist assuming either party uniquely responsible; a descriptive trend is not an identified cause. Missing quantitative data, private whip communications and removed social posts remain unverified, not inferred.
