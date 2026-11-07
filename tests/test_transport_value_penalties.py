"""Transportation price-versus-service, E-ZPass and toll-penalty source integrity."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"place-impact"
APP=ROOT/"platform"/"unified"
VALUE=DATA/"transport-value-audit-v1.json"
EZPASS=DATA/"ezpass-value-audit-v1.json"
PENALTIES=DATA/"toll-penalties-v1.json"
VALUE_JS=APP/"transport-value-ezpass.js"
PEN_JS=APP/"transport-toll-penalties.js"
TRANSPORT_JS=APP/"transport-cost-story.js"
PAGE=APP/"my-life.html"

class TransportationTransparencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value=json.loads(VALUE.read_text("utf-8"))
        cls.ez=json.loads(EZPASS.read_text("utf-8"))
        cls.pen=json.loads(PENALTIES.read_text("utf-8"))
        cls.value_js=VALUE_JS.read_text("utf-8")
        cls.pen_js=PEN_JS.read_text("utf-8")
        cls.transport_js=TRANSPORT_JS.read_text("utf-8")
        cls.page=PAGE.read_text("utf-8")

    def test_agency_scoped_fare_outcome_measure(self):
        self.assertEqual(self.value["schema"],"power-atlas.transport-value-audit.v1")
        ids={x["id"] for x in self.value["agencies"]}
        self.assertTrue({"njt","nyct","path","panynj","cta"}<=ids)
        nj=next(x for x in self.value["agencies"] if x["id"]=="njt")
        rail=next(x for x in nj["performance"] if x["id"]=="rail-otp")
        self.assertEqual((rail["older"],rail["newer"]),(92.1,89.2))
        self.assertEqual((rail["olderPeriod"],rail["newerPeriod"]),("FY2023","FY2025"))
        self.assertTrue(rail["periodComparable"])
        cta=next(x for x in self.value["agencies"] if x["id"]=="cta")
        self.assertEqual((cta["fares"][0]["before"],cta["fares"][0]["after"]),(2.5,2.5))
        for ag in self.value["agencies"]:
            self.assertTrue(ag["region"] in ("NYNJ","CHI"))
            self.assertTrue(ag["ratingBasis"])
            for price in ag["fares"]:
                self.assertTrue(price["source"].startswith("https://"))
            for item in ag["performance"]:
                self.assertTrue(item["sourceOlder"].startswith("https://"))
                self.assertTrue(item["sourceNewer"].startswith("https://"))
            for cap in ag["capital"]:
                self.assertTrue(cap["allocationSource"].startswith("https://"))
                self.assertIn("warning",cap)

    def test_capital_authorized_not_declared_delivered(self):
        mta=next(x for x in self.value["agencies"] if x["id"]=="nyct")
        cap=mta["capital"][0]
        self.assertEqual(cap["authorizedBillions"],68.4)
        self.assertEqual(cap["committedBillions"],7.5)
        self.assertAlmostEqual(cap["committedBillions"]/cap["authorizedBillions"],.1096491,places=4)
        self.assertIn("not",cap["warning"].lower())
        self.assertIn("not service improvements",self.value["rules"][6].lower())
        self.assertIn("committed",self.value_js)
        self.assertIn("not the same as a finished repair",self.value_js)

    def test_ezpass_is_agency_scoped(self):
        self.assertEqual(self.ez["schema"],"power-atlas.ezpass-value-audit.v1")
        ids={x["id"] for x in self.ez["agencies"]}
        self.assertEqual(ids,{"nysta","mta-toll","panynj-ezpass","illinois-ipass"})
        for ag in self.ez["agencies"]:
            self.assertIn(ag["region"],("NYNJ","CHI"))
            self.assertTrue(ag["verdict"])
            self.assertTrue(ag["scope"])
            self.assertGreater(len(ag["money"]),0)
            self.assertTrue(ag["next"])
            for entry in ag["prices"]+ag["outcomes"]+ag["delivery"]:
                self.assertTrue(entry["source"].startswith("https://"),entry["name"])
        nysta=next(x for x in self.ez["agencies"] if x["id"]=="nysta")
        audit=next(x for x in nysta["outcomes"] if "25A" in x["name"])
        self.assertIn("NOT a statewide error rate",audit["limitation"])
        ill=next(x for x in self.ez["agencies"] if x["id"]=="illinois-ipass")
        self.assertTrue(any(x["kind"]=="data_gap" for x in ill["delivery"]))

    def test_fee_per_notice_is_not_fee_per_transaction(self):
        self.assertEqual(self.pen["schema"],"power-atlas.toll-penalties.v1")
        groups={g["id"]:g["operatorIds"] for g in self.pen["groups"]}
        self.assertIn("ny-thruway",groups["NYNJ"])
        self.assertIn("il-standard",groups["CHI"])
        ops={x["id"]:x for x in self.pen["operators"]}
        self.assertEqual(len(ops),6)
        stage=lambda name,key:next(x for x in ops[name]["stageDefinitions"] if x["id"]==key)
        ny=stage("ny-thruway","violation")
        mta=stage("ny-mta","violation")
        self.assertEqual((ny["feePerNotice"],ny["feePerTxn"]),(50,0))
        self.assertEqual((mta["feePerTxn"],mta["feePerNotice"]),(50,0))
        self.assertEqual(stage("ny-mta","late")["feePerBill"],5)
        # For three $5 tolls grouped into one notice, fees must not be tripled for NYSTA.
        n=3
        compute=lambda s:5*n+s["feePerTxn"]*n+s["feePerBill"]+s["feePerNotice"]
        self.assertEqual(compute(ny),65)
        self.assertEqual(compute(mta),165)
        self.assertEqual(compute(stage("ny-mta","late")),20)

    def test_illinois_grace_invoice_escalation_and_suspended_additional_fine(self):
        ops={x["id"]:x for x in self.pen["operators"]}
        std={s["id"]:s for s in ops["il-standard"]["stageDefinitions"]}
        route390={s["id"]:s for s in ops["il390"]["stageDefinitions"]}
        self.assertEqual(std["first"]["feePerTxn"],0)
        self.assertEqual(std["late"]["feePerTxn"],3)
        self.assertEqual(std["third"]["feePerTxn"],8)
        self.assertEqual(std["violation"]["feePerTxn"],28)
        self.assertEqual(route390["late"]["feePerTxn"],1.5)
        self.assertEqual(route390["third"]["feePerTxn"],4)
        self.assertEqual(route390["violation"]["feePerTxn"],14)
        self.assertIn("excluded",ops["il-standard"]["limit"])
        self.assertTrue(std["collections"]["unknownFurtherFees"])
        self.assertIn("I-PASS Assist",ops["il-standard"]["relief"])

    def test_new_jersey_registration_and_fee_waivers(self):
        op=next(x for x in self.pen["operators"] if x["id"]=="nj-turnpike")
        violation=next(x for x in op["stageDefinitions"] if x["id"]=="violation")
        late=next(x for x in op["stageDefinitions"] if x["id"]=="late")
        self.assertEqual(violation["feePerTxn"],50)
        self.assertIsNone(late["feePerTxn"])
        self.assertIn("$500",next(x for x in op["stageDefinitions"] if x["id"]=="collections")["description"])
        self.assertIn("inadvertent",op["relief"].lower())
        pa=next(x for x in self.pen["operators"] if x["id"]=="ny-panynj")
        self.assertIn("15 days",next(x for x in pa["stageDefinitions"] if x["id"]=="violation")["description"])

    def test_undocumented_collections_fee_and_pilot_not_added(self):
        for op in self.pen["operators"]:
            self.assertTrue(op["sources"])
            self.assertTrue(op["verifiedAsOf"])
            self.assertTrue(op["limit"])
            for st in op["stageDefinitions"]:
                if st.get("unknownFurtherFees"):
                    self.assertIn("collections",st["id"])
        self.assertIn("No collections costs",self.pen["rules"][5])
        self.assertIn("additional post-order",self.pen["rules"][6])
        self.assertIn("revenue-sharing",self.pen["financialWatch"][1]["description"])

    def test_ui_mounts_and_source_date_privacy(self):
        for anchor in ('id="transportValuePanel"','id="transportEZPanel"',
                       'id="transportPenaltyPanel"'):
            self.assertIn(anchor,self.transport_js)
        self.assertIn("window.PowerAtlasTransportValue?.render()",self.transport_js)
        self.assertIn("window.PowerAtlasTollPenalty?.render()",self.transport_js)
        self.assertIn('transport-value-ezpass.js?v=',self.page)
        self.assertIn('transport-toll-penalties.js?v=',self.page)
        self.assertIn(".tp-stages",self.page)
        self.assertIn(".tv-value-grid",self.page)
        self.assertIn("not your liability",self.pen_js.lower())
        self.assertIn("feePerNotice",self.pen_js)
        self.assertIn("window.PowerAtlasGetBenchmarkContext",self.pen_js)
        for value in (self.value_js,self.pen_js):
            for forbidden in ("localStorage","sessionStorage","sendBeacon","navigator.geolocation"):
                self.assertNotIn(forbidden,value)

    def test_js_syntax(self):
        if not shutil.which("node"):self.skipTest("node unavailable")
        for path in (VALUE_JS,PEN_JS,TRANSPORT_JS):
            with self.subTest(path=path.name):
                r=subprocess.run(["node","--check",str(path)],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)

if __name__=="__main__":unittest.main()
