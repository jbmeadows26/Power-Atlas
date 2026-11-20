# Eastern Axis — financial-market early warning

## Scope

- **Risk Watch is the single financial-risk location.** It displays 6 compact market cards, sparklines, source dates, click-through evidence and explicit equity-versus-credit screens. No duplication on Country or other tabs.
- Free-first backend: Python standard library reads individual FRED CSV graph downloads on GitHub Actions (01:17 / 07:17 / 13:17 / 19:17 UTC), publishes a versioned static JSON at \`public/analysis/financial-markets.json\` and lets existing GitHub Pages CI deploy it.
- **This is not a live market terminal.** End-of-day markets update on business days, FRED observations may lag and the St. Louis stress series updates weekly. The frontend flags a collection older than 12 hours; the collector flags stale underlying observations separately.
- Data use and redistribution restrictions vary by **original source**. Cite FRED *and* S&P Dow Jones Indices, Nasdaq, Cboe and ICE, and verify provider licensing before broader downstream reuse. This monitor does not represent that feeds are commercially licensed.
- Primary browser-visible signals are **screening triggers, not risk probabilities**. A market-value change is not cash withdrawn or the realized financial loss of a lender. A spike in VIX is not evidence of default.

## Public market measurements

| Feed | Frequency | Why | Origin |
|---|---|---|---|
| SP500 | Daily | Broad US equities, 60-observation correction and 5-observation declines | S&P Dow Jones Indices via FRED |
| NASDAQCOM | Daily | Technology-heavy equity stress and breadth vs S&P | Nasdaq via FRED |
| VIXCLS | Daily | Options-implied volatility level | Cboe via FRED |
| BAMLH0A0HYM2 | Daily | Broad US high-yield option-adjusted credit spread | ICE Data Indices via FRED |
| T10Y2Y | Daily | US Treasury term spread, not direct default risk | Federal Reserve via FRED |
| STLFSI4 | Weekly | Broader St. Louis Fed financial-stress composite | FRB St. Louis |

Alerts require **fresh** observations and show their rules. A reported \$4T AI valuation wipeout is stored only as a source-dated news **claim** in a clickable dossier, not a fabricated \$4T metric. Credit screens are calculated independently of equity screens. Joint breach triggers an *investigate* prompt, not a declared credit crisis.

## Event dossier, source standards

- Nov 20, 2026 — Anthropic IPO / AI-sector reversal: Reuters and the Wall Street Journal; market-value totals reported, not computed from a constituent universe.
- Nov 20, 2026 — Reported Apollo/Goldman \$44B GPU financing: compare the official announcement and Reuters; investigate financing rate and collateral structure, not a default claim. Reconcile the differently scoped \$32B report before adding tranche totals.
- Nov 2026 — ECB Financial Stability Review: regulatory evidence of potential interconnections among equities, corporate financing, banks and non-bank finance; neither a bank insolvency finding nor a recession forecast.

**Citation URLs are embedded in each event's evidence dialog.** Shared conversations and media headlines are research leads and not independent corroboration.

## Coverage gaps / next connectors

Not observed yet: individual issuer equity prices (ANT, NVDA, semiconductors), options volume and market breadth, futures and pre-market moves, global exchange benchmarks, bond-tranche pricing time series, private-credit loan tapes, guarantees and counterparty claims, lender concentration and realized impairments, household withdrawals and retirement-account impacts, and employment causally tied to an AI revaluation. Authoritative additions would come from SEC EDGAR company disclosures, regulators (Fed, FDIC, ECB, ESMA, BIS), CFTC position reports, BLS payrolls and market data with suitable redistribution rights. **Do not silently treat a source directory entry as an ingested feed.**

## QA

Run \`python -m unittest discover -s eastern-axis/tests -p test_financial_markets.py -v\` then \`npm run build\` from \`eastern-axis/\`. Pull-request CI exercises an actual FRED download without publishing. Main-branch schedule requires at least 3 fresh series to avoid overwriting the last working snapshot with a mostly empty file, but does not hide missing series. After publishing, check the action logs, original observation periods and the deployed Pages asset before calling it live.

## Expansion — household and issuer financial transmission (November 20, 2026)

- Risk Watch now contains **one integrated view**: six US market benchmarks at the top; four source-dated household/credit cards; three supporting labor/savings readings; optional issuer filing drilldown. No duplicate financial dashboard elsewhere.
- Collector: `eastern-axis/scripts/collect_market_transmission.py`, source JSON `eastern-axis/public/analysis/financial-transmission.json`.
- FRED via Fed/BLS/BEA/ICE: `DRCCLACBS` (quarterly credit card delinquencies), `TDSP` (quarterly household debt-service burden), `PSAVERT` (monthly saving rate), `UNRATE` (monthly unemployment), `ICSA` (weekly jobless claims), `DRTSCILM` (quarterly commercial/industrial loan standards), and `BAMLC0A0CM` (daily investment-grade spreads). Original time-series observation dates are shown **even when collection happened today**.
- SEC public EDGAR `company_tickers.json`, `submissions/CIK*.json` and US-GAAP `companyfacts/CIK*.json`: tracked issuer list `ANT, NVDA, MSFT, GOOGL, META, AMZN, ORCL, AMD, AVGO, CRWV`. SEC maps tickers to CIKs; no inferred company mapping on lookup failure. Structured balance-sheet cash/debt facts disclose filing date and XBRL tag.
- Item 8-K `1.03` (bankruptcy/receivership) and `2.04` (events changing debt obligations) are **review queues** and link directly to SEC primary filings. Item `2.03` (new obligations) is financing context **not proof of failure**. Zero matching events only means no item-coded matches in the 120-day sampled issuer index; it does not prove no defaults across private credit.
- No record is treated as a confirmed private credit loss or counterparty guarantee payment without source documents and validation.
- Scheduled GitHub Actions uses Python standard library, bounded HTTP source reads and fail-closed status, and publishes both financial JSON snapshots via GitHub Pages. Missing sources show as unavailable; partial results remain visibly partial.
- Independent warning screens require a source-dated threshold breach: IG credit spread increase >=25 bps between published observations, credit-card delinquencies +0.30 percentage points quarter-on-quarter, or a recent SEC item 1.03/2.04 requiring human filing review.
- A market drawdown and household aggregate deterioration in nearby periods are **not proof of causation** from AI financing or securities losses.

### Incomplete by access/licensing, not silently marked done

- Intraday ticker quotes, 1-minute charts, option order flow and extended-hours prices require an exchange-authorized data provider and public-display/redistribution entitlement; free personal-use API keys do not automatically grant this. The public UI explicitly says `not-connected` until authorized. Never commit keys, scrape protected feeds or present old quotes as live.
- Private-credit loan tapes, borrower covenants, guarantee calls, realized lender impairment and undisclosed debt defaults are generally not public; this is a bounded public filing/credit-spread **proxy**, not complete loan surveillance.
- Household pension/retirement account losses, individual withdrawals and causal employment effects require representative sourced data and cannot be determined from FRED aggregates.
- Source freshness must be checked separately for each cadence; quarterly observation dates are the start of the quarter and cannot be interpreted as date of release.

### Evidence and validation

- US SEC public API docs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC 8-K item meanings: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/how-read-8
- NY Fed Household Debt and Credit (Q3 2026): https://www.newyorkfed.org/newsevents/news/research/2026/20261110
- Federal Reserve TDSP series: https://fred.stlouisfed.org/series/TDSP
- Frontend build + collectors: `.github/workflows/eastern-axis-market-watch.yml`; tests `test_financial_markets.py` and `test_market_transmission.py`. Verify CI and public JSON after merge; do not assume GitHub Actions success implies that the SEC connection is live.
