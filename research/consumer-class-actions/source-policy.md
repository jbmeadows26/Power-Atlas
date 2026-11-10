# Consumer Class Actions — research-source registry
Updated: 2026-11-10

## Four discovery providers

These sites are **secondary research and discovery sources**, not court dockets or court-appointed settlement administrators. Use attributed links and independently verify the facts and deadlines on the original source.

| Provider | Discovery entry | Role |
| --- | --- | --- |
| ClassAction.org | https://www.classaction.org/settlements | Settlement and lawsuit reporting; use as a lead to primary sources |
| Top Class Actions | https://topclassactions.com/category/lawsuit-settlements/open-lawsuit-settlements/ | Settlement news and consumer alerts, including open claim lists |
| Consumer Action | https://www.consumer-action.org/lawsuits/by-status/open | Nonprofit consumer advocacy organization's curated open-to-claims list |
| ClaimDepot | https://www.claimdepot.com/settlements | Searchable settlement directory with topics, administrator categories and procedural-status filters |

The data ledger `data/consumer-class-actions/cases-v1.json` retains a wider directory of related ClassAction.org pages and a separate, limited set of **independently verified case records**. The source-directory links are not counted as cases.

## Primary-source promotion gate

1. Discover a company, legal allegation or settlement from a secondary listing; retain its URL for attribution.
2. Independently match defendants, docket, court and case name. Look for a court order or official settlement administrator notice.
3. Confirm, on the primary source, the eligibility window, applicable products/states, procedural status, opt-out deadline, claims deadline, payment calculation, final hearing and date reviewed.
4. Keep `discoverySource` and `secondaryUrl` in case records when a report led to an independently verified entry.
5. Separate private class actions from FTC/CFPB agency enforcement, lawyer advertising, mass torts, and unfiled investigations.
6. Display a source confidence gate, plain-language allegation qualifiers and a clear warning where a claims window is not verified as open. Do not guarantee payments, imply any defendant's liability, or sum gross fund amounts as consumers' actual injury.
7. Identify duplicate entries across publishers using stable court/docket identifiers; avoid counting the same case four times.

## Content and data rights

Use links and attributed, independently written summaries; no automated crawling, mirroring publisher articles, or bulk-copying source content. No API/data license has been established for any of the four sites. Consumer Action expressly permits linking to its materials; it limits commercial reuse of its copyrighted content (https://www.consumer-action.org/about/articles/copyright_policy). ClaimDepot's terms retain rights to their content and disclaim guarantees about accuracy and timeliness (https://www.claimdepot.com/legal/terms-of-service). Any future licensed feed needs explicit permission and a separate compliance review.

## Limitation

This is a source registry and manually reviewed case sample, not live synchronization. Search/claim status is a date-stamped snapshot. Official notices and the court govern legal deadlines and settlements.
