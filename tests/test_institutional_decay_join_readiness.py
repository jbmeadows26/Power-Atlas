"""Quality gates for country/year OECD integrity-trust join readiness."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"scripts/audit_institutional_decay_join.py"
OUT=ROOT/"data/institutional-decay/indicator-join-readiness-2026-10-30.json"


def compute():
    spec=importlib.util.spec_from_file_location("id_join_readiness",AUDIT)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit()


class InstitutionalDecayJoinReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=compute()

    def test_audit_completeness(self):
        d=self.d
        self.assertEqual(d["fullyLabeledIndicators"],44)
        self.assertEqual(d["sourceRows"],5776)
        self.assertEqual(d["trustCountriesWith2025Observation"],33)
        self.assertEqual(d["trustCountriesWith2023And2025Pairs"],28)
        self.assertEqual(len(d["indicators"]),44)
        self.assertEqual(len({x["code"] for x in d["indicators"]}),44)

    def test_source_semantics_not_conflated(self):
        d=self.d
        self.assertEqual(d["conclusion"],
            "source_data_harmonization_audit_only_no_causal_model_identified")
        flagged={x["code"] for x in d["indicators"]
                 if x["containsSurveyTrustOutcome"]}
        self.assertEqual(flagged,{"PII_31314","PII_31315"})
        self.assertTrue(all(not x["canEnterCausalRegression"]
                            for x in d["indicators"]))
        self.assertTrue(all(not x["comparableAnnualPanelEstablished"]
                            for x in d["indicators"]))

    def test_source_fraction_and_missing_count_reconciliation(self):
        s=self.d["summary"]
        self.assertEqual(s["sourceReportedMissing"],1718)
        self.assertEqual(s["sourceReportedFractions"],1640)
        self.assertEqual(s["sourceNumericValues"],2418)
        self.assertEqual(sum([s["sourceReportedMissing"],s["sourceReportedFractions"],
                              s["sourceNumericValues"]]),5776)
        for i in self.d["indicators"]:
            self.assertEqual(sum(x["allRows"] for x in i["yearCoverage"]),
                             i["totalRawObservations"])
            self.assertEqual(sum(x["decimal"]+x["fraction"]+x["sourceMissing"]
                                 for x in i["yearCoverage"]),
                             i["totalRawObservations"])

    def test_written_audit_matches_reproducible_computation(self):
        persisted=json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(persisted,self.d)


if __name__=="__main__":
    unittest.main()
