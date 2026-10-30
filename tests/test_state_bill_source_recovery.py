"""Offline tests for the four-jurisdiction bounded source-link recovery."""
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from recover_state_bill_source_gaps import (
    BASE, PER_PAGE, STATES, detail_source, process_state, reject_reason, verify_https_official_link
)

UID = "11111111-1111-4111-8111-111111111111"


def bill(source_url=None):
    return {
        "id": UID,
        "identifier": "AB 123",
        "title": "Redistricting commission",
        "source_url": source_url,
        "status": "unknown",
    }


class StateBillSourceRecoveryTests(unittest.TestCase):
    def test_scope_and_filters(self):
        self.assertEqual(STATES, ("MD", "OK", "VT"))
        self.assertEqual(PER_PAGE, 5)
        self.assertEqual(reject_reason(bill()), "missing_source_url")
        self.assertEqual(reject_reason(bill("http://example.org/bill")), "non_https_source_url")
        self.assertIsNone(reject_reason(bill("https://leginfo.legislature.ca.gov/")))

    def test_http_to_https_requires_same_official_host_and_successful_head(self):
        class Response:
            status = 200
            def __init__(self, url):
                self.url = url
            def geturl(self):
                return self.url
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False
        def fake_head(req, timeout):
            self.assertEqual(req.get_method(), "HEAD")
            self.assertEqual(timeout, 12)
            return Response(req.full_url)
        official = bill("http://mgaleg.maryland.gov/2026RS/bills/hb/hb0123f.pdf")
        self.assertEqual(
            verify_https_official_link(official, "MD", fake_head),
            "https://mgaleg.maryland.gov/2026RS/bills/hb/hb0123f.pdf")
        self.assertIsNone(verify_https_official_link(official, "VT", fake_head))

    def test_detail_requires_matching_bill_id(self):
        def wrong_id(_):
            return {"id": "22222222-2222-4222-8222-222222222222",
                    "source_url": "https://leginfo.legislature.ca.gov/"}
        self.assertIsNone(detail_source(bill(), wrong_id))

    def test_missing_source_can_be_recovered_without_fabrication(self):
        def fake_get(url):
            if url.startswith(BASE + "/search?"):
                return {"data": [bill()], "pagination": {"total": 21}}
            self.assertEqual(url, BASE + "/bills/" + UID)
            return {"id": UID, "source_url": "https://leginfo.legislature.ca.gov/"}
        indexed = {}
        result = process_state("CA", indexed, fake_get)
        self.assertEqual(result["newCandidateRows"], 1)
        self.assertEqual(result["billDetailRequests"], 1)
        self.assertEqual(result["providerTotalMatches"], 21)
        self.assertEqual(len(indexed), 1)
        candidate = next(iter(indexed.values()))
        self.assertEqual(candidate["reviewStatus"], "third_party_index_official_source_review_required")
        self.assertIn("first_5", candidate["retrievalScope"])

    def test_http_source_only_recovers_when_detail_has_https(self):
        def fake_get(url):
            if "/search?" in url:
                return {"data": [bill("http://example.org/old")],
                        "pagination": {"total": 3}}
            return {"id": UID, "source_url": "https://example.org/official"}
        indexed = {}
        result = process_state("VT", indexed, fake_get)
        self.assertEqual(result["newCandidateRows"], 1)
        self.assertEqual(result["nonHttpsSourceSchemes"]["http"], 1)
        self.assertEqual(result["nonHttpsSourceHosts"]["example.org"], 1)
        self.assertEqual(next(iter(indexed.values()))["source"],
                         "https://example.org/official")

    def test_missing_source_stays_unverified_without_official_url(self):
        def fake_get(url):
            if "/search?" in url:
                return {"data": [bill()], "pagination": {"total": 1}}
            return {"id": UID, "source_url": None}
        indexed = {}
        result = process_state("MD", indexed, fake_get)
        self.assertEqual(result["rejectionCounts"]["missing_source_url"], 1)
        self.assertEqual(result["newCandidateRows"], 0)
        self.assertFalse(indexed)

    def test_429_stops_source_access_without_fallback(self):
        def rate_limited(url):
            raise HTTPError(url, 429, "rate limited", {}, None)
        with self.assertRaises(HTTPError) as raised:
            process_state("OK", {}, rate_limited)
        self.assertEqual(raised.exception.code, 429)

    def test_existing_record_never_overwritten(self):
        original = {"id": "state-bill-" + UID, "reviewStatus": "original"}
        indexed = {original["id"]: original}
        def fake_get(url):
            return {"data": [bill("https://leginfo.legislature.ca.gov/")],
                    "pagination": {"total": 1}}
        result = process_state("CA", indexed, fake_get)
        self.assertEqual(result["newCandidateRows"], 0)
        self.assertIs(indexed[original["id"]], original)


if __name__ == "__main__":
    unittest.main()
