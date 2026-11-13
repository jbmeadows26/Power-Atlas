"""Live-reference audit must detect errors without accusing public agencies."""
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock

from scripts.audit_live_reference import (
    AuditOutcome, Extracted, Retrieved, contains_expected, inspect_reference,
    normalized_tokens, reviewer_disposition,
)

TODAY = date(2026, 11, 12)
GOOD = ("OFFICIAL MUNICIPAL TAX RATE REPORT. Bergen County. "
        "Cliffside Park BORO general tax rate 2.836, effective rate 1.920 "
        "per one hundred dollars of assessed valuation.").encode()


def inspect(*, response=None, parser=None, fetcher=None, history=(), expected="2.836"):
    return inspect_reference(
        expected, TODAY,
        fetch=fetcher if fetcher is not None else lambda: response,
        extract=parser if parser is not None else
            lambda r: Extracted(r.body.decode("utf-8", errors="replace")),
        prior_checks=history
    )


class ReferenceAuditTests(unittest.TestCase):
    def test_timeout_leaves_publication_and_user_warning_unchanged(self):
        out = inspect(fetcher=Mock(side_effect=TimeoutError("slow")),
                      parser=Mock(side_effect=AssertionError("extractor must not run")))
        self.assertEqual(out.check_state, "http_error")
        self.assertEqual(out.publication_action, "none")
        self.assertFalse(out.public_warning)

    def test_503_is_not_a_changed_document(self):
        out = inspect(response=Retrieved(503, "text/html", b"503"))
        self.assertEqual(out.check_state, "http_error")
        self.assertFalse(out.human_review_required)

    def test_access_challenge_is_access_blocked(self):
        out = inspect(response=Retrieved(200, "text/html", b"<title>Just a moment</title> Verify you are human"))
        self.assertEqual(out.check_state, "access_blocked")
        self.assertFalse(out.public_warning)

    def test_unreadable_pdf_text_is_parse_error(self):
        out = inspect(response=Retrieved(200, "application/pdf", b"%PDF-1.6 binary"),
                      parser=lambda _r: Extracted("\ufffd" * 350, clean=False))
        self.assertEqual(out.check_state, "parse_error")
        self.assertIsNone(out.expected_excerpt_found)
        self.assertFalse(out.public_warning)

    def test_pdf_parser_throw_is_parse_error(self):
        out = inspect(response=Retrieved(200, "application/pdf", b"%PDF-1.6"),
                      parser=Mock(side_effect=ValueError("text extraction failed")))
        self.assertEqual(out.check_state, "parse_error")

    def test_http200_clean_text_missing_excerpt_requires_human_review_only(self):
        body = ("OFFICIAL MUNICIPAL TAX RATE REPORT. Bergen County. "
                "Cliffside Park 2.935 general rate in this table.").encode()
        out = inspect(response=Retrieved(200, "text/plain", body))
        self.assertEqual(out.check_state, "pending_manual_review")
        self.assertFalse(out.expected_excerpt_found)
        self.assertTrue(out.human_review_required)
        self.assertEqual(out.publication_action, "none")
        self.assertFalse(out.public_warning)

    def test_normalized_whitespace_and_punctuation_match(self):
        out = inspect(response=Retrieved(200, "text/plain", GOOD))
        self.assertEqual(out.check_state, "content_verified")
        self.assertTrue(out.expected_excerpt_found)
        self.assertFalse(out.public_warning)
        self.assertTrue(contains_expected("Cliffside \n Park, BORO  2.836!", "BORO 2.836"))

    def test_numeric_decimal_points_are_not_erased(self):
        self.assertNotEqual(normalized_tokens("2.836"), normalized_tokens("28.36"))
        self.assertFalse(contains_expected("official tax figure is 28.36 per year", "2.836"))
        self.assertFalse(contains_expected("official tax figure is 2836 per year", "2.836"))

    def test_first_404_is_not_record_scrubbing(self):
        out = inspect(response=Retrieved(404, "text/html", b""))
        self.assertEqual(out.check_state, "hard_404")
        self.assertFalse(out.public_warning)
        self.assertFalse(out.human_review_required)

    def test_three_distinct_consecutive_days_404_flag_review(self):
        history = [(date(2026, 11, 10), "hard_404"),
                   (date(2026, 11, 11), "hard_404")]
        out = inspect(response=Retrieved(404, "text/html", b""), history=history)
        self.assertEqual(out.check_state, "dead_link_review_candidate")
        self.assertTrue(out.human_review_required)
        self.assertFalse(out.public_warning)

    def test_404_not_consecutive_is_not_three_day_signal(self):
        history = [(date(2026, 11, 8), "hard_404"),
                   (date(2026, 11, 11), "hard_404")]
        out = inspect(response=Retrieved(404, "text/html", b""), history=history)
        self.assertEqual(out.check_state, "hard_404")

    def test_empty_expected_excerpt_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect(expected="  ")

    def test_reviewer_must_inspect_original_before_declaring_change(self):
        outcome = inspect(response=Retrieved(200, "text/html",
                            b"An official record has a new amount and readable source data."))
        with self.assertRaises(ValueError):
            reviewer_disposition(outcome, reviewer_id="", reviewed_original=True, decision="source_changed")
        with self.assertRaises(ValueError):
            reviewer_disposition(outcome, reviewer_id="editor", reviewed_original=False, decision="source_changed")
        result = reviewer_disposition(outcome, reviewer_id="editor", reviewed_original=True, decision="source_changed")
        self.assertEqual(result["publication_action"], "request_editorial_reassessment")
        self.assertFalse(result["automatic_claim_retraction"])

    def test_cannot_declare_changed_from_parse_failure(self):
        bad = inspect(response=Retrieved(200, "application/pdf", b"%PDF header"),
                      parser=Mock(side_effect=ValueError("unreadable")))
        with self.assertRaises(ValueError):
            reviewer_disposition(bad, reviewer_id="editor", reviewed_original=True, decision="source_changed")

    def test_schema_requires_source_locator_review_and_public_gate(self):
        root = Path(__file__).resolve().parents[1]
        migrations = [(root / f"schema/{p}").read_text(encoding="utf-8")
                      for p in ("0002_housing_temporal_evidence.sql",
                                "0003_housing_tax_receipts.sql",
                                "0004_housing_publication_gate.sql")]
        combined = "\n".join(migrations)
        for table in ("tax_assessment", "tax_bill", "tax_payment_receipt",
                      "tax_incentive_agreement", "municipal_revenue_receipt",
                      "source_assertion", "archive_attempt", "search_protocol",
                      "live_reference_audit", "assertion_dispute", "publication_decision"):
            self.assertIn(f"atlas_housing.{table}", combined)
        self.assertIn("exact_locator TEXT NOT NULL", combined)
        self.assertIn("assertion_publish_guard", combined)
        self.assertIn("CREATE OR REPLACE VIEW atlas_housing.public_evidence", combined)
        self.assertIn("approved_by IS NOT NULL", combined)
        self.assertIn("zero_public_matches_in_defined_scope", combined)
        self.assertIn("pending_manual_review", combined)
        self.assertNotIn("is_published BOOLEAN", combined)


if __name__ == "__main__":
    unittest.main()
