-- Power Atlas housing fiscal evidence extension (requires 0002 schema).
-- DESIGN ONLY: do not run against production before source/rights review.
-- Tax lists, bills, receipts, abatements/PILOT and government receipts are
-- legally and statistically distinct. No owner identity is inferred from a
-- receipt, remitting account, registered agent or escrow servicer.
BEGIN;
CREATE SCHEMA IF NOT EXISTS atlas_housing;

-- Tax valuation: official list is a year/vintage snapshot, not a title search.
CREATE TABLE IF NOT EXISTS atlas_housing.tax_assessment (
  assessment_id TEXT PRIMARY KEY,
  parcel_node_id TEXT NOT NULL REFERENCES atlas_housing.parcel(parcel_node_id),
  tax_year SMALLINT NOT NULL CHECK(tax_year BETWEEN 1900 AND 2200),
  assessment_date DATE,
  published_at DATE,
  tax_class TEXT,
  taxable_assessed_land_usd NUMERIC(18,2) CHECK(taxable_assessed_land_usd IS NULL OR taxable_assessed_land_usd >= 0),
  taxable_assessed_improvement_usd NUMERIC(18,2) CHECK(taxable_assessed_improvement_usd IS NULL OR taxable_assessed_improvement_usd >= 0),
  total_assessed_usd NUMERIC(18,2) CHECK(total_assessed_usd IS NULL OR total_assessed_usd >= 0),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  record_scope TEXT NOT NULL DEFAULT 'annual_assessor_tax_list'
    CHECK(record_scope IN ('annual_assessor_tax_list','supplemental_assessment','appeal_adjustment')),
  limitations TEXT NOT NULL,
  UNIQUE(parcel_node_id,tax_year,record_scope,source_record_id)
);

-- General and effective rates are different. Only general tax rate is for
-- computing a standard NJ property tax bill; never substitute effective rate.
CREATE TABLE IF NOT EXISTS atlas_housing.municipal_tax_rate (
  rate_id TEXT PRIMARY KEY,
  state_code CHAR(2) NOT NULL,
  municipality TEXT NOT NULL,
  tax_year SMALLINT NOT NULL CHECK(tax_year BETWEEN 1900 AND 2200),
  rate_kind TEXT NOT NULL CHECK(rate_kind IN ('general','effective_statistical','special_district')),
  dollars_per_100_taxable_assessed NUMERIC(14,6) NOT NULL CHECK(dollars_per_100_taxable_assessed >= 0),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  UNIQUE(state_code,municipality,tax_year,rate_kind,source_record_id)
);

-- Amount billed is not cash collected. Some properties have exemption, credits,
-- interest, appeals or special assessments; keep billed amount as reported.
CREATE TABLE IF NOT EXISTS atlas_housing.tax_bill (
  tax_bill_id TEXT PRIMARY KEY,
  parcel_node_id TEXT NOT NULL REFERENCES atlas_housing.parcel(parcel_node_id),
  tax_year SMALLINT NOT NULL CHECK(tax_year BETWEEN 1900 AND 2200),
  installment_no INTEGER CHECK(installment_no IS NULL OR installment_no BETWEEN 1 AND 12),
  due_date DATE,
  billed_amount_usd NUMERIC(18,2) NOT NULL CHECK(billed_amount_usd >= 0),
  charge_kind TEXT NOT NULL CHECK(charge_kind IN
    ('ad_valorem_property_tax','special_assessment','adjustment','interest','other')),
  assessment_id TEXT REFERENCES atlas_housing.tax_assessment(assessment_id),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  status TEXT NOT NULL DEFAULT 'billed_not_payment_verified'
    CHECK(status IN ('billed_not_payment_verified','adjusted','voided')),
  limitations TEXT NOT NULL
);

