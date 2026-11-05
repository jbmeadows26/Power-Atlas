"""NYC CFB city-level finance extractor: source grain, identity, non-donor labels."""
import unittest
from scripts import collect_nyc_cfb_2025 as m

class NYCTests(unittest.TestCase):
    def rows(self,n=20):
        return [{"el_cycle":"2025","cand_name":"PUBLIC CANDIDATE "+str(i),
                 "cand_id":"A"+str(1000+i),"boro_dist":"M",
                 "office":"1","cntns_no":"15",
                 "net_cntns":"12345.67","match_amt":"6200.00",
                 "name":"PRIVATE CONTRIBUTOR MUST NOT PUBLISH",
                 "address":"PRIVATE STREET MUST NOT PUBLISH"} for i in range(n)]
    def test_only_candidate_level_without_private_donors(self):
        output=m.parse(self.rows())
        self.assertEqual(len(output),20)
        self.assertEqual(output[0]["reportedNetContributionsUSD"],12345.67)
        self.assertEqual(output[0]["office"],"Mayor")
        self.assertEqual(output[0]["contributionsClaimedForMatchingUSD"],6200.00)
        self.assertTrue(all("PRIVATE" not in str(r) for r in output))
        self.assertTrue(all(r["source"]==m.PUBLISHER for r in output))
    def test_duplicate_campaign_district_does_not_double_count(self):
        original=self.rows()
        older=dict(original[0]);older["to_stmt"]="3";older["net_cntns"]="99999"
        newer=dict(original[0]);newer["to_stmt"]="9";newer["net_cntns"]="23456.78"
        original[0]=newer
        result=m.parse(original+[older])
        self.assertEqual(len(result),20)
        latest=next(r for r in result if r["candidateId"]=="A1000")
        self.assertEqual(latest["statementThrough"],"9")
        self.assertEqual(latest["reportedNetContributionsUSD"],23456.78)
        self.assertEqual(latest["sourceRowsForCampaignDistrict"],2)
    def test_year_filter_fails_closed(self):
        rows=self.rows();rows[0]["el_cycle"]="2024"
        with self.assertRaises(ValueError):m.parse(rows)
    def test_suspect_negative_net_fails_closed(self):
        rows=self.rows();rows[0]["net_cntns"]="-4"
        with self.assertRaises(ValueError):m.parse(rows)
    def test_small_or_empty_dataset_fails_closed(self):
        with self.assertRaises(ValueError):m.parse([])

if __name__=="__main__":unittest.main()
