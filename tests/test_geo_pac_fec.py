"""Regression tests for privacy-safe FEC PAC→candidate source rows."""
import io
import json
import unittest
import zipfile
from scripts import collect_geo_pac_fec as m


class GeoPACFileTests(unittest.TestCase):
    def record(self, amount="1000.00", file_no="10000", tran="TR1",
               memo="", code="24K", sub="100001", date="03152024"):
        c = [""] * 22
        c[0] = m.COMMITTEE_ID
        c[1] = "N"
        c[2] = "Q1"
        c[3] = "G2024"
        c[4] = "202404010000000000"
        c[5] = code
        c[6] = "COM"
        c[7] = "DO NOT PUBLISH CONTRIBUTOR NAME"
        c[8] = "PRIVATE CITY"
        c[9] = "AA"
        c[10] = "00000"
        c[11] = "EMPLOYER PRIVACY"
        c[12] = "OCCUPATION PRIVACY"
        c[13] = date
        c[14] = amount
        c[15] = "C00000001"
        c[16] = "H4NY01001"
        c[17] = tran
        c[18] = file_no
        c[19] = memo
        c[20] = "MEMO PRIVACY"
        c[21] = sub
        return "|".join(c)

    def pack(self, lines):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("itpas2.txt", "\n".join(lines)+"\n")
        return buf.getvalue()

    def test_parses_pac_only_and_strips_personal_fields(self):
        row = m.parse_pac_line(self.record(), 2024)
        self.assertEqual(row["recipientCommitteeId"], "C00000001")
        self.assertEqual(row["candidateId"], "H4NY01001")
        self.assertEqual(row["category"], "direct")
        self.assertNotIn("name", json.dumps(row).lower())
        self.assertNotIn("PRIVATE", json.dumps(row))
        self.assertEqual(row["amountUsd"], 1000.0)

    def test_nullable_fec_recipient_ids_do_not_create_fake_edges(self):
        raw = self.record().split("|")
        raw[15] = ""
        self.assertIsNone(m.parse_pac_line("|".join(raw), 2024))
        raw = self.record().split("|")
        raw[16] = ""
        self.assertIsNone(m.parse_pac_line("|".join(raw), 2024))
        raw = self.record().split("|")
        raw[17] = ""
        self.assertIsNone(m.parse_pac_line("|".join(raw), 2024))
        d = m.parse_archive(self.pack([
            self.record(),
            self.record(tran="TR2").replace("|C00000001|H4NY01001|", "||H4NY01001|")
        ]), 2024)
        self.assertEqual(d["matchedCommitteeRows"], 2)
        self.assertEqual(d["rowsWithoutVerifiableRecipientOrTransactionId"], 1)
        self.assertEqual(len(d["records"]), 1)

    def test_amendments_canonicalized_memo_excluded_and_types_separated(self):
        wrong = self.record().replace(m.COMMITTEE_ID, "C99999999", 1)
        blob = self.pack([
            wrong,
            self.record(file_no="9000", amount="1000", sub="1"),
            self.record(file_no="11000", amount="2000", sub="2"),
            self.record(tran="TR2", sub="3", code="24E", amount="700"),
            self.record(tran="TR3", sub="4", memo="X", amount="500"),
        ])
        d = m.parse_archive(blob, 2024)
        self.assertEqual(d["matchedCommitteeRows"], 4)
        self.assertEqual(d["amendmentVersionsSupersededHeuristic"], 1)
        self.assertEqual(d["memoRowsExcluded"], 1)
        self.assertEqual(len(d["records"]), 2)
        totals = {x["category"]: x["netReportedUsd"] for x in d["categoryTotals"]}
        self.assertEqual(totals, {"direct": 2000.0, "independent": 700.0})
        self.assertNotIn("DO NOT PUBLISH", json.dumps(d))
        self.assertEqual(len(d["archiveSha256"]), 64)

    def test_strict_file_schema_and_publishing_guard(self):
        with self.assertRaises(ValueError):
            m.parse_pac_line("malformed|row", 2024)
        with self.assertRaisesRegex(ValueError, "No GEO PAC"):
            m.parse_archive(self.pack([self.record().replace(m.COMMITTEE_ID, "C99999999")]), 2024)
        with self.assertRaisesRegex(ValueError, "Unmapped"):
            m.parse_pac_line(self.record(code="ZZZ"), 2024)
        self.assertEqual(m.archive_url(2024), "https://www.fec.gov/files/bulk-downloads/2024/pas224.zip")
        with self.assertRaises(ValueError):
            m.archive_url(2023)


if __name__ == "__main__":
    unittest.main()
