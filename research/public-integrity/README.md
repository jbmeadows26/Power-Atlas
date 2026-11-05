# Public Integrity Investigations — Evidence & Publication Protocol
Updated: 2026-11-04

## Mission
Connect documented exchanges of benefits, campaign contributions, public contract awards, legislative acts and legal outcomes without claiming that a correlation or indictment establishes criminal conduct. Publish legible, source-linked, dated case studies that distinguish confirmed crimes from unresolved allegations, allegations from named-only relationships, and estimates from actual payments.

## Initial source-backed inventory
- UI: `platform/unified/investigations.html`
- UI-backed static data: `platform/unified/investigations-data.json`
- Canonical research snapshot: `data/influence/investigations-2026.json`
- Prior standalone case: `platform/unified/navatek.html` and `data/influence/navatek-2026.json`
- Initial snapshot included 20 cases; subsequent verified additions now bring the November 4 snapshot to 26 cases, 71 distinct named persons and 41 official-source / underlying court-file links. Counts are computed from the JSON and must not be frozen into UI descriptions.
- This is a purposive case collection, not a representative sample, prevalence estimate, ranking of political actors, or a universal allegation database.

## Evidentiary boundary
- Person association has role-level provenance. "Named in court evidence" ≠ "charged" ≠ "pleaded guilty" ≠ "convicted"; source dates apply to each status.
- For mixed cases, show each person's status separately. All people charged but not convicted retain the presumption of innocence.
- DOJ press releases are strong official summaries; favor the underlying plea, sentencing memorandum, indictment, verdict, docket or published agency resolution for claim-level verification. A charging document is still an allegation.
- For each financial figure, type it explicitly: `alleged_offer`, `actual_bribe_paid`, `court_determined_loss`, `restitution_ordered`, `forfeiture`, `civil_penalty`, `appropriation_request`, `appropriated_funding`, `contract_award_value`, `obligation`, `outlay`. Never add incomparable numbers.
- Distinguish direct evidence of quid pro quo from temporal coincidence and from prosecutors' allegations.
- Public figures, contractors and defendants may be identified where sourced in official public records; do not introduce home addresses, private contact details, family members unconnected to an official public record, or social-media accusations.
- Every case preserves countervailing information where available, including dismissals, acquittals, vacaturs, appellate decisions and official responses. Never silently replace earlier status; date the new source.
- No political or individual guilt rankings or qualitative verdicts.

## Source-discovery ladder (free access where lawful)
1. **Official criminal records**: DOJ Public Integrity Section and USAO news, linked filed indictments, guilty pleas, verdicts, sentencing releases and RECAP-accessible court documents.
2. **Political money**: FEC reports, enforcement MUR files, LDA.gov reports, House lobbying disclosures; distinguish disbursements from reported contributions and avoid inferring that a donation bought an act.
3. **Public expenditures**: USAspending federal prime and sub-awards, FPDS/SAM.gov, appropriations bills and committee reports; join on recipient and unique award IDs, not fuzzy names alone.
4. **Corporate/legal**: SEC company/13D/8-K disclosures, regulator civil settlements, inspector general audits, state ethics commission decisions, state attorney general actions.
5. **Independent reporting**: ProPublica, local investigative news, databases such as OpenSecrets for discovery with original documents traced and rights respected.

## Next research tasks
- Reconcile all indexed cases to original court dockets and record linked case numbers, court, offense-level outcomes, sentencing and any appeal changes as of retrieval date.
- Attach contract IDs and separate `award_amount`, `obligation_amount`, `actual_paid`, `estimated_loss` by government agency and fiscal year.
- Attach donor- and committee-level transaction IDs and LDA filings where applicable; identify known omissions and refunds. Do not import unreviewed FEC links as accusations.
- Add exact dated relationship evidence for officials, executives, contractors and nonprofit organizations; avoid graph edges implying wrongdoing by association.
- Build source freshness checks and a *private* review queue for new DOJ/IG releases; publish only after editorial validation.
- Validate each case on mobile; verify record links, filter semantics, source dates, caveats and current legal stage before a public update.
- Maintain zero paid API requirements, source-license compliance, respectful crawl throttling, no unsupported automated exposure of suspects.

## Release tests
- Parse snapshot JSON and require unique case IDs, unique person names within each case, >=1 official source URL per case, a dated source event, and no empty legal-status field.
- Confirm SPA/HTML route renders and local JSON feed loads. Spot-check searches by subject/person, category and legal stage; verify anchors and source links.
- Log deployed commit and verify production HTTP 200 for `/investigations.html`, `/investigations-data.json`, and the existing Navatek case before declaring live.
- A production Vercel READY state alone does not prove browser interactions; use a browser interaction check if available.

## Plain-language presentation rules
- Every case should have a `plain_language` object containing: `summary` (one sentence, ideally under 30 words), `figure` (one plain description of the displayed number), `flow` (three short stages), and `caveat` (one material qualification).
- Preserve full factual summaries, precise metric meanings, detailed flows, limitations, legal statuses, dates and official source URLs in the underlying case data. Plain-language text is an additional reading layer, never a replacement for evidence.
- Use short visible headings: Follow the money; Who was involved?; What to keep in mind; Check the sources. Put longer context behind expandable explanations and keep legal-stage notices visible.
- On case cards: one-sentence summary, one labeled figure, names with status available in detail. Never headline the contract value as if it were a bribe or loss.
- Every new case should receive plain-language text before publication and should be tested on a narrow mobile viewport.
