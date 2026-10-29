"""Offline checks for the public GovInfo congressional cosponsorship collector."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"scripts/collect_hyperpartisanship_govinfo.py"
spec=importlib.util.spec_from_file_location("hyper_govinfo",PATH)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def sample(sponsor="A000001", cosponsors=(("A000002", "", ""),)):
    cos="".join(
        "<item><identifiers><bioguideId>"+pid+"</bioguideId></identifiers>"
        "<sponsorshipDate>"+date+"</sponsorshipDate>"
        "<sponsorshipWithdrawnDate>"+withdraw+"</sponsorshipWithdrawnDate></item>"
        for pid,date,withdraw in cosponsors
    )
    return (
        "<billStatus><bill><congress>119</congress><billType>H</billType><billNumber>23</billNumber>"
        "<introducedDate>2026-01-10</introducedDate>"
        "<sponsors><item><identifiers><bioguideId>"+sponsor+"</bioguideId></identifiers></item></sponsors>"
        "<cosponsors>"+cos+"</cosponsors>"
        "<lastAction><actionDate>2026-01-20</actionDate></lastAction>"
        "</bill></billStatus>"
    ).encode()

class GovInfoParsingTests(unittest.TestCase):
    def test_detects_documented_cross_party_sponsor_relationship(self):
        r=mod.parse_bill(sample(), "hr", "https://www.govinfo.gov/example", {"A000001":"D","A000002":"R"})
        self.assertEqual(r["id"], "119-hr-23")
        self.assertIs(r["knownCrossPartyCosponsor"], True)
        self.assertEqual(r["activeCosponsorCount"], 1)
        self.assertEqual(r["introducedDate"], "2026-01-10")
        self.assertEqual(r["lastActionDate"], "2026-01-20")

    def test_withdrawn_cosponsor_cannot_be_counted_as_active(self):
        r=mod.parse_bill(sample(cosponsors=(("A000002","2026-01-10","2026-02-01"),)), "hr", "https://www.govinfo.gov/example", {"A000001":"D","A000002":"R"})
        self.assertIs(r["knownCrossPartyCosponsor"], False)
        self.assertEqual(r["activeCosponsorCount"],0)
        self.assertEqual(r["withdrawnCosponsorCount"],1)

    def test_unknown_party_must_not_be_assumed_to_be_co_party(self):
        r=mod.parse_bill(sample(), "hr", "https://www.govinfo.gov/example", {"A000001":"D"})
        self.assertIsNone(r["knownCrossPartyCosponsor"])
        self.assertEqual(r["activeCosponsorUnknownPartyCount"],1)

    def test_missing_xml_number_uses_verified_filename(self):
        official = "https://www.govinfo.gov/bulkdata/BILLSTATUS/119/hr/BILLSTATUS-119hr23.xml"
        xml = sample().replace(b"<billNumber>23</billNumber>", b"<billNumber></billNumber>")
        r = mod.parse_bill(xml, "hr", official, {"A000001":"D", "A000002":"R"})
        self.assertEqual(r["billNumber"], 23)
        self.assertEqual(r["billNumberOrigin"], "official_BILLSTATUS_filename_fallback")

    def test_conflicting_xml_and_verified_filename_is_rejected(self):
        official = "https://www.govinfo.gov/bulkdata/BILLSTATUS/119/hr/BILLSTATUS-119hr24.xml"
        with self.assertRaises(ValueError):
            mod.parse_bill(sample(), "hr", official, {"A000001":"D", "A000002":"R"})

    def test_missing_cosponsor_identity_is_preserved_unknown_not_guessed(self):
        xml=sample().replace(b"<bioguideId>A000002</bioguideId>",b"<bioguideId></bioguideId>")
        r=mod.parse_bill(xml,"hr","https://www.govinfo.gov/example",{"A000001":"D"})
        self.assertEqual(r["cosponsorSourceMissingBioguideCount"],1)
        self.assertEqual(r["activeCosponsorUnknownPartyCount"],1)
        self.assertIsNone(r["knownCrossPartyCosponsor"])

    def test_wrong_congress_is_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_bill(sample().replace(b"<congress>119</congress>",b"<congress>118</congress>"),"hr","https://www.govinfo.gov/example",{"A000001":"D"})

    def test_missing_sponsor_is_not_imputed(self):
        r=mod.parse_bill(sample(sponsor="A000001"),"hr","https://www.govinfo.gov/example",{"A000002":"R"})
        self.assertIsNone(r["sponsorPartyCrosswalk"])
        self.assertIsNone(r["knownCrossPartyCosponsor"])

if __name__=="__main__":
    unittest.main()
