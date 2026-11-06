"""Location-first story integrity and full deep-research coverage for Power Atlas."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORIES = ROOT / "data/place-impact/life-issues-v1.json"
MAP = ROOT / "data/place-impact/deep-resource-map-v1.json"
INDEX = ROOT / "data/research/atlas-inventory-v1.json"
PAGE = ROOT / "platform/unified/my-life.html"
HOME = ROOT / "platform/unified/index.html"


class PlaceImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stories = json.loads(STORIES.read_text(encoding="utf-8"))
        cls.resources = json.loads(MAP.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))

    def test_all_25_research_tracks_and_new_deep_datasets_mapped(self):
        self.assertEqual(self.resources["schema"], "power-atlas.place-impact-deep-evidence.v1")
        self.assertEqual(self.index["schema"], "power-atlas.story-inventory.v1")
        idset = {x["id"] for x in self.index["items"]}
        mapping = self.resources["inventory"]
        self.assertEqual(len(idset), 25)
        self.assertEqual(set(mapping["expectedIds"]), idset)
        self.assertEqual(set(mapping["topicTags"]), idset)
        self.assertEqual(len(self.resources["additional"]), 9)
        self.assertEqual(len({x["id"] for x in self.resources["additional"]}), 9)
        self.assertFalse(idset.intersection(x["id"] for x in self.resources["additional"]))
        self.assertTrue(any(x["id"] == "contract-benefits" for x in self.resources["additional"]))
        self.assertTrue(any(x["id"] == "oversight-records" for x in self.resources["additional"]))
        self.assertTrue(any(x["id"] == "cross-domain-research" for x in self.resources["additional"]))
        for track in self.index["items"]:
            self.assertIn(track["status"], self.resources["evidenceLevels"])
            self.assertTrue(track["evidence"])
        for x in self.resources["additional"]:
            self.assertIn(x["status"], self.resources["evidenceLevels"])
            self.assertIn(x["path"], [str(p.relative_to(ROOT)) for p in (ROOT / "data").rglob("*.json")],
                          "Recent source registry references an unavailable JSON: " + x["path"])
            self.assertTrue(x["summary"] and x["missing"])
            self.assertTrue(x["issues"])

    def test_original_source_directory_is_link_only_and_issue_scoped(self):
        directory = self.resources["sourceDirectories"]
        self.assertGreaterEqual(len(directory), 30)
        self.assertEqual(len({x["id"] for x in directory}), len(directory))
        known = set(self.resources["issueIds"])
        for source in directory:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertEqual(source["coverage"], "source_directory_only_no_assumption_of_automated_ingestion")
            self.assertTrue(source["name"] and source["limitation"])
            self.assertTrue(set(source["issues"]) <= known)
        ids={x["id"] for x in directory}
        for required in ("fec","usaspending","sec","doj","congress","courtlistener",
                         "opensecrets","followmoney","anes","ces","voteview",
                         "cook","census","bls","eia","cms","ofac","opencorporates"):
            self.assertIn(required, ids)
        self.assertIn("NOT", self.resources["sourceDirectoryNotes"])

    def test_nine_life_issues_have_nonpartisan_research_and_actions(self):
        d = self.stories
        self.assertEqual(d["schema"], "power-atlas.place-impact-stories.v1")
        keys = {x["id"] for x in d["issues"]}
        self.assertEqual(len(keys), 9)
        self.assertEqual(set(self.resources["issueIds"]), keys)
        self.assertIn(d["defaultIssue"], keys)
        for x in d["issues"]:
            self.assertEqual(len(x["levers"]), 3)
            self.assertGreaterEqual(len(x["resources"]), 2)
            self.assertEqual(len(x["policies"]), 2)
            self.assertGreater(len(x["question"]), 25)
            for factor in x["levers"]:
                self.assertTrue(factor["actor"] and factor["why"] and factor["evidence"])
            for action in x["resources"]:
                self.assertTrue(
                    action["url"].startswith("https://") or
                    re.fullmatch(r"[a-z0-9-]+\.html", action["url"])
                )
        for tags in self.resources["inventory"]["topicTags"].values():
            self.assertTrue(set(tags) <= keys)
        for track in self.resources["additional"]:
            self.assertTrue(set(track["issues"]) <= keys)

    def test_zip_is_opt_in_not_assumed_political_geography(self):
        txt = PAGE.read_text(encoding="utf-8")
        self.assertIn('id="zipForm"', txt)
        self.assertIn('id="localMetrics"', txt)
        self.assertIn("local-measures-v1.json", txt)
        self.assertIn('name="zip"', txt)
        self.assertIn("api.zippopotam.us/us/", STORIES.read_text(encoding="utf-8"))
        self.assertIn('Only on user submission', STORIES.read_text(encoding="utf-8"))
        self.assertIn('No ZIP selected', txt)
        self.assertIn('ZIP can cross municipalities', STORIES.read_text(encoding="utf-8"))
        self.assertIn("No city, district or local effect has been guessed", txt)
        self.assertIn("ZIP code", txt)
        self.assertNotIn("navigator.geolocation", txt)
        self.assertNotIn("localStorage", txt)
        self.assertNotIn("sessionStorage", txt)
        self.assertNotIn("political ideology", txt)

    def test_research_index_is_loaded_directly_and_step3_never_disappears(self):
        txt = PAGE.read_text(encoding="utf-8")
        home = HOME.read_text(encoding="utf-8")
        for marker in ("SOURCE_MAP", "SOURCE_ATLAS", "SOURCE_STORIES",
                       "renderResearch()", "renderChain()", "researchRecords()",
                       'id="researchItems"', 'id="scopeButton"',
                       'id="allButton"', 'id="loadMore"', 'id="decisionChain"',
                       'id="actionGrid"', 'id="researchStatus"',
                       'id="originalSources"', 'id="originAll"',
                       "renderSources()", "sourceDirectories"):
            self.assertIn(marker, txt)
        self.assertIn("data/research/atlas-inventory-v1.json", txt)
        self.assertIn("data/place-impact/deep-resource-map-v1.json", txt)
        self.assertIn("25 research tracks + 9 newer source collections", txt)
        self.assertIn("What has not been established?", txt)
        self.assertIn("A tag indicates research relevance, not a proven local effect.", txt)
        self.assertIn("my-life.html", home)
        self.assertIn("What shapes <em>your everyday life?</em>", home)
        self.assertEqual(len(re.findall(r"<script\s*>", txt)), 1)


if __name__ == "__main__":
    unittest.main()
