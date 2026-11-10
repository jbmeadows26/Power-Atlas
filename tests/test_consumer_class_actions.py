"""Consumer class-action evidence and navigation safeguards (offline)."""
from pathlib import Path
import datetime
import json
import re
import shutil
import subprocess
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "consumer-class-actions" / "cases-v1.json"
UNIFIED = ROOT / "platform" / "unified"
SITE = ROOT / "site"


class ConsumerClassActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.cases = cls.data["cases"]
        cls.page = (UNIFIED / "class-actions.html").read_text(encoding="utf-8")

    def test_registry_schema_and_independent_cases(self):
        self.assertEqual(self.data["schema"], "power-atlas.consumer-class-actions.v1")
        self.assertGreaterEqual(len(self.cases), 3)
        self.assertEqual(len(self.cases), len({x["id"] for x in self.cases}))
        self.assertIn("not a comprehensive", self.data["scope"])
        self.assertIn("separate remedies", self.data["methodology"]["classification"].lower())

    def test_evidence_gates_prevent_false_legality_and_guarantees(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertIn(case["proceduralStatus"], {"settlement-proposed", "settlement-final"})
                self.assertIn(case["claimStatus"], {"open-as-of-review", "claims-closed"})
                self.assertIn("den", case["allegations"].lower())
                self.assertTrue(case["officialUrl"].startswith("https://"))
                self.assertNotIn("ftc.gov", case["officialUrl"])
                self.assertTrue(case["classSummary"] and case["action"])
                self.assertTrue(case["officialEvidence"])
                self.assertIn(case["confidence"], {"official-website-verified", "source-access-limited"})
                for name in ("deadline", "hearingDate", "optOutDeadline"):
                    self.assertRegex(case[name], r"^20\d{2}-\d{2}-\d{2}$")
                    datetime.date.fromisoformat(case[name])
                self.assertGreater(case["grossFundUSD"], 0)
                self.assertTrue((UNIFIED / case["crossLinks"][0]).is_file())
        self.assertGreaterEqual(len({x["industry"] for x in self.cases}), 5)
        self.assertTrue(any(x["claimStatus"] == "claims-closed" for x in self.cases))
        self.assertGreaterEqual(len(self.data["discoverySources"]), 8)
        self.assertTrue(all(x["kind"] == "secondary-discovery" for x in self.data["discoverySources"]))
        self.assertTrue(all(x["ingestion"] == "attributed-links-only; no scraping" for x in self.data["discoverySources"]))
        self.assertEqual({urlsplit(x["url"]).hostname for x in self.data["discoverySources"]}, {"www.classaction.org", "topclassactions.com", "www.consumer-action.org", "www.claimdepot.com"})
        promoted = [x for x in self.cases if x.get("discoverySource") == "ClassAction.org"]
        self.assertGreaterEqual(len(promoted), 2)
        self.assertTrue(all("classaction.org/news/" in x["secondaryUrl"] for x in promoted))
        self.assertTrue(all(x["officialUrl"].startswith("https://www.") for x in promoted))

    def test_frontend_filters_and_fail_closed(self):
        for id_ in ("q", "industry", "claim", "resultCount", "caseList", "countClaims"):
            self.assertIn('id="' + id_ + '"', self.page)
        self.assertIn("power-atlas.consumer-class-actions.v1", self.page)
        self.assertIn('src="bug-report.js"', self.page)
        self.assertIn('href="global-navigation.css"', self.page)
        self.assertIn("Evidence feed temporarily unavailable", self.page)
        self.assertIn('id="directoryLinks"', self.page)
        self.assertIn("ClassAction.org coverage", self.page)
        for source in ("ClassAction.org", "Top Class Actions", "Consumer Action", "ClaimDepot"):
            self.assertIn(source, self.page)
        self.assertIn("discovery leads, not independently verified findings", self.page.lower())
        self.assertIn("proposed settlement, not final approval", self.page)
        self.assertNotIn("localStorage", self.page)
        self.assertNotIn("sendBeacon", self.page)

    def test_category_is_linked_from_two_surfaces_and_daily_life(self):
        for path in ("index.html", "consumer-practices.html", "my-life.html"):
            self.assertIn('href="class-actions.html"', (UNIFIED / path).read_text(encoding="utf-8"), path)
        for path in ("index.html", "consumer-practices.html"):
            self.assertIn("power-atlas-unified.vercel.app/class-actions.html",
                          (SITE / path).read_text(encoding="utf-8"), path)

    def test_inline_javascript_parses(self):
        if not shutil.which("node"):
            self.skipTest("Node unavailable")
        scripts = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", self.page)
        self.assertTrue(scripts)
        for script in scripts:
            if script.strip():
                result = subprocess.run(["node", "--check", "-"], input=script, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
