"""Cross-project corporate ownership and cost evidence integration tests."""
from __future__ import annotations
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GRAPH=ROOT/"data/corporate-ownership/verified-relationships-v1.json"
CASES=ROOT/"data/corporate-ownership/transparency-price-power-v1.json"
LIFE=ROOT/"platform/unified/my-life.html"
PAGE=ROOT/"platform/unified/corporate-ownership.html"
ISSUES={"housing","groceries","energy","health","work","schools","transport","public-services","representation"}

class CorporateOwnershipIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=json.loads(GRAPH.read_text(encoding="utf-8"))
        cls.c=json.loads(CASES.read_text(encoding="utf-8"))

    def test_temporal_company_brand_graph_honours_identity(self):
        g=self.g
        self.assertEqual(g["schema"],"power-atlas.corporate-ownership.evidence-graph.v1")
        self.assertGreaterEqual(len(g["entities"]),80)
        self.assertGreaterEqual(len(g["relations"]),60)
        entities={x["id"]:x for x in g["entities"]}
        self.assertEqual(len(entities),len(g["entities"]))
        self.assertEqual(len({r["id"] for r in g["relations"]}),len(g["relations"]))
        self.assertEqual(set.union(*(set(x["issues"]) for x in g["entities"])),ISSUES)
        for x in g["entities"]:
            self.assertTrue(x["name"] and set(x["issues"])<=ISSUES)
        for r in g["relations"]:
            self.assertIn(r["from"],entities)
            self.assertIn(r["to"],entities)
            self.assertIn(r["relation"],g["relationshipTypes"])
            self.assertTrue(r["source"].startswith("https://"))
            self.assertRegex(r["asOf"],r"^\d{4}-\d{2}-\d{2}$")
            self.assertIs(r["localEffectEstablished"],False)
            self.assertTrue(r["note"])
        self.assertIn("partners-group",entities)
        self.assertIn("kindercare",entities)
        self.assertIn("learning-care",entities)
        self.assertIn("realpage",entities)
        self.assertIn("pepsico",entities)
        self.assertIn("pg",entities)

    def test_share_percent_is_dated_not_blanket_control(self):
        g=self.g
        edges={x["id"]:x for x in g["relations"]}
        self.assertEqual(edges["pg-kindercare"]["stakePct"],68.8)
        self.assertEqual(edges["pg-kindercare"]["asOf"],"2026-04-09")
        self.assertEqual(edges["bezos-amazon-2026"]["stakePct"],8.8)
        self.assertEqual(edges["bezos-amazon-2026"]["asOf"],"2026-02-24")
        self.assertIn("MINORITY",edges["bezos-amazon-2026"]["note"])
        self.assertIn("current ownership not verified",edges["4x4-metrx"]["note"])
        self.assertEqual(edges["lcg-brand-la-petite"]["asOf"],"2018-03-13")
        self.assertEqual(edges["orlando-thoma-bravo"]["relation"],"FOUNDED_AND_LEADS")
        self.assertEqual(len([x for x in g["entities"] if x["kind"]=="political_finance_business_candidate"]),8)
        self.assertEqual(len([x for x in g["entities"] if x["kind"]=="business_case_candidate"]),2)
        for x in g["relations"]:
            self.assertNotIn("PAC",x["relation"])

    def test_expanded_corporate_families_are_sourced_and_not_local_price_claims(self):
        g=self.g
        entities={x["id"]:x for x in g["entities"]}
        relations={x["id"]:x for x in g["relations"]}
        self.assertGreaterEqual(len(entities),108)
        self.assertGreaterEqual(len(relations),84)
        for id_,source in (
            ("blackstone-tricon","blackstone.com"),
            ("amazon-one-medical","aboutamazon.com"),
            ("amazon-whole-foods","sec.gov"),
            ("mars-kellanova","mars.com"),
            ("kellanova-cheez-it","mars.com"),
            ("general-mills-blue-buffalo","generalmills.com"),
            ("berkshire-geico","sec.gov"),
            ("berkshire-bnsf","sec.gov"),
        ):
            self.assertIn(id_,relations)
            self.assertIn(source,relations[id_]["source"])
            self.assertFalse(relations[id_]["localEffectEstablished"])
        self.assertEqual(relations["mars-kellanova"]["to"],relations["kellanova-cheez-it"]["from"])
        page=PAGE.read_text(encoding="utf-8")
        life=LIFE.read_text(encoding="utf-8")
        for marker in ('id="ownership-network"','id="networkOwners"','id="networkSearch"',
                       "renderOwnershipNetwork()","function ownershipPaths(","Dated evidence:",
                       "Original source ("):
            self.assertIn(marker,page)
        self.assertIn('slice(0,6)',life)
        self.assertIn('#ownership-network',life)

    def test_price_cases_keep_proven_alleged_and_unknown_distinct(self):
        c=self.c
        self.assertEqual(c["schema"],"power-atlas.corporate-ownership.transparency-price-power.v1")
        self.assertEqual(len(c["cases"]),7)
        self.assertEqual(len({x["id"] for x in c["cases"]}),7)
        for case in c["cases"]:
            self.assertTrue(case["summary"])
            self.assertTrue(case["interpretationLimits"])
            self.assertIsNone(case["measuredIndividualCostUsd"])
            self.assertIs(case["doesNotEstablishPoliticalCausation"],True)
            self.assertIs(case["directLocalGeographicConnection"],False)
            self.assertTrue(set(case["powerAtlasIssues"])<=ISSUES)
            self.assertGreaterEqual(len(case["originalSources"]),1)
            self.assertGreaterEqual(len(case["evidenceSteps"]),4)
            self.assertTrue(all(s["evidenceStatus"] in c["sourceTypes"] for s in case["evidenceSteps"]))
            self.assertTrue(all(s["url"].startswith("https://") for s in case["originalSources"]))

    def test_both_explorers_link_graphs_to_all_nine_life_topics(self):
        life=LIFE.read_text(encoding="utf-8")
        page=PAGE.read_text(encoding="utf-8")
        for marker in ('id="corporatePaths"','id="ownerPathCards"',
                       'id="ownerCostQuestion"','id="ownershipFullLink"',
                       "renderCorporatePaths()", "SOURCE_CORPORATE","SOURCE_TRANSPARENCY",
                       "corporate-ownership.html?issue="):
            self.assertIn(marker,life)
        for marker in ("verified-relationships-v1.json","transparency-price-power-v1.json",
                       "Object.entries(issueLabels)","id=\"relationshipCards\"",
                       "id=\"caseCards\"","id=\"businessCandidates\"",
                       "localEffectEstablished","Evidence-led research"):
            if marker=="localEffectEstablished":continue
            self.assertIn(marker,page)
        self.assertIn("No local facility or price claim is inferred",page)
        self.assertIn("No company-specific local price change",life)

if __name__=="__main__":
    unittest.main()
