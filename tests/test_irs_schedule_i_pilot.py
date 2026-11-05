"""Live-target IRS ZIP pilot: identity, manifest, privacy, file bounds."""
import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import collect_irs_schedule_i_pilot as pilot

class IRSPilotTests(unittest.TestCase):
    def test_exact_filing_locator(self):
        row={"ein":"264486735","filingId":"202533159349305888",
             "archiveURL":"https://apps.irs.gov/pub/epostcard/990/xml/2025/2025_TEOS_XML_11B.zip",
             "archiveMember":"202533159349305888_public.xml",
             "returnType":"990",
             "reviewStatus":"official_irs_index_entry_nonprofit_profile_independently_identified"}
        self.assertEqual(pilot.check_filing(row)[1],"202533159349305888_public.xml")
        with self.assertRaises(ValueError):
            pilot.check_filing(dict(row,ein="999999999"))
        with self.assertRaises(ValueError):
            pilot.check_filing(dict(row,archiveMember="../../secret.xml"))
    def test_zip_membership_strict_and_limited(self):
        member="202533159349305888_public.xml"
        with TemporaryDirectory() as td:
            path=Path(td)/"official-irs.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr(member,b"<Return/>")
                z.writestr("other_public.xml",b"<Ignore/>")
            self.assertEqual(pilot.read_target_xml(path,member),b"<Return/>")
            with self.assertRaises(ValueError):
                pilot.read_target_xml(path,"wrong_public.xml")
    def test_parser_no_personal_donors(self):
        from tests.test_irs_schedule_i import GOOD,URL,MEMBER
        from scripts.parse_irs_schedule_i import parse_xml
        rows=parse_xml(GOOD,URL,MEMBER)
        self.assertEqual(len(rows),1)
        self.assertFalse(any("PRIVATE" in str(x) for x in rows))

if __name__=="__main__":unittest.main()
