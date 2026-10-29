# Census state-finance source-code integrity audit (2000–2015)
Updated 2026-10-29. **Observed source facts only; no spending or election-cycle inference.**

## What has actually been ingested
The original public U.S. Census Bureau state government finance **state-only** files for FY 2000–2015 were retrieved from [the official /govs/state archive](https://www2.census.gov/govs/state/). The raw byte SHA256 for each source, original vintage, observed fixed-record width, Census government code, item code, numeric-as-published text, date/vintage fields, and origin are retained in `data/fiscal/state-legacy/fyYEAR.json`.

The validated archival index lists **16 official annual source files**, all with 50 state governments. The source-code collector preserves 65,554 original F/G/K-character item rows and 66 explicit missing-value markers. This count does **not** equal the number of construction projects, capital allocations, or independent non-overlapping expense observations. The source code rows cannot by themselves determine investment efficiency or government intent. See `data/fiscal/state-legacy/index.json` and derived `quality-audit.json` for exact counts and per-vintage source hashes.

## Nonadditive category crosswalk — primary hazard

The [Census Government Finance and Employment Classification Manual](https://www2.census.gov/govs/class/classfull.pdf) identifies:
- F — Construction.
- G — Purchase of land and existing structures **during initial state-government compilation**. In computer/tabular statistics, G may become *capital outlay other than construction*, incorporating K equipment values.
- K — Purchase of equipment; when G is broad, **K is a nested subcategory of G**.

As a result, **F + G + K may double-count K**. Do not estimate `capital_outlay_total` by blindly summing source F, G and K records. An additive definition such as F + broad G is only permitted after exact published item codes and data vintage have been reconciled against official functional/object definitions, missing values, and state-level financial aggregates.

The [2022 State Government Finance technical documentation](https://www2.census.gov/programs-surveys/state/technical-documentation/complete-technical-documentation/statetechdoc2022.pdf) documents an additional break: prior F construction, G land/buildings and K equipment categories were consolidated into a new F capital-expenditures classification. It also changed social-insurance trust accounting. **A raw pre/post-2022 trend is not comparable without a bridge.**

## Additional observable discontinuity

Between archived FY 2012 and FY 2013, F/G/K rows rise from **3,959 to 4,656**, a 697-row / ~17.6% increase in source-code coverage. This is a count of published *code records*, not a 17.6% jump in public investment. Our quality audit flags the change pending investigation of source-reporting scope, functions/item-code availability and revisions. Source rows for 2013–2015 contain 11, 10 and 45 missing markers respectively. Missingness is unknown, not zero.

## Sample and clock definition

The Census state-only finance program is a complete enumeration of the **50 state governments** (no local governments), with heterogeneous agencies and state functions. The Census [methodology](https://www.census.gov/programs-surveys/state/technical-documentation/methodology.html) notes that the Bureau standardizes administrative government records, subjects them to classification and imputation, and warns about nonsampling error. Comparisons of states directly performing local-type functions can therefore differ substantively even where the accounting code is the same.

Fiscal **year labels are not calendar election years**. Before modeling electoral proximity, build a cited state-specific fiscal-year start/end table, the realized election date and constitutionally scheduled election calendar, state government changeover date, budget proposal date and data release vintage. Parliamentary/country election calendars require additional design and should not be pooled into state-year panels as equivalent observations.

## Strict release gates

1. Verify official item-code definitions by year, identify nested G/K and disaggregate class/function code consistently. Permit either properly constructed `construction`, `equipment` or total investment values, not all at once when overlapping.
2. Confirm historical monetary units, numeric scale, revisions and published missing values from period-appropriate documentation. Use state-only denominator matched to the numerator in same vintage.
3. Extend fiscal data from FY 2016 to the most recent completed and officially released fiscal year via authorized Census bulk/API sources. The current 2000–2015 archival subset is not the full proposed 2000–2025 study.
4. Join verified state-level election dates and fiscal-year boundaries; test exposure windows and other states/years/administration covariates. Do not claim a quarterly election-cycle effect from annual-only observations.
5. After independently validated controls and sample availability, pre-register descriptive effects and causal-identification assumptions. Until then, leave spending shares, policy returns and causal coefficients explicitly null.

## Machine-checkable evidence
- [Stored source index](../../data/fiscal/state-legacy/index.json)
- [Derived code-overlap/missingness audit](../../data/fiscal/state-legacy/quality-audit.json)
- [Audit code](../../scripts/audit_state_fiscal_codes.py)
- [Data-quality invariants](../../tests/test_fiscal_code_audit.py)

This report is deliberately free of politician-specific misconduct claims: source-code accounting patterns do not identify motive or decision-makers.
