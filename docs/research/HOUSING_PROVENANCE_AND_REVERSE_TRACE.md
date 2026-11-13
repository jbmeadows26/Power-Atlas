# Power Atlas housing: reverse trace + epistemic publication gate

**Design status: proposed, tested in isolated database, not migrated into production.**
**Operating mode: live reference.** No Raspberry Pi, Super6C, paid database or bulk source download is required to use the source index.
**Baseline:** 55 local + 9 national research gates remain open until jurisdiction/record-level completion rules are satisfied.

## Investigative direction

Start with a measured household expense, government revenue/payment or dated official decision, then trace **backward** through relevant records:

1. Define outcome: asking rent by bedroom / observed lease rent / actual payment / general property-tax rate / official PILOT service charge. **These cannot substitute for one another.**
2. Define geography and time: official local parcel identifier, municipality, county FIPS, tax year and effective dates. ZIP is not a parcel or electoral district.
3. Identify nominal legal property titleholder from a lawful, dated official record. Record transfers and corporate entities separately. A registered agent, mailing address, manager or shared officer name is not proof of ultimate ownership.
4. Compare dated parcel **assessment**, official general **tax rate**, parcel **bill**, posted collector **receipts**, any **PILOT/abatement agreement** and actual municipal-budget **collections**. Track credits, refunds, late postings and state/local exemptions separately.
5. Match specific government authorization: adopted ordinance, council vote or zoning board decision, legal effective date, and PILOT or tax agreement terms. Local decisions are not necessarily state bills.
6. Verify original campaign finance and lobbying reports by donor capacity, committee ID, reporting period, and correct transaction category. An individual's donation is not automatically their employer's payment.
7. Build a visual narrative with edges labeled **verified**, **uncertain**, **disputed** or **unknown**. Display the original record and precise locator for every positive claim.
8. Publish a measurable effect **only** after independent causal study design (valid pretrend, comparison, confounder and spillover checks). Temporal order, a matching money trail, or coincident rent increase does **not** prove motive or causal effect.

## Tax evidence now verified, in narrow scope

The official New Jersey Division of Taxation 2024 and 2025 general-tax-rate PDFs have been used for a **municipality-rate observation** in
`data/housing/official-tax-rate-cliffside-park-2024-2025.json`.

The model distinguishes:
- **2024:** 2.756 general and 1.966 effective rate, dollars per $100 of assessed value.
- **2025:** 2.836 general and 1.920 effective rate, same units.
- General vs effective rates are not interchangeable; no parcel, owner, payment, PILOT beneficiary, council member, individual renter or causal link is thereby verified.
- The reference is source-attributed by exact PDF/row locator. No captured byte hash exists. A URL and source page are not archival proof.

## Why a publication approval is not a boolean field

See `schema/0004_housing_publication_gate.sql`. Investigators may keep candidate nodes, public searches, and source records in the **research workspace**. The public evidence view selects only assertions that:
- identify a supported target table and actual target row, with matching original `source_record_id`;
- have a nonempty exact document locator and expected excerpt;
- have a researcher-marked and time-stamped source review;
- use a source with legal/reuse permission and a reviewed original record;
- have explicit editorial approval;
- are not currently disputed.

An absence of search results is stored as a **bounded search protocol**, e.g. a specific portal, query, date and scope. It never proves a regulator did nothing.

**Causality is not guaranteed by provenance.** Provenance proves a defensible document-to-claim path within a defined scope; quantitative causal inference requires additional identification, controls, uncertainty and independent review.

## Capture and archives

`capture_event` is **optional** for live-reference-only findings. When an authorized file copy is permitted, store the SHA-256 of the exact byte sequence, capture time and MIME type. It is not an independent government publication date, authenticity certification, or proof the official record never changed.

`archive_attempt` can be `not_attempted`, `archived`, `blocked_by_source`, `service_unavailable`, or `rights_not_verified`. A missing third-party archive never automatically disqualifies an otherwise legitimate official live reference.

## Defensive live-reference tripwire

`scripts/audit_live_reference.py` performs **classification only**. No requests, scraping, OCR or publishing occur unless a separately reviewed official-source adapter explicitly supplies a response and trustworthy extracted text.

| Observation | Internal state | Public result |
| --- | --- | --- |
| Timeout, 500/503 or network error | `http_error` | No automatic change |
| CAPTCHA, 401/403/429 or access challenge | `access_blocked` | No automatic change |
| One/two days of 404 | `hard_404` | No automatic change |
| Three **different, consecutive** days of 404 | `dead_link_review_candidate` | Manual link review; no accusation |
| PDF extractor fails or emits garbage | `parse_error` | Engineering alert; no accusation |
| High-quality readable content contains normalized expected excerpt | `content_verified` | Source content found, within checked scope |
| Readable document missing expected excerpt | `pending_manual_review` | Human verification required; no accusation or auto-retraction |
| Human manually confirms genuine source change | `source_changed` | Reassessment/caution; old finding is not silently rewritten |
| Human manually clears an earlier alert | `unchanged` | Clear stale caution; audit history remains |

Normalization tolerates whitespace/line break variations, but **preserves decimal identity**: 2.836 is not 28.36 or 2836. A normalized snippet match proves only that text was present in one extraction, not that surrounding context and the claim remain true.

## Model and product display

- **Verified original record:** solid edge; click to see exact official source, locator, date, and claim scope.
- **Unresolved connection:** dashed edge ending at an explicit `Unknown` node; never imply a parent company or government action.
- **Disputed original sources:** caution and side-by-side source evidence, not an approved solid edge. The public database has a separate restricted `public_disputed_evidence` view; the verified view excludes active disputes.
- **Access/parse errors:** maintain existing publication, internal diagnostic only, while audit checks continue.
- **Human-confirmed document change:** persistent inline caution until subsequent human review resolves it.
- **Search yielded no records:** "No matching public records found in [specified portal/query/date/scope]." Never state "no enforcement action occurred."

The publication view must be the **only public database read surface**. Do not grant the public client direct SELECT access to source research tables or let API handlers bypass this view. All assertions remain versioned and reviewable; production privileges, auth, migrations and real source adapters have **not** been deployed by this PR.

## Tests and operations

- `python -m unittest discover -s tests -p 'test_housing_reference_audit.py' -v`
- `python -m py_compile scripts/audit_live_reference.py`
- Execute `schema/0002...`, `schema/0003...`, `schema/0004...` **in a throwaway PostgreSQL test database only**, followed by `tests/sql/housing_publication_gate_smoke.sql`.
- GitHub Actions: `.github/workflows/validate-housing-evidence.yml`.

These tests use synthetic database rows and mocked network/parser outputs. The 2024–25 municipal rate fixture corresponds to the cited official PDFs but the test is **not** an actual live-source audit. No real PILOT, council vote, donation or rent-price causal claim is published by this implementation.