-- Keep receipted transaction line items separate; credit/refund are not
-- additional positive collections. Don't store banking details, payer PII,
-- owner names or financial account fields. Property ID and amount suffice.
CREATE TABLE IF NOT EXISTS atlas_housing.tax_payment_receipt (
  payment_receipt_id TEXT PRIMARY KEY,
  parcel_node_id TEXT NOT NULL REFERENCES atlas_housing.parcel(parcel_node_id),
  tax_bill_id TEXT REFERENCES atlas_housing.tax_bill(tax_bill_id),
  collector_transaction_id TEXT,         -- official redacted public locator only
  posted_date DATE NOT NULL,
  payment_or_adjustment_kind TEXT NOT NULL CHECK(payment_or_adjustment_kind IN
    ('payment','refund','credit','reversal','correction')),
  applied_amount_usd NUMERIC(18,2) NOT NULL CHECK(applied_amount_usd >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'USD' CHECK(currency='USD'),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  verification_stage TEXT NOT NULL DEFAULT 'source_record_pending'
    CHECK(verification_stage IN ('source_record_pending','public_ledger_checked','official_receipt_reconciled','disputed')),
  privacy_review_status TEXT NOT NULL DEFAULT 'pending_review'
    CHECK(privacy_review_status IN ('pending_review','redacted_public_info','restricted')),
  limitations TEXT NOT NULL,
  UNIQUE(source_record_id,collector_transaction_id,posted_date,payment_or_adjustment_kind)
);

-- Important: NJ PILOT annual service charges can replace standard property
-- taxation for a qualifying project. Don't call an ASC an ordinary tax bill.
CREATE TABLE IF NOT EXISTS atlas_housing.tax_incentive_agreement (
  incentive_id TEXT PRIMARY KEY,
  parcel_node_id TEXT REFERENCES atlas_housing.parcel(parcel_node_id),
  agreement_holder_entity_node_id TEXT REFERENCES atlas_housing.legal_entity(entity_node_id),
  program_kind TEXT NOT NULL CHECK(program_kind IN
    ('pilot_long_term','pilot_other','five_year_abatement','partial_exemption',
     'tax_credit','other_exemption','other')),
  governing_authority TEXT NOT NULL,
  linked_public_decision_node_id TEXT REFERENCES atlas_housing.public_decision(decision_node_id),
  approval_date DATE,
  effective_from DATE,
  effective_to DATE,
  annual_service_charge_usd NUMERIC(18,2) CHECK(annual_service_charge_usd IS NULL OR annual_service_charge_usd >= 0),
  estimated_forgone_tax_usd NUMERIC(18,2) CHECK(estimated_forgone_tax_usd IS NULL OR estimated_forgone_tax_usd >= 0),
  estimate_method TEXT,
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  approval_status TEXT NOT NULL DEFAULT 'document_unconfirmed'
    CHECK(approval_status IN ('document_unconfirmed','adopted','expired','terminated','challenged')),
  limitations TEXT NOT NULL,
  CHECK(effective_from IS NULL OR effective_to IS NULL OR effective_to > effective_from),
  CHECK(estimated_forgone_tax_usd IS NULL OR estimate_method IS NOT NULL)
);

-- Distinguish municipal cash actually received from assessed property levies.
-- These are government-level receipts, not per-parcel tax payments.
CREATE TABLE IF NOT EXISTS atlas_housing.municipal_revenue_receipt (
  revenue_receipt_id TEXT PRIMARY KEY,
  municipality TEXT NOT NULL,
  state_code CHAR(2) NOT NULL,
  fiscal_year SMALLINT NOT NULL CHECK(fiscal_year BETWEEN 1900 AND 2200),
  revenue_kind TEXT NOT NULL CHECK(revenue_kind IN
    ('municipal_property_tax_collected','school_tax_collected',
     'county_tax_collected','pilot_annual_service_charge_collected',
     'special_assessment_collected','other_property_revenue')),
  amount_usd NUMERIC(20,2) NOT NULL CHECK(amount_usd >= 0),
  accounting_basis TEXT NOT NULL CHECK(accounting_basis IN ('cash','accrual','budget_estimate','other')),
  granularity TEXT NOT NULL CHECK(granularity IN ('actual_financial_statement','audited_actual','budget')),
  source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
  limitations TEXT NOT NULL
);

-- Public-facing completeness must never infer who actually remitted the money:
-- some payments arrive through mortgage escrow, agent or an unrelated payer.
CREATE OR REPLACE VIEW atlas_housing.public_tax_payment_summary AS
SELECT r.parcel_node_id, r.posted_date, r.payment_or_adjustment_kind,
       r.applied_amount_usd, r.verification_stage, s.source_url,
       s.record_locator, s.reviewed_at
FROM atlas_housing.tax_payment_receipt r
JOIN atlas_housing.source_document s ON s.source_record_id = r.source_record_id
WHERE r.privacy_review_status = 'redacted_public_info'
  AND r.verification_stage IN ('public_ledger_checked','official_receipt_reconciled')
  AND s.review_stage IN ('original_record_checked','cross_source_reconciled')
  AND s.source_terms_status IN ('public_reference_allowed','reuse_permitted');

CREATE INDEX IF NOT EXISTS housing_tax_assessment_year ON atlas_housing.tax_assessment(parcel_node_id,tax_year);
CREATE INDEX IF NOT EXISTS housing_tax_bill_year ON atlas_housing.tax_bill(parcel_node_id,tax_year);
CREATE INDEX IF NOT EXISTS housing_tax_receipt_date ON atlas_housing.tax_payment_receipt(parcel_node_id,posted_date);
CREATE INDEX IF NOT EXISTS housing_tax_incentive_time ON atlas_housing.tax_incentive_agreement(parcel_node_id,effective_from,effective_to);
COMMIT;
