-- Power Atlas logical reconciliation schema (PostgreSQL 15+).
-- VERSIONED DESIGN ONLY: this repo's production site currently serves static JSON.
-- This file is not a claim that a live database migration has been executed.
-- No paid database required: integration can be deferred to an authorized DB.
BEGIN;

CREATE SCHEMA IF NOT EXISTS atlas;

DO $$ BEGIN
 CREATE TYPE atlas.vote_verification_status AS ENUM ('unverified','partially_parsed','certified_tally');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
 CREATE TYPE atlas.jurisdiction_coverage_status AS ENUM ('pending','page1_complete','full_sweep');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
 CREATE TYPE atlas.bill_verification_status AS ENUM ('raw_candidate','source_matched','official_text_verified','official_status_verified');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
 CREATE TYPE atlas.certification_status AS ENUM ('pending_download','downloaded_unreconciled','reconciled_official');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS atlas.evidence_source (
  id TEXT PRIMARY KEY,
  source_url TEXT NOT NULL CHECK (source_url ~ '^https://'),
  source_authority TEXT,
  source_type TEXT NOT NULL,
  retrieved_at TIMESTAMPTZ,
  source_sha256 TEXT,
  license_status TEXT NOT NULL DEFAULT 'review_required',
  UNIQUE(source_url, source_type)
);
CREATE TABLE IF NOT EXISTS atlas.legal_framework (
  id TEXT PRIMARY KEY,
  decision_date DATE NOT NULL,
  cited_case TEXT NOT NULL,
  controlling_source_url TEXT NOT NULL CHECK (controlling_source_url ~ '^https://'),
  legal_subject TEXT NOT NULL,
  reviewer_notes TEXT,
  CHECK (id IN ('VRA_Sec2_Milligan_2023','VRA_Sec2_Callais_2026'))
);
INSERT INTO atlas.legal_framework
 (id,decision_date,cited_case,controlling_source_url,legal_subject)
 VALUES
 ('VRA_Sec2_Milligan_2023','2023-06-08','Allen v. Milligan',
 'https://www.supremecourt.gov/docket/docketfiles/html/public/21-1086.html','Section 2 vote dilution precedent'),
 ('VRA_Sec2_Callais_2026','2026-04-29','Louisiana v. Callais',
 'https://www.supremecourt.gov/docket/docketfiles/html/public/24-109.html','Section 2 vote dilution and constitutional limits on race-based districting')
 ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS atlas.jurisdiction (
  id CHAR(2) PRIMARY KEY CHECK (id ~ '^[A-Z]{2}$'),
  display_name TEXT
);
CREATE TABLE IF NOT EXISTS atlas.raw_ingestion (
  id TEXT PRIMARY KEY,
  domain TEXT NOT NULL CHECK(domain IN ('legislation','election_results','campaign_finance','map','judicial')),
  source_record_id TEXT NOT NULL,
  source_id TEXT REFERENCES atlas.evidence_source(id),
  raw_metadata JSONB NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'raw_candidate',
  ingestion_time TIMESTAMPTZ DEFAULT now(),
  UNIQUE(domain,source_record_id)
);
CREATE TABLE IF NOT EXISTS atlas.search_coverage (
  jurisdiction_id CHAR(2) PRIMARY KEY REFERENCES atlas.jurisdiction(id),
  provider TEXT NOT NULL,
  search_term TEXT NOT NULL,
  search_depth INTEGER NOT NULL DEFAULT 0 CHECK(search_depth >= 0),
  page_indexed INTEGER NOT NULL DEFAULT 0 CHECK(page_indexed >= 0),
  total_matches_reported INTEGER CHECK(total_matches_reported >= 0),
  coverage_status atlas.jurisdiction_coverage_status NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
  last_error TEXT,
  last_checked_at TIMESTAMPTZ,
  CHECK (page_indexed <= search_depth),
  CHECK (
    (coverage_status='pending' AND page_indexed=0)
    OR (coverage_status='page1_complete' AND page_indexed>=1)
    OR (coverage_status='full_sweep' AND page_indexed>=1 AND total_matches_reported IS NOT NULL)
  )
);
CREATE TABLE IF NOT EXISTS atlas.ingestion_queue (
  id TEXT PRIMARY KEY,
  jurisdiction_id CHAR(2) NOT NULL REFERENCES atlas.jurisdiction(id),
  domain TEXT NOT NULL,
  query TEXT NOT NULL,
  next_page INTEGER NOT NULL CHECK (next_page >= 1),
  reason TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','retry','blocked','completed')),
  UNIQUE(jurisdiction_id,domain,query,next_page)
);

