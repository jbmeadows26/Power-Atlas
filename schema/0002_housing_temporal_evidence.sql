-- Power Atlas housing vertical slice: provenance-first, time-bounded evidence model.
-- DESIGN MIGRATION ONLY; not applied to production. PostgreSQL 15+.
-- Logical extension of schema/0001_evidence_domain_separation.sql.
-- No raw data ingestion, ownership claims, personal tenants or causal findings.
BEGIN;
CREATE SCHEMA IF NOT EXISTS atlas_housing;

-- An original-source URL is not the same as a checked record.
-- A content hash is optional for link-first inspection; if later archived, record it.
CREATE TABLE IF NOT EXISTS atlas_housing.source_document (
  source_record_id TEXT PRIMARY KEY,
  source_catalog_id TEXT,
  authority TEXT NOT NULL,
  source_url TEXT NOT NULL CHECK (source_url ~ '^https://'),
  record_locator TEXT,                  -- filing ID, bill page, table cell, docket entry
  public_access_status TEXT NOT NULL DEFAULT 'reference_only'
    CHECK (public_access_status IN ('reference_only','live_record','permitted_cache','archived_original')),
  source_published_at TIMESTAMPTZ,
  source_effective_on DATE,
  retrieved_at TIMESTAMPTZ,
  reviewed_at TIMESTAMPTZ,
  content_sha256 TEXT CHECK (content_sha256 IS NULL OR content_sha256 ~ '^[a-f0-9]{64}$'),
  source_terms_status TEXT NOT NULL DEFAULT 'review_required'
    CHECK (source_terms_status IN ('review_required','public_reference_allowed','reuse_permitted','restricted','blocked')),
  review_stage TEXT NOT NULL DEFAULT 'source_link_identified'
    CHECK (review_stage IN ('source_link_identified','original_record_checked','cross_source_reconciled','disputed')),
  CHECK (review_stage NOT IN ('original_record_checked','cross_source_reconciled')
         OR (record_locator IS NOT NULL AND reviewed_at IS NOT NULL))
);

-- One stable ID per real entity; individuals are limited to publicly relevant actors.
-- No names or private details of tenants or protected persons.
CREATE TABLE IF NOT EXISTS atlas_housing.node (
  node_id TEXT PRIMARY KEY,
  node_kind TEXT NOT NULL CHECK(node_kind IN
    ('parcel','legal_entity','public_person','committee','public_body','bill',
     'decision','geographic_market','court_case','trade_association')),
  display_label TEXT NOT NULL,
  jurisdiction TEXT,
  external_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(node_kind,jurisdiction,external_id)
);

CREATE TABLE IF NOT EXISTS atlas_housing.parcel (
  parcel_node_id TEXT PRIMARY KEY REFERENCES atlas_housing.node(node_id),
  state_code CHAR(2) NOT NULL,
  county_fips CHAR(5),                  -- tax parcel identity is state/county/local scoped
  municipality TEXT,
  local_parcel_id TEXT NOT NULL,
  parcel_version TEXT,
  standardized_address TEXT,           -- public/geocoding permission reviewed separately
  longitude NUMERIC(10,7),
  latitude NUMERIC(10,7),
  bedrooms INTEGER CHECK(bedrooms IS NULL OR bedrooms >= 0),
  unit_count INTEGER CHECK(unit_count IS NULL OR unit_count >= 1),
  geometry_source_record_id TEXT REFERENCES atlas_housing.source_document(source_record_id),
  UNIQUE(state_code,county_fips,municipality,local_parcel_id,parcel_version)
);

CREATE TABLE IF NOT EXISTS atlas_housing.legal_entity (
  entity_node_id TEXT PRIMARY KEY REFERENCES atlas_housing.node(node_id),
  official_legal_name TEXT NOT NULL,
  registration_jurisdiction TEXT,
  registration_number TEXT,
  cik TEXT,
  entity_type TEXT,
  public_registry_source_record_id TEXT REFERENCES atlas_housing.source_document(source_record_id),
  UNIQUE(registration_jurisdiction,registration_number)
);

-- Each ownership, officer, agency or association relationship is its own
-- evidence claim, not a side effect of fuzzy name matching.
CREATE TABLE IF NOT EXISTS atlas_housing.relationship (
  relationship_id TEXT PRIMARY KEY,
  from_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  to_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  relation_type TEXT NOT NULL CHECK(relation_type IN
    ('parcel_legal_owner','equity_owner','controlling_parent','managing_agent',
     'registered_agent','same_mailing_address','officer_of','director_of',
     'connected_pac','member_of_trade_association','lobbying_client_of',
     'other_documented_association')),
  effective_from DATE,
  effective_to DATE,                     -- exclusive, NULL means unknown, NOT current
  interest_pct NUMERIC(7,4) CHECK(interest_pct IS NULL OR (interest_pct >= 0 AND interest_pct <= 100)),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  evidence_status TEXT NOT NULL DEFAULT 'candidate'
    CHECK(evidence_status IN ('candidate','record_checked','independently_reconciled','disputed','rejected')),
  match_method TEXT NOT NULL DEFAULT 'manual_source'
    CHECK(match_method IN ('manual_source','official_identifier','name_candidate','address_candidate','other')),
  relationship_note TEXT,
  asserted_at TIMESTAMPTZ NOT NULL DEFAULT now(), -- system observation time
  CHECK(from_node_id <> to_node_id),
  CHECK(effective_from IS NULL OR effective_to IS NULL OR effective_to > effective_from),
  CHECK(interest_pct IS NULL OR relation_type IN ('equity_owner','controlling_parent')),
  CHECK(NOT (relation_type IN ('equity_owner','controlling_parent','parcel_legal_owner')
              AND match_method IN ('name_candidate','address_candidate')
              AND evidence_status IN ('record_checked','independently_reconciled')))
);

