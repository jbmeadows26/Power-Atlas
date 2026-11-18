"""Offline fixtures for official GB frequency, IXP directory and CRL transport.

No live network requests; failures do not become false healthy indicators.
"""
from datetime import datetime,timezone,timedelta
import importlib.util
from pathlib import Path
import sys
import unittest

DIR=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location("resilience_external",DIR/"resilience_external.py")
e=importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
NOW="2026-11-18T21:00:00Z"

class PublicFeedFixtures(unittest.TestCase):
    def test_elexon_valid_frequency_and_country_scope(self):
        obj=e.grid_from_payload({"data":[
            {"frequency":49.95,"measurementTime":"2026-11-18T20:54:00Z"},
            {"frequency":50.01,"measurementTime":"2026-11-18T20:59:00Z"}]},NOW)
        self.assertEqual("observed",obj["status"])
        self.assertEqual(50.01,obj["frequencyHz"])
        self.assertEqual(60,obj["sampleAgeSeconds"])
        self.assertIn("Great Britain",obj["scope"])
    def test_elexon_stale_is_not_live(self):
        obj=e.grid_from_payload({"data":[{"frequency":50.0,"measurementTime":"2026-11-18T20:00:00Z"}]},NOW)
        self.assertEqual("stale",obj["status"])
    def test_elexon_out_of_bounds_is_screening_warning(self):
        obj=e.grid_from_payload({"data":[{"frequency":49.4,"measurementTime":"2026-11-18T20:59:00Z"}]},NOW)
        self.assertEqual("warning",obj["status"])
        self.assertNotIn("global",obj["scope"].lower())
    def test_elexon_unreported_is_not_zero(self):
        obj=e.grid_from_payload({"data":[{"frequency":"0","measurementTime":"2026-11-18T20:59:00Z"}]},NOW)
        self.assertEqual("unavailable",obj["status"])
        self.assertNotIn("frequencyHz",obj)
    def test_elexon_future_timestamp_cannot_be_healthy(self):
        obj=e.grid_from_payload({"data":[{"frequency":50.0,"measurementTime":"2026-11-18T21:12:00Z"}]},NOW)
        self.assertEqual("stale",obj["status"])
    def test_ixp_directory_is_not_utilization(self):
        obj=e.ixp_from_payload({"data":[{"id":123,"name":"AMS-IX","country":"NL"}]},NOW)
        self.assertEqual("observed",obj["status"])
        self.assertEqual("ixp_directory",obj["category"])
        self.assertIn("no live congestion",obj["scope"])
        self.assertNotIn("utilizationPct",obj)
    def test_ixp_missing_record_not_assumed_offline(self):
        obj=e.ixp_from_payload({"data":[]},NOW)
        self.assertEqual("unavailable",obj["status"])
    def test_pki_head_403_is_unknown_not_an_outage(self):
        obj=e.crl_transport_from_result(403,100.5,NOW)
        self.assertEqual("unavailable",obj["status"])
        self.assertIn("does not establish",obj["detail"])
    def test_pki_head_200_is_transport_only(self):
        obj=e.crl_transport_from_result(200,40,NOW)
        self.assertEqual("observed",obj["status"])
        self.assertIn("No OCSP query",obj["scope"])
    def test_elexon_injected_network_function(self):
        def fake(url,timeout):
            self.assertIn("from=",url)
            self.assertIn("system/frequency",url)
            return {"data":[{"frequency":50.0,"measurementTime":"2026-11-18T20:59:00Z"}]}
        obj=e.probe_gb_frequency(fake,NOW)
        self.assertEqual("observed",obj["status"])
    def test_ixp_injected_network_function(self):
        def fake(url,timeout):
            self.assertIn("AMS-IX",url)
            return {"data":[{"id":17,"name":"AMS-IX"}]}
        obj=e.probe_ixp_directory(fake,NOW)
        self.assertEqual("observed",obj["status"])
    def test_failing_source_cannot_infer_normality(self):
        def down(url,timeout):
            raise TimeoutError("offline")
        self.assertEqual("unavailable",e.probe_gb_frequency(down,NOW)["status"])
        self.assertEqual("unavailable",e.probe_ixp_directory(down,NOW)["status"])

if __name__=="__main__":
    unittest.main()
