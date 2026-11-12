# Banking & Financial Power — evidence charter

**Status (2026-11-12):** curated first interactive investigation at `platform/unified/banking-power.html`. This is not yet a complete bank-level historical database or current automated data pipeline. Do not label it complete.

## Core question

When financial institutions profit from risk or fail, how are losses, rescues, acquisition gains, consumer charges, and legal accountability distributed among depositors, employees, taxpayers, the Deposit Insurance Fund, banks, shareholders, creditors, executives, and other counterparties?

## Six lines of investigation

1. **How a bank earns money:** net-interest margin, fees, loan origination and servicing, securitization, card interchange, underwriting, trading, private credit and off-balance-sheet risk. Separate lawful pricing from alleged or adjudicated misconduct.
2. **Consumer misconduct:** deceptive account openings, reordering or posting transactions, overdraft and junk fees, unfair servicing, foreclosures, credit discrimination, debt collection, payment-system restrictions, fraud and access to human customer support. Official CFPB, OCC, FDIC, FRB, FTC, DOJ, state-AG order or court record required for a legal-status label.
3. **Crashes and interventions:** bank panics 1929–33, S&L, 1998 LTCM context, 2007–09 failures/TARP/AIG/Fed liquidity, 2020 pandemic credit and 2023 SVB/Signature/First Republic. Explain differences between deposit insurance, lender-of-last-resort loans, asset purchase, equity injection, guarantee, receivership, recapitalization, special assessment and actual fiscal loss.
4. **Beneficiaries and losses:** gross authorizations versus disbursements versus repayments versus recognized acquisition accounting gain versus realized investment return. Identify specific bank purchasers, assets/deposits acquired, lending terms, special assessments and taxpayer/fund exposure, with dates and primary filings.
5. **Political funding and regulatory influence:** finance-linked individual contributions, PACs, independent spending, trade-group lobbying, bank-funded political activity where permitted, issues lobbied on, related bill drafts, committee votes, regulatory consultations and enforcement budgets. Never infer quid pro quo from temporal coincidence alone. Study proposed and effective rules separately.
6. **Who was held accountable:** criminal pleas and convictions, individual regulatory prohibitions/civil penalties, enterprise monetary penalties, consent orders, restitution, settlements (with/without admissions), shareholder lawsuits, clawbacks and open cases. Do not conflate corporate fines and personal imprisonment, and do not treat dismissed/non-pursued allegations as proven.

## First source-verified episodes (curated, not comprehensive)

| Episode | Measured claim | Source | What must not be inferred |
| --- | --- | --- | --- |
| TARP 2008–23 | $443.5B disbursed, $31.1B lifetime net program cost | https://www.gao.gov/products/gao-24-107033 | Gross amount equals final fiscal loss; TARP equals every bailout |
| AIG 2008 rescue | Multi-agency support reached a $182.3B peak authorization; counterparties received collateral/settlements | https://www.gao.gov/products/gao-11-616 | Gross counterparty cash flow equals pure profit |
| S&L crisis | Federal Reserve's narrative of 747 RTC institution resolutions and taxpayer cost | https://www.federalreservehistory.org/essays/savings-and-loan-crisis | Identical modern nominal dollar bases |
| SVB/Signature | Systemic risk exception protected uninsured deposits; failed shareholders were not protected | https://www.fdic.gov/news/speeches/2024/lessons-learned-us-regional-bank-failures-2023 | FDIC payouts are direct Treasury grants |
| FDIC special assessment | Estimated recovery requirement ~ $16.7B, revisable | https://www.fdic.gov/deposit-insurance-assessments/special-assessment-pursuant-systemic-risk-determination | A fixed final taxpayer loss |
| First Citizens / SVB | Preliminary after-tax acquisition gain $9.81B | https://www.sec.gov/Archives/edgar/data/798941/000079894124000018/fcnca-20231231.htm | $9.81B cash grant or realized net return |
| JPMorgan / First Republic | Final bargain-purchase gain $2.9B | https://www.sec.gov/Archives/edgar/data/19617/000001961725000270/R43.htm | Same accounting/tax basis as First Citizens |
| FDIC / First Citizens | $500M equity rights sale proceeds after SVB transaction | https://www.fdic.gov/news/speeches/2023/spmay1723.html | Net DIF resolution total |
| JPMorgan RMBS | $13B civil resolution 2013 | https://www.justice.gov/archives/opa/pr/justice-department-federal-and-state-partners-secure-record-13-billion-global-settlement | Executive criminal conviction |
| Bank of America RMBS | $16.65B civil resolution 2014 | https://www.justice.gov/archives/opa/pr/bank-america-pay-1665-billion-historic-justice-department-settlement-financial-fraud-leading | One cash fine or complete consumer relief |
| Wells Fargo unauthorized accounts | CFPB 2016 and separate former-officer OCC penalties | https://www.occ.gov/news-issuances/news-releases/2020/nr-occ-2020-6.html | Same sanction as 2022 CFPB order |
| Goldman 1MDB | Entity guilty plea + individual jail sentence | https://www.justice.gov/archives/opa/pr/goldman-sachs-charged-foreign-bribery-case-and-agrees-pay-over-29-billion | Automatic implication for entire industry |
| Fed BTFP | Fed credit facility, collateralized and repaid | https://www.federalreserve.gov/econres/feds/the-federal-reserves-response-to-the-2023-banking-turmoil-the-bank-term-funding-program.htm | Loan balance equals public loss |
| Banking industry political influence | OpenSecrets F03 2024 associated donations and lobbying are separate measures | https://www.opensecrets.org/industries/indus?cycle=2024&ind=F03 | Corporate bank contributions directly to federal candidates |
| 2024 overdraft rule | CFPB rule disapproved under CRA in 2025; no force/effect | https://www.consumerfinance.gov/compliance/compliance-resources/deposit-accounts-resources/overdraft-lending-very-large-financial-institutions/ | Political money bought specific votes |

## Source hierarchy

Primary: SEC 10-K/10-Q, EDGAR, bank call reports/FFIEC, FDIC receiverships & annual reports, GAO/SIGTARP, FRB lending disclosures, Treasury/FSOC, DOJ dockets/orders, CFPB enforcement database, FEC bulk filing/candidate records, Senate/House lobbying disclosure and Congress.gov voting records. Secondary: OpenSecrets for *attributed* campaign and lobbying aggregations. Third-party calculations require full methodology.

## Machine-readable case ledger (next implementation step)

Proposed schema: `case_id, institution_id, event_type, program_id, year, event_date, source_date, source_url, amount_nominal, currency, amount_measure, taxes_included, recipient_type, funding_source, ledger_role, status, jurisdiction, personal_named_parties, legal_disposition, appeals_status, confidence, limitation`. A number is never published without its measure, observation date, scope and original source. Add per-bank searchable ledgers only as ingested records are reconciled. Avoid unsupported comparisons.

## QA gates

- Each visual number has a source and correct accounting label.
- No unsupported link between campaign donations and a vote.
- Distinguish open civil case from guilty verdict or sentence.
- Clarify the difference between taxpayer appropriations and FDIC fund outlays/industry premiums.
- Avoid treating consumer complaint volumes as verified wrongdoing rates without denominator/validation.
- Verify every outbound source is accessible; audit all source dates/links.
- Verify keyboard/mobile nav, six crisis choices, expandable legal cards, fee calculator and links to banking story from My Life issue grid.
- Do not publish “complete” until separate 2023–26 filing updates, personal litigation dockets and bank-level aggregation have been performed.
