"""Verify election-money source integrations, provenance, and honest coverage flags."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MONEY = ROOT / "data" / "money-influence"


def read(filename):
    return json.loads((MONEY / filename).read_text(encoding="utf-8"))


class MoneySourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read("source-registry-v1.json")
        cls.bridge = read("verified-record-previews-v1.json")

    def test_registry_has_distinct_verified_links(self):
        rows = self.registry["sources"]
        self.assertEqual(len(rows), 17)
        self.assertEqual(len({s["id"] for s in rows}), len(rows))
        self.assertTrue(all(s["url"].startswith("https://") for s in rows))
        self.assertTrue(all(s["name"] and s["coverage"] and s["caution"] for s in rows))
        self.assertEqual({s["status"] for s in rows}, {
            "indexed_partial", "curated_excerpt", "link_only",
            "research_only", "archive_only"
        })

    def test_partial_ingestion_is_not_claimed_complete(self):
        m = {s["id"]: s for s in self.registry["sources"]}
        self.assertEqual(m["fec"]["status"], "indexed_partial")
        self.assertEqual(m["lda"]["status"], "indexed_partial")
        self.assertEqual(m["propublica"]["status"], "link_only")
        self.assertEqual(m["irs527"]["status"], "link_only")
        self.assertEqual(m["dime"]["status"], "research_only")
        self.assertEqual(m["sunlight"]["status"], "archive_only")
        self.assertTrue(all(not s["dataProducts"] for s in m.values() if s["status"] in {"link_only", "archive_only", "research_only"}))

    def test_bounded_existing_evidence(self):
        pac = self.bridge["pacCommittees"]
        lda = self.bridge["lobbyingFilings"]
        self.assertEqual(len(pac), 135)
        self.assertEqual(len(lda), 56)
        self.assertEqual(sum(x["cycle"] == 2024 for x in pac), 69)
        self.assertEqual(sum(x["cycle"] == 2026 for x in pac), 66)
        self.assertEqual({x["cycle"] for x in pac}, {2024, 2026})
        self.assertTrue(all(x["committeeId"].startswith("C") and x["receiptsUSD"] >= 0 for x in pac))
        self.assertTrue(all(x["source"].startswith("https://www.fec.gov/") for x in pac))
        self.assertTrue(all(x["filingDetail"].startswith("https://lda.gov/") for x in lda))

    def test_privacy_and_noncausal_labels(self):
        self.assertIn("donor-to-PAC-to-candidate", " ".join(self.bridge["limitations"]))
        self.assertTrue(all("address" not in k.lower() and "email" not in k.lower()
                            for x in self.bridge["lobbyingFilings"] for k in x))

    def test_visual_story_and_mobile_navigation(self):
        page = (ROOT / "platform" / "unified" / "money-sources.html").read_text(encoding="utf-8")
        for fragment in ('id="overview"', 'id="committees"', 'id="lobbying"', 'id="sources"',
                         'class="sectionNav"', 'id="committeeDetail"', 'id="lobbyDetail"',
                         'id="sourceLegend"', 'id="statusFilters"', 'id="sourceMore"',
                         'id="recordRows"', 'elem(\'div\',undefined,\'stack\')', 'renderPACDetails',
                         'renderLobby', 'renderSources', '@media(max-width:650px)'):
            self.assertIn(fragment, page)
        self.assertIn('No verified donor', page)
        self.assertIn('reported categories', page)

    def test_pac_category_breakdowns_reconcile_to_fec_totals(self):
        for row in self.bridge["pacCommittees"]:
            incoming = (
                row["individualContributionsUSD"] +
                row["otherCommitteeContributionsUSD"] +
                row["transfersFromAffiliatesUSD"]
            )
            outgoing = (
                row["contributionsToOtherCommitteesUSD"] +
                row["transfersToAffiliatesUSD"] +
                row["independentExpendituresUSD"] +
                row["partyCoordinatedExpendituresUSD"]
            )
            self.assertLessEqual(incoming, row["receiptsUSD"] + 1.0)
            self.assertLessEqual(outgoing, row["disbursementsUSD"] + 1.0)
            self.assertTrue(row["coverageEnd"])

    def test_source_hub_linked_from_federal_money_dashboard(self):
        source_page = (ROOT / "platform" / "unified" / "money-sources.html").read_text(encoding="utf-8")
        funding_page = (ROOT / "platform" / "unified" / "election-money.html").read_text(encoding="utf-8")
        home = (ROOT / "platform" / "unified" / "index.html").read_text(encoding="utf-8")
        self.assertIn("source-registry-v1.json", source_page)
        self.assertIn("verified-record-previews-v1.json", source_page)
        self.assertIn("money-sources.html", funding_page)
        self.assertIn("money-sources.html", home)


if __name__ == "__main__":
    unittest.main()
