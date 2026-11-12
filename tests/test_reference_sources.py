"""Reference-first source index must never imply data ingestion or gap closure."""
import unittest
from urllib.parse import urlsplit
from scripts.reference_sources import BACKLOG, INDEX, build, SCHEMA
import json


class ReferenceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))

    def test_index_matches_authoritative_backlog(self):
        self.assertEqual(self.actual, build())
        self.assertEqual(self.actual["schema"], SCHEMA)
        self.assertEqual(len(self.actual["sources"]), len(self.backlog["verifiedEntryPoints"]))

    def test_interim_is_reference_only(self):
        self.assertEqual(self.actual["activeMode"], "reference")
        self.assertTrue(self.actual["integrityPolicy"]["noAutomaticRecordDownload"])
        self.assertTrue(self.actual["integrityPolicy"]["noImplicitGapClosure"])
        self.assertTrue(self.actual["integrityPolicy"]["piHardwareNotYetActivated"])
        for s in self.actual["sources"]:
            self.assertEqual(s["interimAccess"], "direct_source_reference")
            self.assertEqual(s["retrievalStatus"], "source_entry_point_identified_not_evidence_ingested")
            self.assertNotIn("closed", s)
            self.assertNotIn("records", s)

    def test_browser_quick_reference_reuses_local_source_index(self):
        from scripts.reference_sources import ROOT
        page = (ROOT / "platform/unified/source-audit.html").read_text(encoding="utf-8")
        frontend = (ROOT / "platform/unified/quick-reference.js").read_text(encoding="utf-8")
        life = (ROOT / "platform/unified/my-life.html").read_text(encoding="utf-8")
        self.assertIn('id="quick-reference"', page)
        self.assertIn('id="quickReferenceResults"', page)
        self.assertIn('<script src="quick-reference.js" defer></script>', page)
        self.assertIn("./data/source-reference-index-v1.json", frontend)
        self.assertIn("safeHttps", frontend)
        self.assertIn("source-audit.html#quick-reference", life)
        self.assertIn("underlying records are not yet verified", frontend)
        self.assertNotIn("oth26.zip", frontend)
        self.assertNotIn("archiveCandidateURL", frontend)

    def test_urls_and_gate_bindings(self):
        gates = set(self.backlog["corpusSnapshot"].keys())
        known = {s["id"] for s in self.backlog["verifiedEntryPoints"]}
        self.assertEqual({s["id"] for s in self.actual["sources"]}, known)
        for s in self.actual["sources"]:
            for url in (s["officialReferenceURL"], s["archiveCandidateURL"]):
                if url:
                    self.assertEqual(urlsplit(url).scheme, "https")
            self.assertTrue(s["linkedGateIDs"])
        recap = next(s for s in self.actual["sources"] if s["id"] == "recap-archive")
        self.assertEqual(recap["authority"], "secondary_mirror")


if __name__ == "__main__":
    unittest.main()
