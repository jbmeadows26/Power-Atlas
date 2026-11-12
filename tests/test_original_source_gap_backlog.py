"""Keep the original-source execution backlog synchronized with verified evidence gates."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "research/assessments/ORIGINAL_SOURCE_GAP_EXECUTION_2026-11-12.json"
LOCAL = ROOT / "data/health/sitewide-missing-sources-v1.json"
NATIONAL = ROOT / "data/health/completion-gates.json"


class OriginalSourceGapBacklogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(BACKLOG.read_text(encoding="utf-8"))
        cls.local = json.loads(LOCAL.read_text(encoding="utf-8"))
        cls.national = json.loads(NATIONAL.read_text(encoding="utf-8"))

    def test_all_original_gaps_and_gates_have_unique_entries(self):
        local_ids = {x["id"] for x in self.local["gaps"]}
        gate_ids = set(self.national["blockingGates"])
        self.assertEqual(len(local_ids), len(self.local["gaps"]))
        self.assertEqual(set(x["id"] for x in self.plan["localGaps"]), local_ids)
        self.assertEqual(set(x["id"] for x in self.plan["nationalGates"]), gate_ids)
        self.assertEqual(self.plan["corpusSnapshot"]["localGapCount"], len(local_ids))
        self.assertEqual(self.plan["corpusSnapshot"]["nationalBlockingGateCount"], len(gate_ids))

    def test_candidate_discovery_is_never_described_as_completion(self):
        for item in self.plan["localGaps"] + self.plan["nationalGates"]:
            self.assertEqual(item["executionState"], "not_closed", item["id"])
            self.assertIsNone(item["closedOn"], item["id"])
        self.assertIn("NOT ORIGINAL_RECORD_INGESTED", self.plan["policy"]["statusRule"])
        self.assertIn("Paid", self.plan["policy"]["costRule"])

    def test_all_local_source_refs_exist_in_original_catalog(self):
        source_ids = {x["id"] for x in self.local["sources"]}
        self.assertGreaterEqual(len(source_ids), 50)
        for item in self.plan["localGaps"]:
            self.assertTrue(set(item["sourceIds"]).issubset(source_ids), item["id"])
            self.assertTrue(item["proposedWorkflow"], item["id"])
            self.assertEqual(
                item["originalStatus"],
                next(x["status"] for x in self.local["gaps"] if x["id"] == item["id"]),
                item["id"]
            )

    def test_original_portal_receipts_have_source_and_explicit_limitations(self):
        candidates = self.plan["verifiedEntryPoints"]
        self.assertGreaterEqual(len(candidates), 8)
        self.assertEqual(len({x["id"] for x in candidates}), len(candidates))
        for item in candidates:
            self.assertTrue(item["url"].startswith("https://"), item["id"])
            self.assertTrue(item["stage"], item["id"])
            self.assertTrue(item["coverage"], item["id"])
            self.assertTrue(item["next"], item["id"])
            self.assertTrue(set(item["relevantGates"]).issubset(
                set(self.national["blockingGates"])
            ), item["id"])


if __name__ == "__main__":
    unittest.main()