-- Only official-reviewable bill identities enter this table.
-- Raw Bill Commons keyword matches stay in raw_ingestion.
CREATE TABLE IF NOT EXISTS atlas.bills (
  id TEXT PRIMARY KEY,
  jurisdiction_id CHAR(2) REFERENCES atlas.jurisdiction(id),
  session_id TEXT,
  legislative_identifier TEXT NOT NULL,
  bill_title TEXT NOT NULL,
  official_source_id TEXT REFERENCES atlas.evidence_source(id),
  verification_status atlas.bill_verification_status NOT NULL
    CHECK(verification_status != 'raw_candidate'),
  introduced_date DATE,
  enacted_date DATE,
  last_official_action TEXT,
  UNIQUE(jurisdiction_id,session_id,legislative_identifier)
);
CREATE TABLE IF NOT EXISTS atlas.roll_calls (
  id TEXT PRIMARY KEY,
  bill_id TEXT NOT NULL REFERENCES atlas.bills(id),
  jurisdiction_id CHAR(2) NOT NULL REFERENCES atlas.jurisdiction(id),
  chamber TEXT NOT NULL,
  motion TEXT NOT NULL,
  vote_date DATE,
  yea INTEGER CHECK(yea >= 0),
  nay INTEGER CHECK(nay >= 0),
  abstain INTEGER CHECK(abstain >= 0),
  absent INTEGER CHECK(absent >= 0),
  vote_verification_status atlas.vote_verification_status NOT NULL DEFAULT 'unverified',
  official_source_id TEXT REFERENCES atlas.evidence_source(id),
  CHECK (
    vote_verification_status <> 'certified_tally'
    OR (yea IS NOT NULL AND nay IS NOT NULL AND abstain IS NOT NULL
        AND official_source_id IS NOT NULL)
  )
);
-- Certified in roll_calls means officially verified *legislative tally*, not
-- the separate certification of election returns.
CREATE TABLE IF NOT EXISTS atlas.election_offices (
  jurisdiction_id CHAR(2) PRIMARY KEY REFERENCES atlas.jurisdiction(id),
  election_office_url TEXT NOT NULL CHECK (election_office_url ~ '^https://'),
  certification_status atlas.certification_status NOT NULL DEFAULT 'pending_download',
  official_canvass_url TEXT,
  CHECK (certification_status <> 'reconciled_official' OR official_canvass_url IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS atlas.election_contests (
  id TEXT PRIMARY KEY,
  jurisdiction_id CHAR(2) NOT NULL REFERENCES atlas.jurisdiction(id),
  election_year SMALLINT NOT NULL,
  office TEXT NOT NULL,
  stage TEXT NOT NULL,
  district_id TEXT,
  map_version TEXT,
  certified_source_id TEXT REFERENCES atlas.evidence_source(id),
  certification_status atlas.certification_status NOT NULL DEFAULT 'pending_download',
  CHECK(certification_status <> 'reconciled_official' OR certified_source_id IS NOT NULL),
  UNIQUE(jurisdiction_id,election_year,office,stage,district_id)
);
CREATE TABLE IF NOT EXISTS atlas.election_returns (
  id TEXT PRIMARY KEY,
  contest_id TEXT NOT NULL REFERENCES atlas.election_contests(id),
  candidate_id TEXT NOT NULL,
  party TEXT,
  votes BIGINT NOT NULL CHECK(votes >= 0),
  source_id TEXT REFERENCES atlas.evidence_source(id),
  UNIQUE(contest_id,candidate_id)
);
CREATE TABLE IF NOT EXISTS atlas.finance_transactions (
  id TEXT PRIMARY KEY,
  filer_committee_id TEXT NOT NULL,
  recipient_committee_id TEXT,
  transaction_date DATE,
  amount_usd NUMERIC(18,2) NOT NULL,
  filing_source_id TEXT REFERENCES atlas.evidence_source(id),
  review_status TEXT NOT NULL DEFAULT 'source_indexed'
);
CREATE TABLE IF NOT EXISTS atlas.map_versions (
  id TEXT PRIMARY KEY,
  jurisdiction_id CHAR(2) REFERENCES atlas.jurisdiction(id),
  adopted_date DATE,
  effective_date DATE,
  geometry_source_id TEXT REFERENCES atlas.evidence_source(id),
  geometry_vintage TEXT NOT NULL,
  geometry_status TEXT NOT NULL CHECK (geometry_status IN ('generalized_display','authoritative_full_resolution')),
  legal_framework_at_drawing TEXT REFERENCES atlas.legal_framework(id),
  framework_as_of_date DATE,
  application_review_status TEXT NOT NULL DEFAULT 'human_legal_review_required'
);
CREATE TABLE IF NOT EXISTS atlas.legal_assessments (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  map_version_id TEXT REFERENCES atlas.map_versions(id),
  claim_type TEXT NOT NULL,
  drawing_date DATE,
  adjudication_date DATE,
  framework_at_drawing TEXT REFERENCES atlas.legal_framework(id),
  framework_at_adjudication TEXT REFERENCES atlas.legal_framework(id),
  source_id TEXT REFERENCES atlas.evidence_source(id),
  review_status TEXT NOT NULL DEFAULT 'human_legal_review_required',
  legal_risk_score NUMERIC DEFAULT NULL,
  CHECK (legal_risk_score IS NULL)
);
-- No score is produced solely from chronology: an earlier map adjudicated
-- in 2026 may be affected by Callais depending on the case/procedural posture.
COMMIT;
