# Power Atlas — reference-first now, selective local archive later
**Decision record:** 2026-11-12 | **Status:** interim reference index implemented; future Pi/CM4 archival design only.

## Objective and non-goals
Keep the site fast and source-backed without storing full public datasets today. Do not infer that a source directory is a verified record, a live API, a complete jurisdiction, or proof of causality. Preserve existing Power Atlas evidence and QA gates. Do not deploy a new public-network proxy, paid provider, or unreviewed scraper. Existing collection workflows remain separately configured; this document does **not** disable them.

## Phase 0 — NOW: quick reference (default)
- `platform/unified/data/source-reference-index-v1.json` is a small, public-friendly **official source-link index**, generated deterministically from the authoritative 2026-11-12 research gap backlog.
- `python scripts/reference_sources.py --list`, `--id fec-committee-to-committee-oth` and `--gate state_campaign_finance` resolve stable source IDs without contacting the network.
- A reader can follow the official source link. Existing site pages may query an approved third-party API directly where already implemented, but the new index does not automatically turn portal pages into APIs.
- Do **not** cache a reader's ZIP, name, private identity, browsing history or political inference. A public lookup's official service can receive the data that the user voluntarily submits to that service. Keep consent and privacy disclosures.
- Display provenance levels: **link identified**, **original record checked**, **reconciled**, and **publication-grade**. Links alone never close the 55 local gaps or 9 national gates.
- When an official source is unavailable, show **unavailable / last verified date**, not a fabricated zero, stale result disguised as current, or unsupported narrative.
- The registry is static metadata. Actual on-demand fetching must use a source-specific adapter, HTTPS origin allowlist, timeouts, rate limits, license review and cache controls; no arbitrary-URL proxy or browser-side secret API keys.

## Phase 1 — AFTER BOTH EXISTING PI 5s ARE CONFIGURED AND ONLINE: reference + cache
```
Visitor → Vercel presentation → bounded evidence resolver
                                  ├─ official URL / provider-specific free API
                                  ├─ source-ID metadata + validation
                                  ├─ short-lived response cache (only license-allowed)
                                  └─ claim/evidence receipts (version + source + date)
```
Hardware roles (SSD capacities are nominal, filesystem space will be lower):
- **Raspberry Pi 5 16 GB RAM / 512 GB SSD**: source registry, SQLite or modest PostgreSQL evidence index, entity crosswalks, bounded normalized cache, short receipt ledger. Budget disk by *usable* space, not full nominal 512 GB: ~15% OS/updates, 25% metadata/indexes, 35% bounded cache, 10% receipts/staging, 15% free headroom. Enforce space quotas and retention.
- **Raspberry Pi 5 8 GB RAM / 256 GB SSD**: independent retrieval scheduler and validation worker; small staging space; encrypted, verified backup **of critical indexes/config/receipts only** (not a full 512 GB replica). Reserve at least 20% free space and cap temporary downloads.
- Keep Vercel as the visitor-facing CDN/front end for now. Do not expose local PostgreSQL, SSH, NAS or unsecured Raspberry Pi ports to the public internet; use authenticated, outbound-only private connectivity or a tightly controlled reverse gateway. The site must work when home internet is unavailable, showing a dated public fallback instead of hanging.

## Phase 2 — WHEN THE SUPER6C HAS CM4 MODULES: selective original-data archive
The DeskPi Super6C physically supports up to **6 CM4 compute nodes**, each with its **own M.2 PCIe 2.0 x1 SSD**. Your six installed SSDs are not six active storage volumes until compatible CM4 compute modules, OS and a storage network are installed. SSD capacities and CM4 counts are not yet confirmed, so **do not assume usable aggregate capacity, redundancy, Ceph performance or a specific RAID layout**.

