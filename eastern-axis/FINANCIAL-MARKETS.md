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
