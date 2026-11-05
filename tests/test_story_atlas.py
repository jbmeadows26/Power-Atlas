"""Regression checks for the mobile-first research atlas and evidence boundaries."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "platform" / "unified" / "compare.html"
CATALOG = ROOT / "data" / "research" / "atlas-inventory-v1.json"

class StoryAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.items = cls.catalog["items"]

    def test_research_inventory_is_complete_and_unique(self):
        ids = [item["id"] for item in self.items]
        self.assertEqual(len(ids), 25)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(item["category"] for item in self.items),
                         {"Elections", "Money", "Institutions", "Solutions"})
        self.assertEqual(set(item["status"] for item in self.items),
                         {"partial", "curated", "needs_data"})
        self.assertEqual(sum(item["status"] == "needs_data" for item in self.items), 10)
        for item in self.items:
            for key in ("title", "question", "gap", "evidence"):
                self.assertTrue(item[key].strip(), f"{item['id']} missing {key}")

    def test_mobile_compact_topic_selection_and_accessibility(self):
        for marker in (
            'id="coverageBar"', 'id="coverageLegend"', 'id="inventory"',
            'id="topicDialog"', 'id="closeTopic"', 'id="dialogTitle"',
            'id="dialogGap"', 'id="dialogLinks"', 'id="topicSearch"',
            'class="topicTile"', 'grid-template-columns:repeat(2,minmax(0,1fr))',
        ):
            self.assertIn(marker, self.html)
        self.assertNotIn('<article class="researchCard">', self.html)
        self.assertNotIn('<div class="gap"><strong>Still needed:', self.html)
        self.assertIn('aria-labelledby="dialogTitle"', self.html)
        self.assertIn('type="button" class="topicTile"', self.html)

    def test_money_caveats_and_source_ids_remain(self):
        for id_ in ("filed", "leads", "ultimate", "moneyStatus"):
            self.assertEqual(len(re.findall('id="' + id_ + '"', self.html)), 1)
        self.assertIn('class="moneyJourney"', self.html)
        self.assertIn('not a nationwide census', self.html)
        self.assertIn("different units and denominators", self.html)
        self.assertIn("not that dark money does not exist", self.html)

    def test_evidence_methods_are_available_but_not_forced_open(self):
        self.assertIn('<details class="methodDisclosure">', self.html)
        self.assertIn('<details class="evidenceDetails">', self.html)
        self.assertIn('https://both-sides.the7eye.org.il/en/', self.html)
        self.assertIn("Missing records aren't zero activity", self.html)
        self.assertIn('No topics match.', self.html)
