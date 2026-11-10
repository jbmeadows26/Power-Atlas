"""Evidence, comparability and live-navigation safeguards for financial scale and market power."""
import json, re, shutil, subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"site"
U=ROOT/"platform/unified"
def load(path): return json.loads(path.read_text(encoding="utf-8"))
class MoneyMarketReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.money=load(U/"money-scale.json")
        cls.bridge=load(U/"household-market-bridge.json")
        cls.market=load(U/"market-power.json")
        cls.bench=load(ROOT/"data/place-impact/cost-benchmark-drivers-v1.json")
    def test_release_status_and_mirrors(self):
        self.assertEqual(self.money["status"],"published")
        self.assertEqual(self.bridge["publicationStatus"],"published")
        self.assertEqual(self.market["publication"],"published")
        self.assertEqual(self.money,load(S/"money-scale.json"))
        self.assertEqual(self.money,load(S/"data/money-scale-v1.json"))
        self.assertEqual(self.bridge,load(S/"household-market-bridge.json"))
        self.assertEqual(self.market,load(S/"market-power.json"))
    def test_source_quality_and_measures_are_not_conflated(self):
        metrics=self.money["metrics"];self.assertGreaterEqual(len(metrics),15)
        self.assertEqual(len(metrics),len({x["id"] for x in metrics}))
        for x in metrics:
            self.assertTrue(x["sourceUrl"].startswith("https://"),x["id"])
            self.assertTrue(x["year"] and x["scope"] and x["definition"] and x["interpretation"],x["id"])
            self.assertGreater(x["valueTrillionsUsd"],0)
        m={x["id"]:x for x in metrics}
        self.assertAlmostEqual(m["world-gdp-2025"]["valueTrillionsUsd"],118.350166)
        self.assertEqual(m["world-gdp-2025"]["measurement"],"annual-output")
        self.assertAlmostEqual(m["billionaires-world-2026"]["valueTrillionsUsd"],20.1)
        self.assertEqual(m["billionaires-world-2026"]["measurement"],"asset-stock")
        self.assertEqual(m["us-healthcare-spending-2025"]["measurement"],"annual-flow-estimate")
        self.assertEqual(m["global-military-sipri-2025"]["measurement"],"annual-flow-alternative")
        self.assertGreaterEqual(len(self.money["sourceCorrections"]),13)
        billions=[x for x in metrics if x["measurement"]=="billion-scale"]
        self.assertEqual(len(billions),3)
        self.assertAlmostEqual(m["amazon-net-sales-2025"]["valueBillionsUsd"],716.924)
        self.assertAlmostEqual(m["amazon-net-income-2025"]["valueBillionsUsd"],77.670)
        self.assertIn("planned",m["stargate-announced-plan-2025"]["interpretation"].lower()) if "planned" in m["stargate-announced-plan-2025"]["interpretation"].lower() else self.assertIn("neither",m["stargate-announced-plan-2025"]["interpretation"].lower())
    def test_bls_household_cost_baseline_exact(self):
        rows={x["id"]:x for x in self.bridge["categories"]}
        for key in ("housing","transport","groceries","health"):
            self.assertEqual(rows[key]["annualUsd"],self.bench["topics"][key]["headline"]["annual"])
            self.assertTrue(rows[key]["unresolved"])
        self.assertEqual(self.bridge["baseline"]["totalExpenditureUsd"],81905)
        self.assertEqual(self.bridge["incomeExample"]["annualUsd"],self.bench["topics"]["work"]["headline"]["annual"])
        self.assertIn("bls.gov",self.bridge["baseline"]["sourceUrl"])
        self.assertIn("no nationwide, zip-level or individual-household causal estimate"," ".join(self.bridge["interpretationRules"]).lower())
    def test_case_references_preserve_legal_status(self):
        cases={x["id"]:x for x in self.market["cases"]}
        self.assertGreaterEqual(len(cases),12)
        for x in self.bridge["categories"]:
            for id in x["caseIds"]:
                self.assertIn(id,cases)
                self.assertIn(cases[id]["kind"],("measured","finding","allegation","context"))
                self.assertTrue(cases[id]["source"].startswith("https://"))
    def test_original_visual_system_and_routes(self):
        for folder in (S,U):
            js=(folder/"atlas-visual-system.js").read_text()
            css=(folder/"atlas-visual-system.css").read_text()
            self.assertIn("Ten paths into the evidence",js)
            self.assertIn("09 · Financial scale",js)
            self.assertIn("08 · Market power",js)
            self.assertIn('"market-power.html"',js)
            self.assertIn('"money-scale.html"',js)
            self.assertIn(".pa4-tile:nth-child(9)",css)
            h=(folder/"market-power.html").read_text()
            ms=(folder/"money-scale.html").read_text()
            self.assertIn('id="household-bridge"',h)
            self.assertIn('id="hbBars"',h)
            self.assertIn('src="market-power-household.js"',h)
            self.assertIn('href="money-scale.html"',h)
            self.assertIn('data-group="annual-output"',ms)
            self.assertIn('data-group="billion-scale"',ms)
            self.assertIn('href="atlas-visual-system.css"',ms)
            self.assertIn('src="atlas-visual-system.js"',ms)
            self.assertNotIn("noindex,nofollow",h+ms)
            self.assertNotIn("REVIEW ONLY",h+ms)
            self.assertNotIn("NOT PUBLISHED",h+ms)
            self.assertIn("money-scale.json",ms)
            self.assertIn("household-market-bridge.json",(folder/"market-power-household.js").read_text())
    @unittest.skipUnless(shutil.which("node"),"node unavailable")
    def test_browser_javascript_syntax(self):
        for folder in (S,U):
            for filename in ("atlas-visual-system.js","market-power-household.js"):
                p=subprocess.run(["node","--check",str(folder/filename)],capture_output=True,text=True,timeout=25)
                self.assertEqual(p.returncode,0,p.stderr)
            for filename in ("market-power.html","money-scale.html"):
                html=(folder/filename).read_text()
                blocks=re.findall(r"<script\s*>([\s\S]*?)</script>",html)
                self.assertGreaterEqual(len(blocks),1,filename)
                for block in blocks:
                    p=subprocess.run(["node","--check","-"],input=block,capture_output=True,text=True,timeout=25)
                    self.assertEqual(p.returncode,0,p.stderr)
if __name__=="__main__": unittest.main()