-- For legal changes, political districts, and regulators, use dated jurisdiction.
CREATE TABLE IF NOT EXISTS atlas_housing.office_tenure (
  tenure_id TEXT PRIMARY KEY,
  actor_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  public_body_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  district_boundary_version TEXT,
  office_title TEXT NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE,
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  CHECK(effective_to IS NULL OR effective_to > effective_from)
);

CREATE TABLE IF NOT EXISTS atlas_housing.public_decision (
  decision_node_id TEXT PRIMARY KEY REFERENCES atlas_housing.node(node_id),
  decision_kind TEXT NOT NULL CHECK(decision_kind IN
    ('ordinance','state_law','federal_law','zoning_board','permit','tax_assessment',
     'regulatory_order','budget','merger_review','settlement','court_order','other')),
  public_body_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  jurisdiction TEXT NOT NULL,
  case_or_bill_number TEXT,
  adopted_at DATE,
  effective_from DATE,
  effective_to DATE,
  disposition TEXT NOT NULL DEFAULT 'unconfirmed'
    CHECK(disposition IN ('unconfirmed','proposed','adopted','rejected','enjoined','superseded','rescinded')),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  CHECK(effective_from IS NULL OR effective_to IS NULL OR effective_to > effective_from)
);

CREATE TABLE IF NOT EXISTS atlas_housing.roll_call (
  roll_call_id TEXT PRIMARY KEY,
  decision_node_id TEXT NOT NULL REFERENCES atlas_housing.public_decision(decision_node_id),
  actor_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  vote_date DATE NOT NULL,
  vote_cast TEXT NOT NULL CHECK(vote_cast IN ('yea','nay','abstain','present','absent','other')),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  UNIQUE(decision_node_id,actor_node_id,vote_date)
);

-- Donors, recipients and committees remain distinct legal entities.
-- An employee's personal donation is NOT a donation by their employer.
-- A reported lobbying total is not apportioned automatically to one bill.
CREATE TABLE IF NOT EXISTS atlas_housing.financial_event (
  financial_event_id TEXT PRIMARY KEY,
  payer_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  recipient_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  event_kind TEXT NOT NULL CHECK(event_kind IN
    ('candidate_contribution','pac_contribution','committee_transfer','independent_expenditure',
     'lobbying_report_total','in_kind_support','other_disclosed_payment')),
  payer_capacity TEXT NOT NULL CHECK(payer_capacity IN
    ('individual_personal','corporate_treasury','political_committee','organization','unknown')),
  election_level TEXT CHECK(election_level IN ('federal','state','local','other','not_applicable')),
  amount_usd NUMERIC(18,2) CHECK(amount_usd IS NULL OR amount_usd >= 0),
  event_date DATE,
  filing_date DATE,
  filing_id TEXT,
  transaction_id TEXT,
  reporting_scope TEXT,
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  evidence_status TEXT NOT NULL DEFAULT 'reported_not_reconciled'
    CHECK(evidence_status IN ('reported_not_reconciled','filing_reconciled','disputed')),
  CHECK(payer_node_id <> recipient_node_id),
  -- Federal candidate committee contributions from corporate treasury are
  -- prohibited; state/local law must be evaluated per jurisdiction.
  CHECK(NOT (event_kind = 'candidate_contribution'
             AND payer_capacity = 'corporate_treasury'
             AND election_level = 'federal'))
);

CREATE TABLE IF NOT EXISTS atlas_housing.lobbying_reference (
  reference_id TEXT PRIMARY KEY,
  financial_event_id TEXT REFERENCES atlas_housing.financial_event(financial_event_id),
  client_node_id TEXT NOT NULL REFERENCES atlas_housing.node(node_id),
  decision_node_id TEXT REFERENCES atlas_housing.public_decision(decision_node_id),
  cited_issue TEXT NOT NULL,
  period_from DATE,
  period_to DATE,
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  allocation_method TEXT NOT NULL DEFAULT 'not_allocated'
    CHECK(allocation_method IN ('not_allocated','itemized_official')),
  itemized_amount_usd NUMERIC(18,2) CHECK(itemized_amount_usd IS NULL OR itemized_amount_usd >= 0),
  CHECK(allocation_method <> 'not_allocated' OR itemized_amount_usd IS NULL),
  CHECK(period_from IS NULL OR period_to IS NULL OR period_to >= period_from)
);

