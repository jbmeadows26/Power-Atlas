-- Power Atlas housing original-evidence publication and search integrity gate.
-- DESIGN ONLY (not applied to production). Requires schema/0002 and 0003.
-- File capture optional; live official source + exact locator + human review required.
-- Source traceability cannot prove causation, motive or wrongdoing.
BEGIN;
CREATE SCHEMA IF NOT EXISTS atlas_housing;

CREATE TABLE IF NOT EXISTS atlas_housing.capture_event (
 capture_id TEXT PRIMARY KEY,
 source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
 captured_at TIMESTAMPTZ NOT NULL,
 content_sha256 TEXT NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
 content_type TEXT NOT NULL,
 captured_byte_count BIGINT NOT NULL CHECK (captured_byte_count > 0),
 licensed_archival_status TEXT NOT NULL CHECK (licensed_archival_status IN ('retention_permitted','private_verification_only')),
 note TEXT NOT NULL,
 -- Hash is of the captured bytes; it is NOT a government-authored timestamp.
 UNIQUE(source_record_id,content_sha256,captured_at)
);

CREATE TABLE IF NOT EXISTS atlas_housing.archive_attempt (
 attempt_id TEXT PRIMARY KEY,
 source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
 attempted_at TIMESTAMPTZ NOT NULL,
 attempt_status TEXT NOT NULL CHECK(attempt_status IN
  ('not_attempted','archived','blocked_by_source','service_unavailable','rights_not_verified')),
 approved_archive_url TEXT CHECK (approved_archive_url IS NULL OR approved_archive_url ~ '^https://'),
 note TEXT,
 CHECK(attempt_status <> 'archived' OR approved_archive_url IS NOT NULL)
);

-- Assertions are separate from raw research nodes. A checked original record
-- and an exact location are necessary, but are not sufficient to publish.
CREATE TABLE IF NOT EXISTS atlas_housing.source_assertion (
 assertion_id TEXT PRIMARY KEY,
 source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
 target_table TEXT NOT NULL CHECK (target_table IN
  ('relationship','office_tenure','public_decision','roll_call','financial_event',
   'lobbying_reference','rent_observation','housing_outcome','analytic_assessment',
   'tax_assessment','municipal_tax_rate','tax_bill','tax_payment_receipt',
   'tax_incentive_agreement','municipal_revenue_receipt')),
 target_row_id TEXT NOT NULL CHECK (length(trim(target_row_id)) > 0),
 exact_locator TEXT NOT NULL CHECK (length(trim(exact_locator)) >= 4),
 expected_excerpt TEXT NOT NULL CHECK (length(trim(expected_excerpt)) > 0),
 assertion_text TEXT NOT NULL CHECK (length(trim(assertion_text)) > 0),
 assertion_kind TEXT NOT NULL CHECK (assertion_kind IN
  ('observed_fact','documented_relation','bounded_interpretation')),
 verification_status TEXT NOT NULL DEFAULT 'research_candidate' CHECK (verification_status IN
  ('research_candidate','original_record_checked','independently_reconciled','disputed','rejected')),
 checked_by TEXT,
 checked_at TIMESTAMPTZ,
 UNIQUE(target_table,target_row_id,source_record_id,exact_locator),
 CHECK (verification_status NOT IN ('original_record_checked','independently_reconciled')
        OR (checked_by IS NOT NULL AND checked_at IS NOT NULL))
);

