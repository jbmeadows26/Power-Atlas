"""IRS 990 Schedule I parsing: only documented organizational grants."""
import unittest
from scripts.parse_irs_schedule_i import parse_xml
URL="https://apps.irs.gov/pub/epostcard/990/xml/2025/2025_TEOS_XML_01A.zip"
MEMBER="202540000001234.xml"
GOOD=b"""<?xml version="1.0" encoding="utf-8"?>
<Return xmlns="http://www.irs.gov/efile">
<ReturnHeader><TaxYr>2024</TaxYr>
<Filer><EIN>123456789</EIN><BusinessName><BusinessNameLine1Txt>PUBLIC GRANT FOUNDATION</BusinessNameLine1Txt></BusinessName></Filer>
</ReturnHeader><ReturnData><IRS990ScheduleI>
<RecipientTable><RecipientBusinessName><BusinessNameLine1Txt>PUBLIC CIVIC GROUP</BusinessNameLine1Txt></RecipientBusinessName>
<RecipientEIN>987654321</RecipientEIN><CashGrantAmt>45000</CashGrantAmt>
<RecipientUSAddress><AddressLine1Txt>PRIVATE 123 STREET</AddressLine1Txt></RecipientUSAddress></RecipientTable>
<RecipientTable><RecipientPersonNm>Private person</RecipientPersonNm>
<CashGrantAmt>50000</CashGrantAmt></RecipientTable>
</IRS990ScheduleI></ReturnData></Return>"""
class IrsScheduleITests(unittest.TestCase):
    def test_only_org_ein_grants(self):
        records=parse_xml(GOOD,URL,MEMBER)
        self.assertEqual(len(records),1)
        row=records[0]
        self.assertEqual(row["from"],"irs-ein:123456789")
        self.assertEqual(row["to"],"irs-ein:987654321")
        self.assertEqual(row["amountUSD"],45000)
        self.assertIn("not_campaign_contribution",row["evidenceType"])
        self.assertNotIn("PRIVATE",str(records))
    def test_official_source_only(self):
        with self.assertRaises(ValueError):
            parse_xml(GOOD,"https://bad.test/irs.zip",MEMBER)
    def test_external_entity_and_doctype_rejected(self):
        with self.assertRaises(ValueError):
            parse_xml(b'<!DOCTYPE foo [<!ENTITY x SYSTEM "file:///etc/passwd">]>'+GOOD,URL,MEMBER)
    def test_bad_member_rejected(self):
        with self.assertRaises(ValueError):
            parse_xml(GOOD,URL,"../../do-not-process.xml")
    def test_missing_filer_identity_rejected(self):
        with self.assertRaises(ValueError):
            parse_xml(GOOD.replace(b"123456789",b"UNKNOWN"),URL,MEMBER)

if __name__=="__main__":
    unittest.main()