-- Market prices preserve asking vs signed-lease vs HUD reference definitions.
-- A row never implies a tenant's actual payment or a property-specific rent
-- unless the underlying verified source permits that granularity.
CREATE TABLE IF NOT EXISTS atlas_housing.rent_observation (
  observation_id TEXT PRIMARY KEY,
  parcel_node_id TEXT REFERENCES atlas_housing.parcel(parcel_node_id),
  location_label TEXT NOT NULL,
  geography_type TEXT NOT NULL CHECK(geography_type IN ('parcel','municipality','tract','zcta','county','metro','state')),
  observed_on DATE NOT NULL,
  bedrooms INTEGER CHECK(bedrooms IS NULL OR bedrooms >= 0),
  property_type TEXT NOT NULL DEFAULT 'not_specified',
  price_definition TEXT NOT NULL CHECK(price_definition IN
    ('asking_rent','signed_lease_rent','hud_fmr_reference','gross_rent_acs','other')),
  statistic TEXT NOT NULL CHECK(statistic IN ('unit_observation','median','mean','provider_aggregate','reference')),
  monthly_usd NUMERIC(12,2) NOT NULL CHECK(monthly_usd >= 0),
  sample_n INTEGER CHECK(sample_n IS NULL OR sample_n >= 1),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  source_vintage TEXT,
  limitations TEXT NOT NULL,
  CHECK(geography_type <> 'parcel' OR parcel_node_id IS NOT NULL)
);

-- Eviction *filings* != judgments != completed evictions.
CREATE TABLE IF NOT EXISTS atlas_housing.housing_outcome (
  outcome_id TEXT PRIMARY KEY,
  parcel_node_id TEXT REFERENCES atlas_housing.parcel(parcel_node_id),
  jurisdiction TEXT NOT NULL,
  outcome_kind TEXT NOT NULL CHECK(outcome_kind IN
    ('eviction_filing','eviction_judgment','eviction_executed','vacancy_rate',
     'new_permits','rent_increase','other')),
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  value NUMERIC(18,4) NOT NULL,
  denominator NUMERIC(18,4),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  suppression_status TEXT NOT NULL DEFAULT 'public_aggregate'
    CHECK(suppression_status IN ('public_aggregate','disclosable_public_record','suppressed')),
  CHECK(period_end >= period_start),
  CHECK(denominator IS NULL OR denominator > 0)
);

-- A descriptive pathway and a causal estimate are different artifacts.
CREATE TABLE IF NOT EXISTS atlas_housing.analytic_assessment (
  assessment_id TEXT PRIMARY KEY,
  policy_decision_node_id TEXT REFERENCES atlas_housing.public_decision(decision_node_id),
  affected_geography TEXT NOT NULL,
  treatment_definition TEXT,
  control_geography TEXT,
  period_before TEXT,
  period_after TEXT,
  estimator TEXT NOT NULL CHECK(estimator IN
    ('descriptive','difference_in_differences','event_study','synthetic_control','other')),
  pretrend_check TEXT,
  spillover_check TEXT,
  covariates TEXT,
  uncertainty_report TEXT,
  conclusion_status TEXT NOT NULL CHECK(conclusion_status IN
    ('descriptive_only','insufficient_evidence','causal_estimate_reviewed','rejected')),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  CHECK(conclusion_status <> 'causal_estimate_reviewed'
    OR (control_geography IS NOT NULL AND period_before IS NOT NULL
        AND period_after IS NOT NULL AND uncertainty_report IS NOT NULL
        AND pretrend_check IS NOT NULL AND spillover_check IS NOT NULL
        AND estimator <> 'descriptive'))
);

-- No unsourced implied relationships, no inferred ownership as settled fact,
-- and never treat open-ended intervals as verified to present.
CREATE OR REPLACE VIEW atlas_housing.public_verified_relations AS
SELECT r.relationship_id, r.from_node_id, r.to_node_id, r.relation_type,
       r.effective_from, r.effective_to, r.interest_pct,
       s.source_record_id, s.source_url, s.record_locator, s.reviewed_at
FROM atlas_housing.relationship r
JOIN atlas_housing.source_document s ON s.source_record_id = r.source_record_id
WHERE r.evidence_status IN ('record_checked','independently_reconciled')
  AND s.review_stage IN ('original_record_checked','cross_source_reconciled')
  AND s.source_terms_status IN ('public_reference_allowed','reuse_permitted')
  AND r.effective_from IS NOT NULL
  AND r.relation_type <> 'same_mailing_address';

CREATE INDEX IF NOT EXISTS housing_relationship_by_source_time
 ON atlas_housing.relationship(from_node_id,to_node_id,relation_type,effective_from,effective_to);
CREATE INDEX IF NOT EXISTS housing_finance_by_payer_time
 ON atlas_housing.financial_event(payer_node_id,event_date);
CREATE INDEX IF NOT EXISTS housing_outcome_by_place_time
 ON atlas_housing.rent_observation(location_label,observed_on,bedrooms,price_definition);

-- All tables are intentionally empty until specific original records pass review.
COMMIT;
