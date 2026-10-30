"""Offline regression coverage for the bounded, rate-respecting Senate LDA collector."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("atlas_collect_lda", ROOT / "scripts" / "collect_lda.py")
lda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lda)


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *_):
        return json.dumps({"results": [], "next": None}).encode("utf-8")


class LdaRequestSafetyTests(unittest.TestCase):
    def test_first_request_paced_and_no_local_time_shadowing(self):
        with patch.object(lda.time, "sleep") as sleep, patch.object(lda, "urlopen", return_value=_Response()) as open_url:
            self.assertEqual(lda.fetch("redistricting", 2026), [])
        sleep.assert_called_once_with(4.5)
        self.assertEqual(open_url.call_count, 1)
        self.assertIn("filing_year=2026", open_url.call_args.args[0].full_url)

    def test_transient_network_error_uses_one_bounded_retry(self):
        with patch.object(lda.time, "sleep") as sleep, patch.object(lda, "urlopen", side_effect=[URLError("temporary"), _Response()]) as open_url:
            self.assertEqual(lda.fetch("voting rights", 2026), [])
        self.assertEqual(open_url.call_count, 2)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [4.5, 1.0])

    def test_oversized_2026_query_uses_two_row_pages(self):
        with patch.object(lda.time, "sleep"), patch.object(lda, "urlopen", return_value=_Response()) as open_url:
            self.assertEqual(lda.fetch("congressional district", 2026), [])
        self.assertIn("page_size=2", open_url.call_args.args[0].full_url)
        self.assertEqual(open_url.call_count, 1)

    def test_429_stops_without_retry(self):
        blocked = HTTPError("https://lda.gov/api/v1/filings/", 429, "Too Many Requests", {}, None)
        with patch.object(lda.time, "sleep") as sleep, patch.object(lda, "urlopen", side_effect=blocked) as open_url:
            with self.assertRaises(HTTPError):
                lda.fetch("redistricting", 2026)
        self.assertEqual(open_url.call_count, 1)
        sleep.assert_called_once_with(4.5)


if __name__ == "__main__":
    unittest.main()
