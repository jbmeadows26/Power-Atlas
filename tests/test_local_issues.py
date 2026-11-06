"""All-nine-issues locality, source and no-fabricated-result coverage tests."""
import json
import unittest
from pathlib import Path
from scripts import verify_local_acs_sources as audit

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"data/place-impact/local-measures-v1.json"
UI=ROOT/"platform/unified/my-life.html"

class AllIssueLocalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=json.loads(SPEC.read_text(encoding="utf-8"))

    def test_every_step2_topic_has_real_source_metric_spec(self):
        issues=self.s["issues"]
        expected={"housing","groceries","energy","health","work","schools",
                  "transport","public-services","representation"}
        self.assertEqual(set(issues),expected)
        self.assertEqual(self.s["provider"]["release"],"acs2024_5yr")
        self.assertIn("censusreporter.org",self.s["provider"]["api"])
        self.assertIn("2020",self.s["provider"]["dataYears"])
        self.assertTrue(self.s["boundaries"]["noZIPToExactJurisdiction"])
        for topic,config in issues.items():
            self.assertGreaterEqual(len(config["measures"]),2,topic)
            self.assertGreater(len(config["nextResearch"]),1)
            self.assertTrue(config["missing"] and config["localAuthority"])
            ids=set()
            for measure in config["measures"]:
                self.assertNotIn(measure["id"],ids)
                ids.add(measure["id"])
                self.assertRegex(measure["table"],r"^B\d{5}$")
                self.assertIn(measure["format"],{"usd","count","years","share","sumshare","sumcount"})
                for col in measure["columns"]:
                    self.assertRegex(col,r"^B\d{5}\d{3}$")
                    self.assertTrue(col.startswith(measure["table"]))
                self.assertTrue(measure["originalTable"].endswith(measure["table"]+".html"))
                self.assertGreater(len(measure["limits"]),30)
                self.assertTrue(measure["connected"])

    def test_reader_guides_and_comparable_denominators_for_all_nine(self):
        for topic, data in self.s["issues"].items():
            guide = data["readerGuide"]
            self.assertTrue(guide["heading"] and guide["meaning"], topic)
            self.assertTrue(guide["unknown"] and guide["next"], topic)
        schools = self.s["issues"]["schools"]["measures"]
        preschool = next(m for m in schools if m["id"] == "schools__preschool_count")
        school_rate = next(m for m in schools if m["id"] == "schools__enrollment_share")
        self.assertEqual(preschool["format"], "count")
        self.assertEqual(preschool["columns"], ["B14001003"])
        self.assertEqual(school_rate["format"], "share")
        self.assertEqual(school_rate["columns"], ["B14001002", "B14001001"])
        self.assertEqual(audit.scalar(school_rate, {
            "B14001002": 5214, "B14001001": 21000
        }), 24.83)
        html = UI.read_text(encoding="utf-8")
        self.assertIn('function canCompareGeographies(m)', html)
        self.assertIn('["share","sumshare","usd","years"].includes(m.format)', html)
        self.assertIn("National totals are intentionally not compared", html)
        self.assertNotIn("U.S. baseline (same ACS)", html)
        self.assertIn('id="localReaderMeaning"', html)
        self.assertIn('id="localNext"', html)
        self.assertIn("About this figure and its source", html)
        self.assertIn('Census survey, 2020–2024', html)

    def test_math_excludes_suppressed_and_invalid_denominators(self):
        m={"columns":["B22003002","B22003001"],"format":"share"}
        self.assertEqual(audit.scalar(m,{"B22003002":20,"B22003001":100}),20)
        self.assertEqual(audit.scalar(m,{"B22003002":0,"B22003001":100}),0)
        self.assertIsNone(audit.scalar(m,{"B22003002":-666666666,"B22003001":100}))
        self.assertIsNone(audit.scalar(m,{"B22003002":101,"B22003001":100}))
        self.assertIsNone(audit.scalar(m,{"B22003002":20,"B22003001":0}))
        self.assertIsNone(audit.scalar(m,{"B22003002":None,"B22003001":100}))
        u=next(m for m in self.s["issues"]["health"]["measures"] if m["format"]=="sumshare")
        data={col:0 for col in u["columns"]}
        data[u["columns"][-1]]=100
        data[u["columns"][0]]=10
        self.assertEqual(audit.scalar(u,data),10.0)
        data[u["columns"][1]]=-555555555
        self.assertIsNone(audit.scalar(u,data))

    def test_smoke_queries_all_nine_without_live_network(self):
        def feed(url):
            self.assertIn("geo_ids=86000US10001",url)
            self.assertNotIn("key=",url)
            tables=url.split("table_ids=",1)[1].split("&",1)[0].split("%2C")
            values={}
            for t in tables:
                measures=[m for cfg in self.s["issues"].values() for m in cfg["measures"] if m["table"]==t]
                columns={c:100 for m in measures for c in m["columns"]}
                for m in measures:
                    if m["format"] in ("share","sumshare"):
                        columns[m["columns"][-1]]=100000
                values[t]={"estimate":columns}
            return {"release":{"id":"acs2024_5yr"},
                    "tables":{t:{} for t in tables},
                    "data":{"86000US10001":values}}
        d=audit.collect(fetcher=feed)
        self.assertEqual(len(d["observations"]),9)
        self.assertTrue(d["sampleIsNotUserLocation"])
        self.assertEqual(d["sampleZCTA"],"10001")
        self.assertEqual(sum(len(x["measures"]) for x in d["observations"].values()),18)
        self.assertTrue(all(any(m["value"] is not None for m in x["measures"])
                            for x in d["observations"].values()))

    def test_ui_updates_every_category_not_only_first(self):
        s=UI.read_text(encoding="utf-8")
        self.assertIn("local-measures-v1.json",s)
        for fragment in ('id="localDataStatus"','id="localMetrics"',
                         'id="localResearchLinks"','id="localMissing"',
                         "evaluateMeasure(m,estimate)","renderLocalMeasures()",
                         "loadLocalMeasures(activeZIP,id)",
                         "loadLocalMeasures(zip,selected)",
                         "Unexpected ACS release","Census table ",
                         "U.S. share"):
            self.assertIn(fragment,s)
        self.assertIn("No values have been assumed",s)
        self.assertIn("No data has been inferred",s)
        self.assertNotIn("navigator.geolocation",s)
        self.assertNotIn("localStorage",s)

if __name__=="__main__":
    unittest.main()
