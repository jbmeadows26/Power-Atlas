# Political Authenticity — six-component implementation and evidence ledger
**Evidence cutoff: October 30, 2026.** **Research status: partially empirically observed, not a completed causal study.**

## 1. RQ1 — elite distance and individual alienation
- **Observed:** Congress roster 539 birth-date matched member records, 433 voting House members in October 2026; 2024 national age-population comparison, *cross-vintage and resident-based*, not a causally identified comparison.
- **Observed public opinion:** ANES 2024 full-release codebook variables `V242200` and `V242201`: 3507/4928 (71.1648%) and 3153/4932 (63.9294%) agreeing with alienation statements, respectively. **Unweighted observed item-level response percentages**, not nationally weighted survey estimates. Sources: https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/hcbk0040.htm and https://electionstudies.org/data-center/2024-time-series-study/
- **Implemented:** `scripts/rq1_gee.py`, privacy/consent/weights/geography checks in `tests/test_authenticity_rq1.py`. This is weighted district-cluster **GEE, not the originally requested random-intercept mixed-effects model**. No observed regression has run.
- **Unfilled:** member wealth intervals, member-level occupations and self-reported education, approved SFI calibration, permissioned district-coded survey microdata and geographic mapping. ZIP+4 respondent matching is not an acceptable default; Cook PVI may be licensed.

## 2. RQ2 — calculated rhetoric and factorial experiment
- **Implemented:** `scripts/rq2_corpus_metrics.py` with observed lexical hedging metrics and three-coder Fleiss kappa, aligned to 10 binary codes and requiring a second original URL to substantiate contradiction coding; `tests/test_authenticity_rq2.py`.
- **Preregistered design, not fielded:** `data/research/political-authenticity/rq2-factorial-preregistration.json` documents 2x2 protocol, N=2400 target, 600 per arm and original fictitious comparison stimuli.
- **Unfilled:** 1000 primary-source communications with full rights/provenance and three independent human annotations; consented U.S. sample, ethics review, respondent data and actual causal estimates. A script or a plan does not count as participants or human annotations. Speech metrics do not prove internal polling origins, dishonesty or motivation.

## 3. RQ3 — substantive responsiveness by income tercile
- **Observed official source evidence:** 127 of House Clerk rolls 001-150 from 2025, 23 uncollected, 54,933 recorded vote entries from 437 distinct legislators. Totals: 37,291 Yea, 15,194 Nay, 447 Present and 2,001 Not Voting; no duplicate legislator-roll entries or invalid labels in persisted coverage audit.
- **Implemented:** `scripts/collect_authenticity_rollcalls.py`, `scripts/rq3_responsiveness.py`, parser/provenance tests, source SHA-256 and offline selection-manifest gates. Official rollcall collector: `.github/workflows/verify-authenticity-evidence.yml`.
- **Unfilled:** adjudicated **150 key substantive votes** (the first 150 numbered rolls are not a key-vote sample), and pre-vote district-by-issue preferences for bottom/middle/top **income terciles** with adequate weighted subgroup counts. No dyadic income coefficients have been estimated; positive coefficient differences alone would not identify causal favoritism.

## 4. IDI
- **Implemented and tested:** `scripts/idi_research_gate.py` and `tests/test_authenticity_idi.py` implement `0.25 W + 0.25 O + 0.35(1-S) + 0.15 C` with complete-case guard, bounded uncertainty and zero versus unknown semantics.
- **Actual output:** `data/research/political-authenticity/idi-synthetic-results.json` contains **fictional examples only**. For supplied first two synthetic rows: 0.8105 and 0.1520. No second cohort-normalization and no actual representative score.
- **Unfilled:** defensible source/uncertainty-calibrated observed components, externally reviewed fixed anchors, construct validity and weight sensitivity on real data. District economic conditions must not imply a member caused poverty.

## 5. GitHub CI and evidence hashes
- **Independently observed:** `data/health/political-authenticity-tests.json` records actual GitHub Actions execution success at commit `9e0402e1af18816aeb84d7241196bfeceb8ba662`, with SHA-256 of each calculator/analysis script, UI module and synthetic output.
- **Source workflow receipt:** `data/health/political-authenticity-ci.json` records the separate official House XML collector as a **partial** 127/150 ingestion, not falsely complete.
- **Meaning:** successful tests + byte-identity hashes confirm execution and deterministic integrity within scope, **not** human research, source truth, independent peer review or causal identification.

## 6. Production
- **Deployed:** Vercel project `power-atlas-research`, production deployment `dpl_B8JspWXjG7EXTou26JQwVXToYezb` for commit `71ebf108e6a7ef96c0e76729f1f8324b50664933`.
- **Vercel state:** `READY`, no alias error; aliases include https://power-atlas-research.vercel.app/.
- **Verified deployed source:** that exact commit contains `site/index.html` with the external `political-authenticity.js` module and the corresponding JavaScript file. **External live-browser rendering could not be verified**, so visual acceptance is not certified.
- **Cost policy:** existing static-site framework retained; no Next.js substitution, no paid upgrade, no attempted rate-limit circumvention.

## Evidence links
- [ANES survey aggregates](../../../data/research/political-authenticity/anes-2024-efficacy-aggregates.json)
- [Congress age comparison](../../../data/research/political-authenticity/age-comparison.json)
- [Official House vote coverage audit](../../../data/research/political-authenticity/house-rollcalls-coverage-audit.json)
- [Official House recorded votes](../../../data/research/political-authenticity/house-rollcalls-2025.json)
- [IDI synthetic output](../../../data/research/political-authenticity/idi-synthetic-results.json)
- [Offline test receipt](../../../data/health/political-authenticity-tests.json)
- [Collector receipt](../../../data/health/political-authenticity-ci.json)

**Publication boundary:** The verified descriptive measurements are publishable with stated universes, missingness and uncertainty. It would be scientifically false to state that the six-component **causal study is empirically complete**, to give individuals a real IDI rating, or to claim a 2x2 experiment happened. Human-subject work requires actual consenting participants and appropriate review; individual-level socioeconomic and preference data require lawful source access and reproducible linkage before estimation.
