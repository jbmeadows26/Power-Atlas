"""Evidence publication and reference-audit safety regression tests.

No network, paid APIs, PDF downloads or external database needed.
"""
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from io import BytesIO
import unittest

from scripts.audit_live_reference import (
    Retrieved, Extracted, normalized_tokens, contains_expected,
    consecutive_404_days, inspect_reference, reviewer_disposition
)

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 12)
EXPECTED = "2.836% general property-tax rate"


def doc(text):
    return Retrieved(200, "text/html", text.encode("utf-8"))


def good_extraction(response):
    return Extracted(response.body.decode("utf-8"))


SAMPLE = (
    "New Jersey official tax rate publication for Bergen County, "
    "Cliffside Park Borough general property tax rate: "
    "2.836 % general property-tax rate, effective tax rate: 1.920."
)


class ReferenceAuditSafetyTests(unittest.TestCase):
    def check_state(self, got, state, human=False):
        self.assertEqual(got.check_state, state)
        self.assertEqual(got.human_review_required, human)
        self.assertFalse(got.public_warning)
        self.assertEqual(got.publication_action, "none")

    def test_number_punctuation_is_not_normalized_away(self):
        self.assertNotEqual(normalized_tokens("2.836"), normalized_tokens("28.36"))
        self.assertNotEqual(normalized_tokens("2.836"), normalized_tokens("2.835"))
        self.assertNotEqual(normalized_tokens("2.836"), normalized_tokens("1.920"))
        self.assertTrue(contains_expected("General tax: 2.836 % general property tax rate",
                                          EXPECTED))
        self.assertFalse(contains_expected("General tax: 28.36 % general property tax rate",
                                           EXPECTED))
        self.assertTrue(contains_expected(SAMPLE, EXPECTED))

    def test_public_snippet_found_is_checked_not_causal_proof(self):
        result = inspect_reference(EXPECTED, TODAY, lambda: doc(SAMPLE), good_extraction)
        self.check_state(result, "content_verified")
        self.assertIs(result.expected_excerpt_found, True)

    def test_cleanly_parsed_but_missing_enters_human_review_only(self):
        changed = ("New Jersey official tax data for Bergen County and Cliffside Park "
                   "Borough general property tax schedule: 2.835 percent this year.")
        result = inspect_reference(EXPECTED, TODAY, lambda: doc(changed), good_extraction)
        self.check_state(result, "pending_manual_review", human=True)
        self.assertIs(result.expected_excerpt_found, False)
        with self.assertRaises(ValueError):
            reviewer_disposition(result, reviewer_id="", reviewed_original=True,
                                 decision="source_changed")
        with self.assertRaises(ValueError):
            reviewer_disposition(result, reviewer_id="auditor-1", reviewed_original=False,
                                 decision="source_changed")
        decision = reviewer_disposition(result, reviewer_id="auditor-1",
                                        reviewed_original=True, decision="source_changed")
        self.assertEqual(decision["manual_disposition"], "source_changed")
        self.assertEqual(decision["publication_action"], "request_editorial_reassessment")
        self.assertFalse(decision["automatic_claim_retraction"])

    def test_unreadable_or_failed_pdf_extraction_is_not_stealth_edit(self):
        for extractor in (
            lambda _: Extracted(""),
            lambda _: Extracted("▒▒▒▒▒▒▒▒"),
            lambda _: Extracted("unreliable text from parser", clean=False),
            lambda _: (_ for _ in ()).throw(ValueError("broken PDF font map")),
            lambda _: (_ for _ in ()).throw(UnicodeError("corrupt encoding")),
        ):
            with self.subTest(extractor=extractor):
                result = inspect_reference(EXPECTED, TODAY,
                                           lambda: doc(SAMPLE), extractor)
                self.check_state(result, "parse_error")
                self.assertIsNone(result.expected_excerpt_found)
                with self.assertRaises(ValueError):
                    reviewer_disposition(result, reviewer_id="auditor",
                                         reviewed_original=True, decision="source_changed")

    def test_network_failures_and_rate_limited_access_do_not_change_publication(self):
        def timeout():
            raise TimeoutError("upstream connection")
        self.check_state(inspect_reference(EXPECTED, TODAY, timeout, good_extraction),
                         "http_error")
        for status, expected in ((401, "access_blocked"), (403, "access_blocked"),
                                 (429, "access_blocked"), (503, "http_error"),
                                 (500, "http_error")):
            with self.subTest(status=status):
                self.check_state(inspect_reference(EXPECTED, TODAY,
                                 lambda status=status: Retrieved(status, "text/html", b"error"),
                                 good_extraction), expected)
        block_page = ("<html><head><title>Just a moment</title></head><body>"
                      "Checking your browser before accessing the government document."
                      "</body></html>")
        self.check_state(inspect_reference(EXPECTED, TODAY,
                         lambda: doc(block_page), good_extraction), "access_blocked")

    def test_404_requires_three_distinct_consecutive_days(self):
        self.assertEqual(consecutive_404_days(TODAY, [
            (TODAY - timedelta(days=1), "hard_404"),
            (TODAY - timedelta(days=1), "hard_404")]), 2)
        previous = [(TODAY - timedelta(days=1), "hard_404"),
                    (TODAY - timedelta(days=2), "hard_404")]
        self.check_state(inspect_reference(EXPECTED, TODAY,
                         lambda: Retrieved(404, "text/html", b"Not Found"),
                         good_extraction), "hard_404")
        result = inspect_reference(EXPECTED, TODAY,
                lambda: Retrieved(404, "text/html", b"Not Found"),
                good_extraction, previous)
        self.check_state(result, "dead_link_review_candidate", human=True)
        self.assertIsNone(result.expected_excerpt_found)
        interrupted = [(TODAY - timedelta(days=1), "http_error"),
                       (TODAY - timedelta(days=2), "hard_404")]
        self.check_state(inspect_reference(EXPECTED, TODAY,
                         lambda: Retrieved(404, "text/html", b"Not Found"),
                         good_extraction, interrupted), "hard_404")

    def test_http_error_exception_cannot_count_as_content_change(self):
        def raise_404():
            raise HTTPError("https://example.gov/official.pdf", 404,
                            "Not Found", None, BytesIO())
        result = inspect_reference(EXPECTED, TODAY, raise_404, good_extraction)
        self.check_state(result, "hard_404")

    def test_blank_expected_excerpt_is_rejected(self):
        with self.assertRaises(ValueError):
            inspect_reference(" \t\n ", TODAY, lambda: doc(SAMPLE), good_extraction)

    def test_publication_gate_requires_source_assertion_review_and_dispute_exclusion(self):
        ddl = (ROOT / "schema/0004_housing_publication_gate.sql").read_text()
        for expression in (
            "source_assertion", "exact_locator TEXT NOT NULL",
            "assertion_publish_guard", "publication_decision",
            "record_locator IS NULL", "checked_by IS NULL",
            "public_evidence", "publish_state='approved'",
            "verification_status IN ('original_record_checked','independently_reconciled')",
            "source_terms_status IN ('public_reference_allowed','reuse_permitted')",
            "assertion_dispute", "is_active",
            "capture_event", "search_protocol",
            "zero_public_matches_in_defined_scope",
            "manual_disposition", "pending_manual_review",
            "source_changed"
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, ddl)
        self.assertIn("DESIGN ONLY", ddl)
        self.assertIn("not applied to production", ddl)

    def test_2024_2025_tax_rates_have_located_official_sources_and_no_pilot_claim(self):
        import json
        data = json.loads((ROOT / "data/housing/official-tax-rate-cliffside-park-2024-2025.json").read_text())
        self.assertFalse(data["fullGapClosureAllowed"])
        self.assertEqual([x["taxYear"] for x in data["observations"]], [2024, 2025])
        self.assertEqual([x["generalTaxRatePer100"] for x in data["observations"]], [2.756, 2.836])
        self.assertEqual([x["effectiveTaxRatePer100"] for x in data["observations"]], [1.966, 1.92])
        for observation in data["observations"]:
            self.assertEqual(observation["source"]["pdfPageNumber"], 2)
            self.assertTrue(observation["source"]["url"].startswith("https://www.nj.gov/"))
            self.assertIsNone(observation["source"]["documentSha256"])
        self.assertEqual({row["status"] for row in data["nextMissingLinks"]}, {"not_verified"})
        self.assertIn("receipt", [row["stage"] for row in data["nextMissingLinks"]])
        self.assertIn("political_finance", [row["stage"] for row in data["nextMissingLinks"]])


if __name__ == "__main__":
    unittest.main()
