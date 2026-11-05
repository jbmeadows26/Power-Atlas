"""Dark-money evidence, privacy, and provenance safety gates."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts import build_dark_money as m

ROOT = Path(__file__).resolve().parents[1]
class DarkMoneyTests(unittest.TestCase):
    def test_real_graph_is_reproducible(self):
        result = m.collect_graph(
            json.loads(m.FEC_PREVIEW.read_text()),
            json.loads(m.FEC_DISB.read_text()),
            [], m.read_json(m.FEC_OTH, {"schema":"power-atlas.fec.oth-transfers.v1","records":[],"selection":{}}))
        published = json.loads(m.OUT.read_text())
        self.assertEqual(result, published)
        self.assertEqual(result["metrics"]["fecCommitteeCycleSnapshots"], 135)
        self.assertEqual(result["metrics"]["verifiedOriginalDonorAttributions"], 0)
        self.assertFalse(any("address" in k.lower() for e in result["nodes"] for k in e))
        self.assertFalse(any("address" in k.lower() for e in result["edges"] for k in e))

    def test_two_hop_signal_requires_actual_filed_edges(self):
        doc = {"pacCommittees": []}
        records = {"records": [
            {"id":"1", "committeeId":"C00000001", "recipientCommitteeId":"C00000002",
             "date":"2026-09-01", "amountUSD":10000, "source":"https://www.fec.gov/data/"},
            {"id":"2", "committeeId":"C00000002", "recipientCommitteeId":"C00000003",
             "date":"2026-09-05", "amountUSD":9800, "source":"https://www.fec.gov/data/"}
        ]}
        result = m.collect_graph(doc, records)
        self.assertEqual(len(result["signals"]), 1)
        self.assertIn("lead only", result["signals"][0]["interpretation"].lower())
        records["records"][1]["date"] = "2026-06-01"
        self.assertFalse(m.collect_graph(doc, records)["signals"])

    def test_manual_rows_fail_closed_on_persons_and_unreviewed_ids(self):
        original = m.REVIEWED
        with tempfile.TemporaryDirectory() as td:
            m.REVIEWED = Path(td) / "input.json"
            base = {
                "id":"state:12345", "jurisdiction":"municipal",
                "reviewStatus":"human_checked_official_filing",
                "filingId":"F-987", "reviewedBy":"manual-review",
                "date":"2026-09-01", "amountUSD":1200,
                "source":"https://www.campaignfinanceboard.info/ftm/",
                "fromEntity":{"id":"nyc:corp:123","name":"Example Org LLC","entityType":"corporation"},
                "toEntity":{"id":"nyc:pac:456","name":"Example PAC","entityType":"committee"},
            }
            try:
                m.REVIEWED.write_text(json.dumps({"records":[base]}))
                self.assertEqual(len(list(m.reviewed_rows())), 1)
                base["fromEntity"]["street_address"] = "private"
                m.REVIEWED.write_text(json.dumps({"records":[base]}))
                with self.assertRaises(ValueError): list(m.reviewed_rows())
                del base["fromEntity"]["street_address"]
                base["reviewStatus"] = "ai_guess"
                m.REVIEWED.write_text(json.dumps({"records":[base]}))
                with self.assertRaises(ValueError): list(m.reviewed_rows())
            finally:
                m.REVIEWED = original

    def test_dashboard_and_navigation(self):
        ui = (ROOT/"platform/unified/dark-money.html").read_text()
        self.assertIn("dark-money-graph-v1.json", ui)
        self.assertIn("potentialSequentialPaymentLeads", ui)
        self.assertIn("Cannot trace", ui)
        self.assertIn("aria-label", ui)
        self.assertIn("municipalSection",ui)
        self.assertIn("campaign-financial-analysis-2025.json",ui)
        self.assertIn("nycOffice",ui)
        self.assertIn("irsGrants",ui)
        self.assertIn("irs-schedule-i-grants-v1.json",ui)
        self.assertIn("showIRSGrants",ui)
        home = (ROOT/"platform/unified/index.html").read_text()
        self.assertIn("dark-money.html", home)

if __name__ == "__main__":
    unittest.main()
