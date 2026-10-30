"""Tests for official rollcall parsing and for missing dyadic outcome evidence."""
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from collect_authenticity_rollcalls import parse_roll,run

def xml_fixture(count=240,duplicate=False):
    votes="".join(f'<recorded-vote><legislator name-id="A{i:06d}">Member</legislator><vote>{"Yea" if i%2 else "Nay"}</vote></recorded-vote>' for i in range(count))
    if duplicate:votes+='<recorded-vote><legislator name-id="A000001">Dup</legislator><vote>Nay</vote></recorded-vote>'
    return ('<rollcall-vote><vote-metadata><action-date>10-Jan-2025</action-date><vote-question>On Passage</vote-question><vote-desc>Test procedural vote</vote-desc><vote-result>Passed</vote-result></vote-metadata><vote-data>'+votes+'</vote-data></rollcall-vote>').encode()

class OfficialHouseVoteTests(unittest.TestCase):
    def test_primary_source_parser(self):
        item=parse_roll(xml_fixture(),"https://clerk.house.gov/evs/2025/roll001.xml",2025,1)
        self.assertEqual(item["memberVotes"],240)
        self.assertEqual(item["rollCall"],1)
        self.assertEqual(item["votes"]["A000001"],"Yea")
        self.assertEqual(len(item["sourceSha256"]),64)
        self.assertNotIn("wealthBias",item)
    def test_duplicate_member_cannot_be_accepted(self):
        with self.assertRaises(ValueError):parse_roll(xml_fixture(240,True),"https://clerk.house.gov/x",2025,1)
    def test_incomplete_data_rejected(self):
        with self.assertRaises(ValueError):parse_roll(xml_fixture(3),"https://clerk.house.gov/x",2025,1)
    def test_missing_question_rejected(self):
        with self.assertRaises(ValueError):parse_roll(xml_fixture().replace(b"<vote-question>On Passage</vote-question>",b""),"https://clerk.house.gov/x",2025,1)
    def test_invalid_window_rejected_before_network(self):
        with self.assertRaises(ValueError):run(2026,150,149)
        with self.assertRaises(ValueError):run(2023,1,150)
if __name__=="__main__": unittest.main()
