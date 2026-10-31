# Institutional decay — UK accountability and US service records (2026-10-31)

**Evidence status:** additive, official-source-verified descriptive records. **Not** a causal study, nationally representative misconduct rate, harmonized panel, or public-facing redistricting feed. Structured data: [UK/US cases](../../data/institutional-decay/uk-us-accountability-service-2026-10-31.json). Validation: [standard-library regression tests](../../tests/test_institutional_decay_uk_us_cases.py) and [path-scoped CI](../../.github/workflows/validate-institutional-decay-uk-us.yml).

## Accountability — United Kingdom

The [Commons Standards Committee's 26 October 2021 report](https://committees.parliament.uk/committee/290/committee-on-standards/news/158246/committee-on-standards-publish-report-on-the-conduct-of-rt-hon-owen-paterson-mp) found Owen Paterson breached parliamentary rules on paid advocacy, declarations and facilities, and **recommended** a suspension of **30 sitting days**. This was a parliamentary standards finding, not a criminal judgment. The [Commissioner's report appendix](https://publications.parliament.uk/pa/cm5802/cmselect/cmstandards/797/79704.htm) dates the inquiry notice to **30 October 2019**. On **3 November 2021**, the House [amended the motion](https://commonslibrary.parliament.uk/research-briefings/cbp-9359/) and did not approve the recommended suspension. Paterson announced resignation on **4 November 2021**. Do not present the recommended 30 sitting days as a sanction served.

To avoid selecting only a non-imposed recommendation, the [Commons Standards Committee's 29 May 2024 retrospective, Annex 3](https://publications.parliament.uk/pa/cm5804/cmselect/cmstandards/247/report.html), provides two contrasting **House-approved** cases: Andrew Bridgen's **five sitting days**, approved **9 January 2023** following the **3 November 2022** committee report and dismissed appeal; and Margaret Ferrier's **30 days**, approved **6 June 2023** following the **30 March 2023** report and dismissed appeal. The retrospective records subsequent recall in Ferrier's case. **Thirty days** and **thirty sitting days** are not automatically equivalent. This is a deliberately selected case comparison, not an exhaustive denominator or comparative sanction-severity analysis.

## Objective service measures — United States

The [US GAO High-Risk Series, GAO-25-107743, published 25 February 2025](https://files.gao.gov/reports/GAO-25-107743/index.html) reports agency-sourced operational indicators with mixed directions:

- **SSA initial disability claims:** average processing time **184 days (FY2022)** versus **231 days (FY2024)**; pending initial claims **about 941,000** versus **about 1.2 million**. In contrast, pending SSA appeals **decreased from about 347,000 to 262,000**. Pending inventories are snapshots, not numbers of people or completions.
- **VA PACT Act completed claims:** mean processing time **about 155 days (August 2023)** versus **about 168 days (November 2024)**; completed within 125 days **47% (September 2023)** versus **37% (November 2024)**. The earlier processing-time and timeliness observations are from **different months**.
- **VA November 2024 comparison:** non-PACT claims averaged **129 days** with **59%** completed within 125 days; all initial claims averaged **about 139 days**. Do not average subgroup means without counts or equate PACT/non-PACT case mix.
- **VA June 2024 hearing-option appeals:** average **1,089 days**, versus a **730-day goal**. Goal is a target, not an observed result. VA disability-claim backlog stood at **about 244,000** in December 2024, a substantial improvement versus the GAO-described peak of **over 600,000** in March 2013. Rounded quantities remain marked approximate.

GAO's report synthesizes agency data: these are **official audit-reported secondary agency measures**, not newly retrieved individual claim records. Underlying denominator counts for some completion percentages are absent from the cited passage. No agency metric proves elite misconduct or predicts national trust by itself.

## Provenance and permissions

- **UK Parliament:** [Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright/open-parliament-licence/). Attribution retained in the structured source catalog: *Contains Parliamentary information licensed under the Open Parliament Licence v3.0.* Published parliamentary facts are adapted, not copied in bulk; exclusions for personal data, logos, third-party rights and broadcasts are respected. No endorsement implied.
- **US GAO:** [Copyright and Terms of Use](https://www.gao.gov/copyright) states GAO products are generally not protected by US copyright, with third-party material and endorsement caveats. Only attributed numerical facts and short summaries are reused; no figures or photographs reproduced.
- **Validation design:** 19 numeric observations, 10 dated events, five source catalog records, unique IDs, source URLs, licence evidence, per-observation populations/denominator cautions, precision flags, distinct statuses for allegations, committee findings, recommendations, approved sanctions, audits and targets, and no causal inference. A path-scoped GitHub Actions workflow runs Python standard-library tests; the execution outcome must be separately checked, not inferred from a commit.
- **Isolation:** No changes to `data/app-feed.json`, redistricting ingestion, or production UX. Existing Australia/Canada evidence and baseline are preserved.

## Unresolved scientific limitations

No recruited randomized sample, harmonized individual-level trust microdata, causal counterfactual, full UK disciplinary case denominator, or reconciled US agency claims-level denominator. Selected cases are illustrative; no comparison of national corruption rates, causal effect on trust, or inference of guilt from association is warranted.
