"""Offline tests for the historical source crosswalk and Voteview derivation."""
from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/hyperpartisanship/congress-baseline-v1.json"
CANONICAL = ROOT / "data/hyperpartisanship/baseline-v1.json"
SCRIPT = ROOT / "scripts/collect_hyperpartisanship_voteview.py"
spec = importlib.util.spec_from_file_location("voteview_collector", SCRIPT)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

class BaselineCrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(BASELINE.read_text(encoding="utf-8"))
        cls.records = {r["congress"]: r for r in cls.doc["records"]}
        cls.canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
        cls.comparison = {r["congress"]: r for r in cls.canonical["series"]}

    def test_scope_and_provenance(self):
        self.assertEqual(self.doc["schema"], "power-atlas.hyperpartisanship.congress-baseline.v1")
        self.assertEqual(set(self.records), set(range(100, 120)))
        self.assertEqual(set(self.comparison), set(range(100, 120)))
        self.assertEqual(len(self.doc["sourceRegistry"]), 2)
        self.assertTrue(all(r["url"].startswith("https://") for r in self.doc["sourceRegistry"]))

    def test_independent_transcriptions_reconcile(self):
        for n in range(100, 120):
            a, b = self.records[n], self.comparison[n]
            self.assertEqual(a["pewPreElection"]["substantivePublicLaws"], b["substantive_laws_pre_election"])
            self.assertEqual(a["pewPreElection"]["ceremonialPublicLaws"], b["ceremonial_laws_pre_election"])
            if n < 119:
                self.assertEqual(a["senateCloture"]["motionsFiled"], b["cloture_motions_filed"])
                self.assertEqual(a["senateCloture"]["clotureVotes"], b["cloture_votes"])
                self.assertEqual(a["senateCloture"]["clotureInvoked"], b["cloture_invoked"])
            else:
                self.assertIsNone(a["senateCloture"])

    def test_explicit_causal_and_timing_gates(self):
        self.assertEqual(self.records[119]["pewPreElection"]["cutoff"], "2026-10-14")
        self.assertTrue(self.doc["measurementSafeguards"]["differentTimeWindows"])
        self.assertTrue(self.doc["measurementSafeguards"]["causalInterpretationProhibited"])
        self.assertTrue(self.doc["measurementSafeguards"]["nominationAndLegislationNotSeparated"])

class VoteviewCodingTests(unittest.TestCase):
    def test_opposed_majorities_and_code_exclusions(self):
        key = (118, "House")
        members = {(*key, str(i)): ("D" if i <= 105 else "R") for i in range(1, 211)}
        ideologies = {key: {"D": [-0.3] * 105, "R": [0.4] * 105}}
        rows = [{"congress": "118", "chamber": "House", "rollnumber": "1", "icpsr": str(i), "cast_code": "1" if i <= 105 else "6"} for i in range(1, 211)]
        rows += [{"congress": "118", "chamber": "House", "rollnumber": "2", "icpsr": str(i), "cast_code": "9"} for i in range(1, 211)]
        rows += [{"congress": "118", "chamber": "House", "rollnumber": "1", "icpsr": "5000", "cast_code": "1"}]
        result, count, missing = collector.summarize_votes(rows * 6, members, ideologies)
        house = next(r for r in result if r["congress"] == 118 and r["chamber"] == "House")
        self.assertEqual(house["rollCallsEligibleBothParties"], 1)
        self.assertEqual(house["opposed90PctPartyRollCalls"], 1)
        self.assertEqual(house["oppositePartyMajorityRollCalls"], 1)
        self.assertEqual(house["firstDimensionMeanPartyGap"], 0.7)
        self.assertEqual(missing, 6)

    def test_member_archive_decimal_party_codes_are_normalized_exactly(self):
        rows = [
            {"congress":"115","chamber":"House","icpsr":"50001","party_code":"100.0","nominate_dim1":"-0.5"},
            {"congress":"115","chamber":"House","icpsr":"50002","party_code":"200.0","nominate_dim1":"0.5"},
            {"congress":"115","chamber":"House","icpsr":"50003","party_code":"200.5","nominate_dim1":"0.6"},
        ]
        members, ideology = collector.parse_members(rows, min_rows=2)
        self.assertEqual(members[(115, "House", "50001")], "D")
        self.assertEqual(members[(115, "House", "50002")], "R")
        self.assertNotIn((115, "House", "50003"), members)
        self.assertEqual(ideology[(115, "House")]["D"], [-0.5])
        self.assertEqual(ideology[(115, "House")]["R"], [0.5])

    def test_decimal_icpsr_join_is_exact_and_not_name_based(self):
        self.assertEqual(collector.canonical_icpsr("10713.0"), "10713")
        self.assertEqual(collector.canonical_icpsr("10713"), "10713")
        self.assertEqual(collector.canonical_icpsr("00004.000"), "4")
        self.assertIsNone(collector.canonical_icpsr("10713.5"))
        self.assertIsNone(collector.canonical_icpsr("unknown"))
        records = [{"congress":"114","chamber":"House","rollnumber":"1",
                    "icpsr":f"{i}.0","cast_code":"1" if i <= 100 else "6"}
                   for i in range(1,201)]
        identities={(114,"House",str(i)):("D" if i<=100 else "R") for i in range(1,201)}
        ideology={(114,"House"):{"D":[-.4]*100,"R":[.5]*100}}
        rows,_,missed=collector.summarize_votes(records*6,identities,ideology)
        row=next(r for r in rows if r["congress"]==114 and r["chamber"]=="House")
        self.assertEqual(row["rollCallsEligibleBothParties"],1)
        self.assertEqual(row["opposed90PctPartyRollCalls"],1)
        self.assertEqual(missed,0)

    def test_whitelist_blocks_unapproved_hosts(self):
        with self.assertRaises(ValueError):
            next(collector.stream_csv("https://example.org/malicious.csv"))

if __name__ == "__main__":
    unittest.main()
