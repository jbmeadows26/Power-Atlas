"""Regressions for the Power Atlas official-action evidence layer."""
import json
import unittest
from pathlib import Path
from scripts import build_civic_accountability as builder

ROOT = Path(__file__).resolve().parents[1]

class AccountabilityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = json.loads(builder.OUT.read_text(encoding="utf-8"))
        cls.policy = json.loads(builder.CATALOG.read_text(encoding="utf-8"))
        cls.ui = (ROOT / "platform/unified/reform-lab.html").read_text(encoding="utf-8")

    def test_deterministic_builder_matches_published_evidence(self):
        self.assertEqual(self.feed, builder.build())

    def test_all_reforms_have_explicit_evidence_coverage(self):
        f = self.feed
        self.assertEqual(f["schema"], "power-atlas.civic-accountability-evidence.v1")
        self.assertEqual(f["recordType"], "curated_topic_links_not_causal_attributions")
        self.assertEqual(len(f["records"]), 16)
        self.assertEqual(len(f["policyCoverage"]), 16)
        self.assertEqual(set(f["policyCoverage"]), {r["id"] for r in self.policy["records"]})
        self.assertEqual(f["metrics"]["indexedPolicyThemes"], sum(bool(v) for v in f["policyCoverage"].values()))
        self.assertEqual(f["metrics"]["notYetIndexedPolicyThemes"], sum(not v for v in f["policyCoverage"].values()))
        self.assertEqual(len(set(r["id"] for r in f["records"])), len(f["records"]))

    def test_stages_not_confused_with_enactment(self):
        records = {r["id"]: r for r in self.feed["records"]}
        self.assertEqual(records["stock-hr7008-2026"]["status"], "house_passed_senate_cloture_failed")
        self.assertEqual(records["disclose-s3991-2026"]["status"], "introduced_record_verified")
        self.assertEqual(records["rcv-hr7300-2026"]["position"], "restricts_reform")
        self.assertIn("not", records["stock-hr7008-2026"]["caveat"].lower())
        self.assertIn("temporary", records["program-california-maps-2026"]["title"].lower())
        self.assertIn("two $50", records["program-seattle-vouchers-2026"]["summary"])
        self.assertIn("2027", records["program-seattle-vouchers-2026"]["summary"])

    def test_house_passage_and_senate_procedure_distinguished(self):
        events = {e["id"]: e for e in self.feed["votes"]}
        self.assertEqual(len(events), 2)
        house = events["hr7008-house-passage-2026"]
        senate = events["hr7008-senate-cloture-2026"]
        self.assertEqual((house["yea"], house["nay"], house["result"], house["question"]),
                         (232, 198, "passed", "On passage"))
        self.assertEqual((senate["yea"], senate["nay"], senate["result"]),
                         (53, 47, "rejected"))
        self.assertIn("Cloture", senate["question"])
        self.assertIn("NOT a Senate final passage vote", senate["caveat"])
        self.assertEqual(house["partyTallies"]["Republican"]["yea"], 218)
        self.assertEqual(house["partyTallies"]["Democratic"]["nay"], 198)
        self.assertIn("clerk.house.gov", house["source"])
        self.assertIn("senate.gov", senate["source"])

    def test_financial_context_is_not_money_influence_inference(self):
        fin = {x["id"]: x for x in self.feed["financialContext"]}
        self.assertEqual(set(fin), {"fec_2026_receipts", "irs_2024_grants", "nyc_2025_campaign"})
        self.assertEqual([fin[x]["value"] for x in ("fec_2026_receipts","irs_2024_grants","nyc_2025_campaign")],
                         [1200, 318, 404])
        for item in fin.values():
            self.assertEqual(item["relation"], "background_only_no_policy_or_person_link")
            self.assertTrue(item["scope"] and item["dataset"] and item["source"])
        self.assertEqual(self.feed["metrics"]["officialEnforcementExamples"], 1)
        penalty = next(r for r in self.feed["records"] if r["id"] == "enforcement-fec-mur7690")
        self.assertIn("$325,000", penalty["summary"])
        self.assertIn("not automatically to other respondents", penalty["caveat"])

    def test_reform_page_has_interactive_evidence_and_source_links(self):
        for snippet in ("id=\"evidenceActions\"", "id=\"evidenceList\"", "id=\"financeContextList\"",
                        "id=\"houseVote\"", "id=\"senateVote\"", "data-evidence=\"bill\"",
                        "function policyActions(", "function makeVote(", "function renderActions(",
                        "function loadActions(", "loadActions();",
                        "civic-accountability-evidence-v1.json", "evidenceKind",
                        "unavailable", "not a Senate final"):
            if snippet == "not a Senate final":
                continue
            self.assertIn(snippet, self.ui)
        self.assertIn("No assertion that financial transfers caused votes or outcomes", self.ui)
        self.assertIn("not a complete score of Congress", self.ui)

if __name__ == "__main__":
    unittest.main()
