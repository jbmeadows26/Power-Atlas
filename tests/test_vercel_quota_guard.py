"""Guard the zero-cost production release gate against accidental Git deploy churn."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VercelQuotaGuardTests(unittest.TestCase):
    def test_automatic_git_deployments_are_disabled(self):
        config = json.loads((ROOT / "site/vercel.json").read_text(encoding="utf-8"))
        self.assertIs(config["git"]["deploymentEnabled"], False)
        self.assertTrue((ROOT / "site/index.html").exists())


if __name__ == "__main__":
    unittest.main()
