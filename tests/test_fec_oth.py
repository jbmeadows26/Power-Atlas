"""Official FEC bulk OTH source-grain, privacy and direction regression tests."""
from __future__ import annotations
import csv
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts import collect_fec_oth as m
from scripts import build_dark_money as graph

class FecOthTests(unittest.TestCase):
    def row(self, transaction_type="18K", amount="15000.00", memo="", amendment="N",
            file_number="1000", sub="123", sender="C00000001", recipient="C00000002"):
        row=[""]*21
        for n,value in {1:recipient,2:amendment,3:"Q3",6:transaction_type,7:"COM",
                        8:"Private donor name must never appear in output",9:"Private city",10:"XX",
                        11:"00000",12:"Private employer",13:"Private occupation",
                        14:"09152026",15:amount,16:sender,17:"SA-ITEM-1",
                        18:file_number,19:memo,21:sub}.items():
            row[n-1]=value
        return row

    def test_direction_and_privacy(self):
        result=m.parse_row(self.row(),2026,{"C00000002"})
        self.assertEqual(result["from"],"fec:C00000001")
        self.assertEqual(result["to"],"fec:C00000002")
        self.assertEqual(result["transactionMeaning"],"contribution_received_from_registered_filer")
        payload=json.dumps(result).lower()
        for sensitive in ("private","employer","occupation","address"):
            self.assertNotIn(sensitive,payload)
        self.assertIn("committee_id=C00000002",result["source"])

    def test_reject_spending_vs_receipts_and_memo_refunds(self):
        self.assertIsNone(m.parse_row(self.row(transaction_type="24A"),2026,{"C00000002"}))
        self.assertIsNone(m.parse_row(self.row(memo="X"),2026,{"C00000002"}))
        self.assertIsNone(m.parse_row(self.row(amount="-15000"),2026,{"C00000002"}))
        self.assertIsNone(m.parse_row(self.row(sender="H0NY00001"),2026,{"C00000002"}))
        self.assertIsNone(m.parse_row(self.row(amount="200"),2026,{"C00000002"}))
        self.assertIsNone(m.parse_row(self.row(),2026,{"C00000005"}))

    def test_amendment_canonicalization(self):
        base=self.row(file_number="800",amount="11000",sub="111")
        changed=self.row(file_number="900",amount="14000",sub="222",amendment="A")
        rows,stats=m.scan_rows([base,changed,self.row(transaction_type="24K")],2026,{"C00000002"})
        self.assertEqual(stats["scannedRows"],3)
        self.assertEqual(stats["distinctEligibleReceiptItems"],1)
        self.assertEqual(stats["supersededVersions"],1)
        self.assertEqual(rows[0]["amountUSD"],14000.0)
        self.assertEqual(rows[0]["filingId"],"900")

    def test_safe_zip_stream_parse(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"oth26.zip"
            s=io.StringIO()
            writer=csv.writer(s,delimiter="|",lineterminator="\n")
            writer.writerow(self.row())
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("itoth.txt",s.getvalue())
            rows,stats=m.import_archive(path,2026,{"C00000002"})
            self.assertEqual(len(rows),1)
            self.assertEqual(stats["selectedRows"],1)

    def test_graph_uses_only_actual_file_receipts(self):
        receipt=m.parse_row(self.row(),2026,{"C00000002"})
        receipt_doc={"schema":"power-atlas.fec.oth-transfers.v1","records":[receipt],
                     "selection":{"selectedRows":1}}
        result=graph.collect_graph({"pacCommittees":[]},{"records":[]},[],receipt_doc)
        self.assertEqual(len(result["edges"]),1)
        self.assertEqual(result["metrics"]["filedTransactionReceiptEdges"],1)
        self.assertEqual(result["metrics"]["verifiedOriginalDonorAttributions"],0)
        self.assertEqual(result["edges"][0]["source"],receipt["source"])

if __name__=="__main__":
    unittest.main()
