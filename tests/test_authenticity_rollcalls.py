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
    def test_aye_no_normalization_with_auditable_original_labels(self):
        raw=xml_fixture().replace(b"<vote>Yea</vote>",b"<vote>Aye</vote>").replace(b"<vote>Nay</vote>",b"<vote>No</vote>")
        result=parse_roll(raw,"https://clerk.house.gov/evs/2025/roll021.xml",2025,21)
        self.assertEqual(result["memberVotes"],240)
        self.assertEqual(result["voteKind"],"recorded_yea_nay_or_procedural")
        self.assertEqual(result["votes"]["A000001"],"Yea")
        self.assertEqual(result["votes"]["A000002"],"Nay")
        self.assertEqual(result["originalVoteLabelCounts"],{"Aye":120,"No":120})

    def test_speaker_choice_preserves_named_candidates(self):
        raw=xml_fixture().replace(b"On Passage",b"Election of the Speaker").replace(b"<vote>Yea</vote>",b"<vote>Candidate One</vote>").replace(b"<vote>Nay</vote>",b"<vote>Candidate Two</vote>")
        result=parse_roll(raw,"https://clerk.house.gov/evs/2025/roll002.xml",2025,2)
        self.assertEqual(result["memberVotes"],240)
        self.assertEqual(result["voteKind"],"speaker_candidate_selection")
        self.assertEqual(result["votes"]["A000001"],"Candidate One")
        self.assertEqual(result["votes"]["A000002"],"Candidate Two")
        self.assertNotIn("Yea",result["originalVoteLabelCounts"])

    def test_named_candidates_not_admitted_into_ordinary_yes_no_roll(self):
        raw=xml_fixture().replace(b"<vote>Yea</vote>",b"<vote>Candidate One</vote>")
        with self.assertRaises(ValueError):
            parse_roll(raw,"https://clerk.house.gov/evs/2025/roll021.xml",2025,21)

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