-- A protocol is an observation of the SEARCH, not proof an action did not occur.
CREATE TABLE IF NOT EXISTS atlas_housing.search_protocol (
 protocol_id TEXT PRIMARY KEY,
 authority TEXT NOT NULL,
 database_or_portal TEXT NOT NULL,
 search_url TEXT NOT NULL CHECK(search_url ~ '^https://'),
 query_terms TEXT NOT NULL,
 filters_applied TEXT,
 search_date DATE NOT NULL,
 records_returned INTEGER CHECK(records_returned IS NULL OR records_returned >= 0),
 search_outcome TEXT NOT NULL CHECK(search_outcome IN
  ('zero_public_matches_in_defined_scope','matches_found','search_incomplete','access_blocked')),
 coverage_note TEXT NOT NULL,
 reviewed_by TEXT,
 reviewed_at TIMESTAMPTZ,
 CHECK (search_outcome <> 'zero_public_matches_in_defined_scope' OR
        (records_returned = 0 AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS atlas_housing.assertion_dispute (
 dispute_id TEXT PRIMARY KEY,
 assertion_id TEXT NOT NULL REFERENCES atlas_housing.source_assertion(assertion_id),
 contradictory_source_record_id TEXT REFERENCES atlas_housing.source_document(source_record_id),
 opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 dispute_reason TEXT NOT NULL,
 resolution TEXT,
 resolved_by TEXT,
 resolved_at TIMESTAMPTZ,
 is_active BOOLEAN NOT NULL DEFAULT true,
 CHECK(NOT(is_active = false AND (resolution IS NULL OR resolved_by IS NULL OR resolved_at IS NULL)))
);

-- An HTTP status alone is never a content integrity check.
-- `snippet_missing_candidate` is not `confirmed_change`.
CREATE TABLE IF NOT EXISTS atlas_housing.live_reference_audit (
 audit_id TEXT PRIMARY KEY,
 source_record_id TEXT NOT NULL REFERENCES atlas_housing.source_document(source_record_id),
 checked_at TIMESTAMPTZ NOT NULL,
 http_status INTEGER CHECK(http_status BETWEEN 100 AND 599),
 check_state TEXT NOT NULL CHECK (check_state IN
  ('content_verified','http_error','access_blocked','hard_404','dead_link_review_candidate',
   'parse_error','pending_manual_review','not_checked')),
 extraction_quality TEXT CHECK(extraction_quality IN ('clean','unreadable','not_attempted')),
 expected_excerpt_found BOOLEAN,
 manual_disposition TEXT NOT NULL DEFAULT 'not_reviewed' CHECK(manual_disposition IN
  ('not_reviewed','unchanged','source_changed','inconclusive')),
 manual_reviewed_by TEXT,
 manual_reviewed_at TIMESTAMPTZ,
 notes TEXT,
 CHECK(manual_disposition = 'not_reviewed' OR
       (manual_reviewed_by IS NOT NULL AND manual_reviewed_at IS NOT NULL)),
 CHECK(check_state <> 'content_verified' OR expected_excerpt_found = true),
 CHECK(check_state <> 'pending_manual_review' OR
       (http_status = 200 AND extraction_quality = 'clean' AND expected_excerpt_found = false)),
 CHECK(check_state <> 'parse_error' OR extraction_quality = 'unreadable')
);

CREATE TABLE IF NOT EXISTS atlas_housing.publication_decision (
 assertion_id TEXT PRIMARY KEY REFERENCES atlas_housing.source_assertion(assertion_id),
 publish_state TEXT NOT NULL DEFAULT 'research_only' CHECK(publish_state IN
  ('research_only','ready_for_review','approved','withdrawn')),
 approved_by TEXT,
 approved_at TIMESTAMPTZ,
 rationale TEXT NOT NULL,
 CHECK(publish_state <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

-- Fail closed if a supposedly publishable assertion doesn't point to the very
-- row and ORIGINAL SOURCE it purports to support. Safe allowlisted identifiers.
CREATE OR REPLACE FUNCTION atlas_housing.assertion_publish_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE a atlas_housing.source_assertion%ROWTYPE;
DECLARE d atlas_housing.source_document%ROWTYPE;
DECLARE column_name TEXT;
DECLARE present BOOLEAN;
BEGIN
  IF NEW.publish_state <> 'approved' THEN RETURN NEW; END IF;
  SELECT * INTO a FROM atlas_housing.source_assertion WHERE assertion_id=NEW.assertion_id;
  IF NOT FOUND OR a.verification_status NOT IN ('original_record_checked','independently_reconciled')
    OR a.checked_by IS NULL OR a.checked_at IS NULL
    OR NULLIF(trim(a.exact_locator),'') IS NULL THEN
     RAISE EXCEPTION 'Cannot approve unreviewed or unlocated assertion';
  END IF;
  SELECT * INTO d FROM atlas_housing.source_document WHERE source_record_id=a.source_record_id;
  IF NOT FOUND OR d.review_stage NOT IN ('original_record_checked','cross_source_reconciled')
    OR d.source_terms_status NOT IN ('public_reference_allowed','reuse_permitted')
    OR d.record_locator IS NULL OR d.reviewed_at IS NULL THEN
     RAISE EXCEPTION 'Publication requires official record locator, review and permissions';
  END IF;
  SELECT CASE a.target_table
   WHEN 'relationship' THEN 'relationship_id'
   WHEN 'office_tenure' THEN 'tenure_id'
   WHEN 'public_decision' THEN 'decision_node_id'
   WHEN 'roll_call' THEN 'roll_call_id'
   WHEN 'financial_event' THEN 'financial_event_id'
   WHEN 'lobbying_reference' THEN 'reference_id'
   WHEN 'rent_observation' THEN 'observation_id'
   WHEN 'housing_outcome' THEN 'outcome_id'
   WHEN 'analytic_assessment' THEN 'assessment_id'
   WHEN 'tax_assessment' THEN 'assessment_id'
   WHEN 'municipal_tax_rate' THEN 'rate_id'
   WHEN 'tax_bill' THEN 'tax_bill_id'
   WHEN 'tax_payment_receipt' THEN 'payment_receipt_id'
   WHEN 'tax_incentive_agreement' THEN 'incentive_id'
   WHEN 'municipal_revenue_receipt' THEN 'revenue_receipt_id'
   ELSE NULL END INTO column_name;
  IF column_name IS NULL THEN RAISE EXCEPTION 'Unsupported publication target'; END IF;
  EXECUTE format('SELECT EXISTS(SELECT 1 FROM atlas_housing.%I WHERE %I=$1 AND source_record_id=$2)',
        a.target_table, column_name)
     INTO present USING a.target_row_id, a.source_record_id;
  IF NOT present THEN RAISE EXCEPTION 'Assertion does not match target row/source document'; END IF;
  IF EXISTS(SELECT 1 FROM atlas_housing.assertion_dispute
             WHERE assertion_id=a.assertion_id AND is_active) THEN
     RAISE EXCEPTION 'Cannot approve a disputed assertion as verified';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER housing_gate_approval_guard
 BEFORE INSERT OR UPDATE ON atlas_housing.publication_decision
 FOR EACH ROW EXECUTE FUNCTION atlas_housing.assertion_publish_guard();

-- Publication decision is not a boolean client can flip. The public API
-- needs to query ONLY this view (with base-table grants denied).
-- Fail closed if source state changes after approval.
CREATE OR REPLACE VIEW atlas_housing.public_evidence AS
SELECT a.assertion_id,a.target_table,a.target_row_id,a.assertion_text,a.exact_locator,
       a.expected_excerpt,a.verification_status,
       d.authority,d.source_url,d.reviewed_at,p.approved_at,
       CASE WHEN latest_review.manual_disposition='source_changed'
            THEN 'manual_change_caution'
            ELSE 'verified_in_reviewed_scope' END AS display_evidence_state
FROM atlas_housing.source_assertion a
JOIN atlas_housing.source_document d ON d.source_record_id=a.source_record_id
JOIN atlas_housing.publication_decision p ON p.assertion_id=a.assertion_id
LEFT JOIN LATERAL (
 SELECT t.manual_disposition
 FROM atlas_housing.live_reference_audit t
 WHERE t.source_record_id=a.source_record_id
   AND t.manual_disposition <> 'not_reviewed'
 ORDER BY t.manual_reviewed_at DESC, t.checked_at DESC
 LIMIT 1
) latest_review ON true
WHERE p.publish_state='approved'
 AND a.verification_status IN ('original_record_checked','independently_reconciled')
 AND d.review_stage IN ('original_record_checked','cross_source_reconciled')
 AND d.source_terms_status IN ('public_reference_allowed','reuse_permitted')
 AND d.record_locator IS NOT NULL
 AND NOT EXISTS (SELECT 1 FROM atlas_housing.assertion_dispute q
                 WHERE q.assertion_id=a.assertion_id AND q.is_active);

-- Disputes must not masquerade as verified findings. The public surface can
-- provide an explicit disputed-evidence notice with inspected primary sources.
CREATE OR REPLACE VIEW atlas_housing.public_disputed_evidence AS
SELECT a.assertion_id, a.assertion_text, a.exact_locator,
       d.source_url AS claimed_source_url,
       q.dispute_reason, q.opened_at,
       contrary.source_url AS contrary_source_url,
       'disputed_not_a_verified_conclusion'::TEXT AS display_evidence_state
FROM atlas_housing.assertion_dispute q
JOIN atlas_housing.source_assertion a ON a.assertion_id=q.assertion_id
JOIN atlas_housing.source_document d ON d.source_record_id=a.source_record_id
JOIN atlas_housing.publication_decision p ON p.assertion_id=a.assertion_id
LEFT JOIN atlas_housing.source_document contrary
  ON contrary.source_record_id=q.contradictory_source_record_id
   AND contrary.review_stage IN ('original_record_checked','cross_source_reconciled')
   AND contrary.source_terms_status IN ('public_reference_allowed','reuse_permitted')
WHERE q.is_active AND p.publish_state='approved'
  AND d.review_stage IN ('original_record_checked','cross_source_reconciled')
  AND d.source_terms_status IN ('public_reference_allowed','reuse_permitted');

-- Research workspace may hold source links, candidate matches and searches.
-- None of these are published as verified relationships by this view.
-- Production reader role must have SELECT on view only, not on base tables.
COMMIT;
