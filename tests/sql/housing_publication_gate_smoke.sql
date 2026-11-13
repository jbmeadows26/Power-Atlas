-- Runs against an isolated PostgreSQL database ONLY. All rows are test fixtures.
-- The 2.836 figure illustrates a documented municipal rate, not a property tax bill.
INSERT INTO atlas_housing.source_document (
 source_record_id,authority,source_url,record_locator,public_access_status,
 source_terms_status,review_stage,reviewed_at
) VALUES (
 'smoke-nj-rate-2025','New Jersey Division of Taxation',
 'https://www.nj.gov/treasury/taxation/pdf/lpt/gtr/2025taxrates.pdf',
 'PDF page 2, row CLIFFSIDE PARK BORO',
 'live_record','public_reference_allowed','original_record_checked',now()
);

INSERT INTO atlas_housing.municipal_tax_rate (
 rate_id,state_code,municipality,tax_year,rate_kind,
 dollars_per_100_taxable_assessed,source_record_id
) VALUES ('smoke-rate','NJ','Cliffside Park',2025,'general',2.836,'smoke-nj-rate-2025');

INSERT INTO atlas_housing.source_assertion (
 assertion_id,source_record_id,target_table,target_row_id,exact_locator,
 expected_excerpt,assertion_text,assertion_kind,verification_status
) VALUES (
 'smoke-assertion','smoke-nj-rate-2025','municipal_tax_rate','smoke-rate',
 'PDF page 2, CLIFFSIDE PARK BORO, general rate column',
 '2.836','2025 Cliffside Park borough general rate: 2.836 per $100 of assessed value',
 'observed_fact','research_candidate'
);

-- Draft claim must fail gate even if someone flips approval fields directly.
DO $$
DECLARE rejected BOOLEAN:=false;
BEGIN
 BEGIN
  INSERT INTO atlas_housing.publication_decision
    (assertion_id,publish_state,approved_by,approved_at,rationale)
    VALUES ('smoke-assertion','approved','researcher',now(),'should fail because unreviewed');
 EXCEPTION WHEN OTHERS THEN rejected:=true;
 END;
 IF NOT rejected THEN RAISE EXCEPTION 'FAIL: research candidate was approved'; END IF;
END $$;

UPDATE atlas_housing.source_assertion
SET verification_status='original_record_checked',checked_by='smoke-reviewer',checked_at=now()
WHERE assertion_id='smoke-assertion';

INSERT INTO atlas_housing.publication_decision (
 assertion_id,publish_state,approved_by,approved_at,rationale
) VALUES ('smoke-assertion','approved','senior-editor',now(),
          'Original NJ official PDF page 2 tax-rate row checked; narrow municipal rate only.');

DO $$
DECLARE n INTEGER;
BEGIN
 SELECT count(*) INTO n FROM atlas_housing.public_evidence WHERE assertion_id='smoke-assertion';
 IF n<>1 THEN RAISE EXCEPTION 'FAIL: reviewed, located assertion not visible'; END IF;
END $$;

-- A reviewed assertion with wrong target_row_id must fail even when the
-- source itself is original and already approved for public use.
INSERT INTO atlas_housing.source_assertion (
 assertion_id,source_record_id,target_table,target_row_id,exact_locator,
 expected_excerpt,assertion_text,assertion_kind,verification_status,
 checked_by,checked_at
) VALUES (
 'smoke-missing-row','smoke-nj-rate-2025','municipal_tax_rate','no-such-rate-row',
 'PDF page 2, CLIFFSIDE PARK BORO, general rate column',
 '2.836','Unmatched target row must fail review','observed_fact',
 'original_record_checked','smoke-reviewer',now()
);
DO $$
DECLARE rejected BOOLEAN:=false;
BEGIN
 BEGIN
  INSERT INTO atlas_housing.publication_decision
    (assertion_id,publish_state,approved_by,approved_at,rationale)
    VALUES ('smoke-missing-row','approved','senior-editor',now(),'should reject phantom row');
 EXCEPTION WHEN OTHERS THEN rejected:=true;
 END;
 IF NOT rejected THEN RAISE EXCEPTION 'FAIL: phantom target row was approved'; END IF;
