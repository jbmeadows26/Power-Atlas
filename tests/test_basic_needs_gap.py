"""Power Atlas: poverty guideline is NOT actual local survival income."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/affordability/bergen-basic-needs-2026.json"
SCRIPT=ROOT/"platform/unified/basic-needs-gap.js"
CSS=ROOT/"platform/unified/visual-story-v6.css"

class BasicNeedsEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(DATA.read_text(encoding="utf-8"))
        cls.js=SCRIPT.read_text(encoding="utf-8")
    def test_county_and_source_provenance(self):
        self.assertEqual(self.d["year"],2026)
        self.assertEqual(self.d["schema"],"power-atlas.local-basic-needs-gap.2026.v1")
        self.assertEqual(self.d["location"]["countyFips"],"34003")
        self.assertEqual(self.d["location"]["verifiedZipExample"],"07010")
        sources={s["organization"] for s in self.d["sources"]}
        self.assertIn("U.S. Department of Health and Human Services",sources)
        self.assertIn("MIT Living Wage Institute",sources)
        self.assertEqual(len(self.d["scenarios"]),6)
        self.assertIn("administrative",self.d["benchmarks"]["hhs"])
        self.assertIn("Census",self.d["disclaimers"][0])
    def test_gross_income_and_expense_breakdown_consistent(self):
        for s in self.d["scenarios"]:
            with self.subTest(scenario=s["id"]):
                self.assertGreater(s["gross"],s["hhs"])
                self.assertLessEqual(abs(s["gross"]-s["net"]-s["taxes"]),2)
                if "expenseBreakdown" in s:
                    self.assertEqual(sum(s["expenseBreakdown"].values()),s["net"])
        ref=next(s for s in self.d["scenarios"] if s["id"]=="two-adults-one-worker-1")
        self.assertEqual((ref["hhs"],ref["gross"],ref["hourlyPerWorker"]),(27320,95330,45.83))
        self.assertEqual(ref["expenseBreakdown"]["childcare"],0)
        self.assertEqual(ref["expenseBreakdown"]["housing"],29764)
    def test_poverty_not_eligibility_or_actual_rent_claim(self):
        self.assertIn("not an actual living wage",self.d["benchmarks"]["hhs"])
        self.assertIn("not the Census official statistical",self.d["disclaimers"][0])
        self.assertIn("savings",str(self.d["disclaimers"]).lower())
        self.assertIn("not actual current rent listings",self.d["disclaimers"][3])
        self.assertIn("No user income",self.d["disclaimers"][4])
    def test_display_fail_closed_for_unverified_zip(self):
        self.assertIn('const SUPPORTED_ZIP="07010"',self.js)
        self.assertIn('zip!==SUPPORTED_ZIP',self.js)
        self.assertIn("No verified local basic-needs model is connected for this ZIP yet",self.js)
        self.assertIn('data/affordability/bergen-basic-needs-2026.json',self.js)
        self.assertNotIn('input type="number"',self.js)
        self.assertIn('src="basic-needs-gap.js"',
            (ROOT/"platform/unified/my-life.html").read_text(encoding="utf-8"))
        style=CSS.read_text(encoding="utf-8")
        self.assertIn("main > #pa-basic-needs{display:block!important}",style)
        self.assertIn("#pa-basic-needs[hidden]{display:none!important}",style)

if __name__=="__main__":
    unittest.main()
