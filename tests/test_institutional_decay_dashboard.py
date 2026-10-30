"""Static public trust dashboard and synthetic-only GMM integrity checks."""
import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/institutional-decay/trust-country-waves-2023-2025.json"
API = ROOT / "site/api/trust-metrics.json"
HTML = ROOT / "site/index.html"
JS = ROOT / "site/institutional-decay.js"
GMM = ROOT / "scripts/institutional_decay_gmm_demo.py"


def load_gmm():
    spec = importlib.util.spec_from_file_location("id_gmm", GMM)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def correlation(pairs):
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    a = sum(xs) / len(xs)
    b = sum(ys) / len(ys)
    numerator = sum((x-a)*(y-b) for x, y in pairs)
    dx = sum((x-a)**2 for x in xs)
    dy = sum((y-b)**2 for y in ys)
    return numerator / (dx*dy)**0.5


class InstitutionalDecayDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = json.loads(API.read_text(encoding="utf-8"))
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_api_preserves_source_values_and_missingness(self):
        d = self.api
        self.assertEqual(d["schema"], "power-atlas.institutional-decay.trust-metrics.v1")
        self.assertEqual(d["observedTrustCells"], 407)
        self.assertEqual(d["countryCount"], 39)
        self.assertEqual(len(d["rows"]), 39)
        self.assertEqual(len({r["id"] for r in d["rows"]}), 39)
        source = {r["countryCode"]:r for r in self.source["rows"]}
        keys = {"g23":"nationalGovernment2023", "g25":"nationalGovernment2025",
                "c23":"nationalCivilService2023", "c25":"nationalCivilService2025",
                "l23":"localGovernment2023", "l25":"localGovernment2025",
                "p23":"nationalParliament2023", "p25":"nationalParliament2025",
                "j23":"courts2023", "j25":"courts2025",
                "t23":"politicalParties2023", "t25":"politicalParties2025"}
        total = 0
        for row in d["rows"]:
            self.assertIn(row["id"],source)
            self.assertEqual(row["name"],source[row["id"]]["country"])
            self.assertEqual(row["group"],source[row["id"]]["group"])
            for short,long in keys.items():
                self.assertEqual(row[short], source[row["id"]][long])
                total += row[short] is not None
        self.assertEqual(total,407)

    def test_reference_correlation_is_recomputable(self):
        rows = [r for r in self.api["rows"] if r["group"]=="oecd_member" and r["g25"] is not None]
        self.assertEqual(len(rows),33)
        self.assertAlmostEqual(correlation([(r["c25"],r["g25"]) for r in rows]),
                               self.api["referenceCorrelationGovVsCivil2025"], places=4)
        changes = [r for r in rows if r["g23"] is not None and r["c23"] is not None]
        self.assertEqual(len(changes),28)
        self.assertAlmostEqual(correlation([(r["c25"]-r["c23"],r["g25"]-r["g23"]) for r in changes]),
                               0.4901,places=4)

    def test_frontend_has_valid_single_inline_script_and_research_tab(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('data-tab="institutional-decay"',html)
        self.assertIn('data-panel="institutional-decay"',html)
        self.assertIn("decayScript.src='institutional-decay.js'",html)
        self.assertIn('id="idScatter"',html)
        self.assertEqual(len(re.findall(r"<script\\s*>(.*?)</script>",html,re.S)),1)
        self.assertTrue(JS.is_file())
        self.assertIn("correlation reference check failed".lower(),
                      JS.read_text(encoding="utf-8").lower())
        if shutil.which("node"):
            subprocess.run(["node","--check",str(JS)],check=True,timeout=15)

    def test_real_data_cannot_support_dynamic_gmm(self):
        status=load_gmm().check_real()
        self.assertEqual(status["status"],"not_estimable")
        self.assertEqual(status["paired_countries"],28)
        self.assertFalse(status["arellano_bond_identified"])

    def test_synthetic_estimator_recovers_known_parameters(self):
        result=load_gmm().simulate(n=900,tmax=9)
        self.assertEqual(result["status"],"synthetic_math_demo_not_empirical_result")
        self.assertAlmostEqual(result["estimated_rho"],result["true_rho"],delta=0.15)
        self.assertAlmostEqual(result["estimated_beta"],result["true_beta"],delta=0.13)


if __name__=="__main__":
    unittest.main()