Start with **1–2 CM4s**, not mandatory six-node Ceph/Kubernetes:
- CM4 node A + SSD A: validated official raw-record snapshots (content-addressed, immutable after acceptance) and compressed Parquet extracts.
- CM4 node B + SSD B (if installed): checksum-verified replica and restoration staging, plus independent scheduled integrity checks. Replication is **not** itself backup.
- Remaining CM4/SSD pairs: add by dataset size and performance evidence (historical election/court/map archives; bulk committee finance) as needed, not by default.
- Each archived record receives a stable source ID, dataset/version, origin URL, publication/effective time, retrieval UTC, SHA-256, file size, license/redistribution conditions, archive path, schema version, transform version, redaction, entity join status and reviewer status. The *claim* links to this receipt rather than an unversioned local file.
- Avoid bulk-archiving mutable market listings or personal details unless collection, terms, privacy and public-interest necessity are established.

## Mode handoff — no frontend rewrite
**Reference** (now) → resolve `sourceId` to a canonical official source link, with "not downloaded" status.
**Hybrid** (Pi 5s available) → prefer a verified, dated cached answer; otherwise provider-specific live query; preserve publication receipts when a claim is shown.
**Archive** (Super6C CM4s configured) → for high-value historical investigations, read the content-hashed local snapshot; re-check authoritative status on a schedule. Continue live queries for frequently changing sources.
Source IDs, story evidence references and validation rules remain constant across modes. No mode switch alone closes a research gap.

## Evidence / claim relationship
```
Story claim → claim_id → source_id + exact external record_url/record_id
                                  └─ evidence_receipt (once retrieved)
                                      ├─ retrieved_at / published_at / effective_at
                                      ├─ raw_sha256 / normalized_sha256 / schema_version
                                      ├─ source authorization / source terms / redistribution
                                      ├─ coverage and entity-join confidence
                                      └─ validation status, reconciliation and review
```
Store source metadata and public institutional IDs; avoid republishing unnecessary people-level PII. No allegation is labeled proven without case-level independent evidence.

## Download priority (AFTER hardware + legal review)
1. Publication-critical immutable originals: certified returns, official votes and final court decisions tied to a live Power Atlas story.
2. Bounded, reconciled transaction cohorts: FEC committee-to-committee and state-finance records; handle amendments, transaction type and reporting direction. Do not treat all OTH rows as transfers.
3. Historical versions of political maps, legislative texts, corporate parent/subsidiary filings and relevant contracts.
4. Large national bulk datasets only when a measurable research need and retention budget justify them.

## Backup and disaster recovery
- Follow **3-2-1** for irreplaceable evidence metadata and selected raw originals: three copies, two media/devices, one encrypted geographically separate/offsite copy. Mirroring two SSDs in the same Super6C chassis is not an offsite backup.
- Perform daily encrypted incremental backups for the evidence DB/ledger; weekly archived-source manifests; monthly restoration test; quarterly disaster recovery drill. Protect credentials outside Git. If no offsite destination has been approved, the requirement remains **unmet**.
- Use filesystem checksums on ingestion, scheduled bit-rot audits and transactional database snapshots. Stagger upgrades and snapshot before schema changes.

## Activation checklist (must pass before `hybrid` or `archive`)
1. Pi host inventory, disk health and mounts confirmed; Super6C CM4 hardware actually online for archive.
2. HTTPS origin allowlists, rate limits, source terms/robots policies and download-size budgets validated.
3. Evidence resolver and reproducible receipts implemented and unit/integration tested.
4. Encrypted backups restored successfully on a second device; offsite recovery tested.
5. Source outage and Pi outage fail closed with a dated public-reference fallback; no public database ports.
6. Existing 55 + 9 research gates remain incomplete until record-level and jurisdiction-level acceptance tests pass.

## Existing systems and boundaries
- Existing `data/place-impact/deep-resource-map-v1.json` and the Census Reporter ZCTA requests are retained. A ZIP/ZCTA is **not** an electoral boundary.
- The separate `scripts/collect_fec_oth.py` weekly collector already exists; this architecture decision does not silently switch it off or assert that it has ingested a complete FEC archive.
- Current source candidate mapping: `research/assessments/ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json`.
- Check or regenerate index: `python scripts/reference_sources.py --check` or `python scripts/reference_sources.py --write`.
- Run offline tests: `python -m unittest discover -s tests -p 'test_reference_sources.py' -v`.

**Operational distinction:** This change provides an actual quick-reference registry now, and a migration-ready data contract for future Pi/CM4 archival. It does not yet install a Pi service, add a public lookup API, bulk-import source data, or certify previously missing records.
