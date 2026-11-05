"""IRS official e-file index filtered to a tiny audited civic nonprofit EIN list."""
import unittest
from scripts.collect_irs_focused_index import parse_index

FIELDS=["RETURN_ID","FILING_TYPE","EIN","TAX_PERIOD","SUB_DATE","TAXPAYER_NAME","RETURN_TYPE","DLN","OBJECT_ID","XML_BATCH_ID"]
ROW={"EIN":"264486735","RETURN_TYPE":"990","OBJECT_ID":"202533159349305888",
     "XML_BATCH_ID":"2025_TEOS_XML_11B","TAX_PERIOD":"202412","SUB_DATE":"2025-11-11",
     "TAXPAYER_NAME":"Sixteen Thirty Fund","RETURN_ID":"123","FILING_TYPE":"EFILE","DLN":"111"}
class IRSIndexTests(unittest.TestCase):
    def test_whitelist_prevents_unrelated_person_details(self):
        unrelated=dict(ROW,EIN="111222333",TAXPAYER_NAME="PRIVATE PERSON DO NOT PUBLISH")
        records,stats=parse_index([ROW,unrelated],FIELDS)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]["archiveMember"],"202533159349305888_public.xml")
        self.assertEqual(records[0]["ein"],"264486735")
        self.assertNotIn("PRIVATE",str(records))
        self.assertEqual(stats["rowsScanned"],2)
    def test_no_inferred_batch(self):
        broken=dict(ROW,XML_BATCH_ID="bad/../../path")
        with self.assertRaises(ValueError):parse_index([broken],FIELDS)
    def test_no_unverified_filing_identity(self):
        with self.assertRaises(ValueError):parse_index([dict(ROW,OBJECT_ID="unknown")],FIELDS)
    def test_missing_source_columns_fails_closed(self):
        with self.assertRaises(ValueError):parse_index([ROW],["EIN","OBJECT_ID"])

if __name__=="__main__":unittest.main()