END $$;

-- A later recorded source dispute must not continue as verified.
INSERT INTO atlas_housing.assertion_dispute
 (dispute_id,assertion_id,dispute_reason,is_active)
VALUES ('smoke-dispute','smoke-assertion','Dispute test; no real-world dispute implied',true);

DO $$
DECLARE verified_n INTEGER; DECLARE disputed_n INTEGER;
BEGIN
 SELECT count(*) INTO verified_n FROM atlas_housing.public_evidence WHERE assertion_id='smoke-assertion';
 SELECT count(*) INTO disputed_n FROM atlas_housing.public_disputed_evidence WHERE assertion_id='smoke-assertion';
 IF verified_n<>0 OR disputed_n<>1 THEN
  RAISE EXCEPTION 'FAIL: disputed claim must be flagged, not verified';
 END IF;
END $$;

UPDATE atlas_housing.assertion_dispute
SET is_active=false,resolution='Fixture completed',resolved_by='smoke-reviewer',resolved_at=now()
WHERE dispute_id='smoke-dispute';

-- Automated missing snippet is not itself a government document change.
INSERT INTO atlas_housing.live_reference_audit
(audit_id,source_record_id,checked_at,http_status,check_state,extraction_quality,
 expected_excerpt_found,manual_disposition,notes)
VALUES
('smoke-pending','smoke-nj-rate-2025',now(),200,'pending_manual_review','clean',
false,'not_reviewed','Snippet absent in clean text; needs human assessment');

DO $$
DECLARE state TEXT;
BEGIN
 SELECT display_evidence_state INTO state FROM atlas_housing.public_evidence
  WHERE assertion_id='smoke-assertion';
 IF state<>'verified_in_reviewed_scope' THEN
  RAISE EXCEPTION 'FAIL: unreviewed disappearance produced public accusation';
 END IF;
END $$;

-- Only a human reviewed change creates the caution state.
INSERT INTO atlas_housing.live_reference_audit
(audit_id,source_record_id,checked_at,http_status,check_state,extraction_quality,
 expected_excerpt_found,manual_disposition,manual_reviewed_by,manual_reviewed_at,notes)
VALUES
('smoke-reviewed','smoke-nj-rate-2025',now(),200,'pending_manual_review','clean',
false,'source_changed','senior-editor',now(),'Synthetic editorial change fixture; not a real government edit');

DO $$
DECLARE state TEXT;
BEGIN
 SELECT display_evidence_state INTO state FROM atlas_housing.public_evidence
  WHERE assertion_id='smoke-assertion';
 IF state<>'manual_change_caution' THEN
  RAISE EXCEPTION 'FAIL: manually confirmed drift did not generate caution';
 END IF;
END $$;

-- A later human review may clear an earlier caution; never make the caution
-- permanent merely because a prior manual audit exists in history.
INSERT INTO atlas_housing.live_reference_audit
(audit_id,source_record_id,checked_at,http_status,check_state,extraction_quality,
 expected_excerpt_found,manual_disposition,manual_reviewed_by,manual_reviewed_at,notes)
VALUES
('smoke-cleared','smoke-nj-rate-2025',now()+interval '1 minute',200,'content_verified','clean',
true,'unchanged','senior-editor',now()+interval '1 minute','Synthetic cleared fixture');

DO $$
DECLARE state TEXT;
BEGIN
 SELECT display_evidence_state INTO state FROM atlas_housing.public_evidence
  WHERE assertion_id='smoke-assertion';
 IF state<>'verified_in_reviewed_scope' THEN
  RAISE EXCEPTION 'FAIL: latest reviewed status was not respected';
 END IF;
END $$;

SELECT 'Housing epistemic publication gate smoke PASS' AS result;
