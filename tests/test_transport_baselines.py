"""Published transportation baseline-first interface: sources, arithmetic, no required user inputs."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"place-impact"
WEB=ROOT/"platform"/"unified"

class TransportationBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=json.loads((DATA/"transport-baselines-v1.json").read_text("utf-8"))
        cls.rates=json.loads((DATA/"transport-fares-v1.json").read_text("utf-8"))
        cls.ui=(WEB/"transport-cost-story.js").read_text("utf-8")
        cls.pen=(WEB/"transport-toll-penalties.js").read_text("utf-8")
        cls.v=(WEB/"transport-value-ezpass.js").read_text("utf-8")
        cls.page=(WEB/"my-life.html").read_text("utf-8")

    def test_national_spending_average_is_distinct_from_commute(self):
        self.assertEqual(self.b["schema"],"power-atlas.transport-baselines.v1")
        self.assertEqual(self.b["national"]["annual"],13492)
        self.assertEqual(self.b["national"]["monthly"],1124)
        self.assertIn("Mean per consumer unit",self.b["national"]["unit"])
        self.assertIn("NOT",self.b["national"]["warning"])
        self.assertTrue(self.b["national"]["source"].startswith("https://"))

    def test_regional_rows_join_exact_official_rate_ids(self):
        assert self.b["asOf"]=="2026-11-07"
        regions={x["id"]:x for x in self.b["regions"]}
        self.assertEqual(set(regions),{"NYNJ","CHI","OTHER"})
        fare={r["id"]:r for r in self.rates["fares"]}
        toll={r["id"]:r for r in self.rates["tolls"]}
        for reg in self.b["regions"]:
            self.assertTrue(reg["missing"])
            for item in reg["rows"]:
                self.assertEqual(sum(key in item for key in ("fareSourceId","tollSourceId")),1)
                a=fare.get(item.get("fareSourceId")) if "fareSourceId" in item else toll.get(item.get("tollSourceId"))
                self.assertIsNotNone(a,item["id"])
                self.assertGreater(a["price"],0,item["id"])
                self.assertTrue(a["source"].startswith("https://"))
        self.assertEqual({x["id"] for x in regions["NYNJ"]["rows"]},{"mta-local","path","mta-express","pa-peak","pa-offpeak","pa-mail","nyc-congestion"})
        self.assertEqual({x["id"] for x in regions["CHI"]["rows"]},{"cta-rail","cta-bus"})
        self.assertEqual(regions["OTHER"]["rows"],[])

    def test_standards_are_disclosed_not_mislabeled_as_measured(self):
        m=self.b["method"]
        self.assertEqual(m["standardWorkweekDays"],5)
        self.assertEqual(m["annualWorkweeks"],52)
        self.assertEqual(m["months"],12)
        self.assertEqual(m["transitPaidFaresPerWorkday"],2)
        self.assertEqual(m["tolledTripsPerWorkday"],1)
        self.assertIn("NOT a combined commute",m["disclosure"])
        self.assertIn("monthly pass",m["important"])

    def test_monthly_reference_arithmetic_and_fare_caps(self):
        fare={r["id"]:r for r in self.rates["fares"]}
        toll={r["id"]:r for r in self.rates["tolls"]}
        factor=5*52/12
        self.assertAlmostEqual(fare["mta-local"]["price"]*2*factor,130,places=2)
        self.assertAlmostEqual(fare["path"]["price"]*2*factor,140.8333333,places=5)
        self.assertAlmostEqual(fare["cta-bus"]["price"]*2*factor,97.5,places=2)
        self.assertAlmostEqual(fare["cta-rail"]["price"]*2*factor,108.3333333,places=5)
        self.assertAlmostEqual(toll["pa-peak"]["price"]*factor,363.7833333,places=5)
        self.assertAlmostEqual(toll["pa-mail"]["price"]*factor,504.8333333,places=5)
        self.assertAlmostEqual(min(fare["mta-express"]["price"]*2*5,fare["mta-express"]["capWeekly"])*52/12,290.3333333,places=5)
        self.assertEqual(fare["path"]["monthlyPass"],131.5)

    def test_no_input_required_to_render_costs_and_penalties(self):
        self.assertIn("showing.map(baselineRegion)",self.ui)
        self.assertIn("baselineRecord(row)",self.ui)
        self.assertIn("standardized monthly illustration",self.ui)
        self.assertIn("No personal input required".lower(),self.ui.lower())
        begin=self.ui.index("function build(){")
        end=self.ui.index("function totals(){")
        markup=self.ui[begin:end]
        self.assertNotIn("<input",markup)
        self.assertNotIn("sourceSection(",markup)
        self.assertNotIn("ts-picker-grid",markup)
        self.assertNotIn("ts-output",markup)
        self.assertIn("STANDARD_TOLL=5",self.pen)
        self.assertIn("operators().map(card)",self.pen)
        self.assertNotIn("<input",self.pen)
        self.assertIn('optionalCostPanel.hidden=id==="transport"',self.page)

    def test_zip_not_required_and_multi_agency_evidence_included(self):
        self.assertIn('current.id==="OTHER"?baselines.regions.filter(x=>x.id!=="OTHER")',[x.strip() for x in self.ui.splitlines() if 'current.id==="OTHER"' in x][0])
        self.assertIn('region==="OTHER"||x.region===region',self.v)
        self.assertIn("previewCards(options",self.v)
        self.assertIn('region==="OTHER"',self.pen)
        self.assertIn("No local operator has been identified",self.ui)
        self.assertIn("not your local fares",self.ui)

    def test_investigative_chain_kept_after_baseline(self):
        self.assertIn("renderAccountability()",self.ui)
        for marker in ('id="transportValuePanel"','id="transportEZPanel"','id="transportPenaltyPanel"'):
            self.assertIn(marker,self.ui)
        self.assertIn("Contracting relationships alone are not proof of corruption",self.pen)
        self.assertIn("not automatically dedicated to infrastructure improvements",self.pen)

if __name__=="__main__":
    unittest.main()
