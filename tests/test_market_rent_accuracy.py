"""Market vs HUD vs Census must remain distinct in every public ZIP story."""
import json
from datetime import date
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/housing/market-asking-rent-cliffside-park-2026-11.json"
V6=ROOT/"platform/unified/visual-story-v6.js"
MARKET=ROOT/"platform/unified/market-rent-primary.js"
HUD=ROOT/"platform/unified/hud-rent-current.js"
HOME=ROOT/"platform/unified/my-life.html"

class MarketRentAccuracyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(DATA.read_text(encoding="utf-8"))
        cls.visual=V6.read_text(encoding="utf-8")
        cls.client=MARKET.read_text(encoding="utf-8")

    def test_source_is_listing_market_not_hud_or_signed_leases(self):
        d=self.data
        self.assertEqual(d["schema"],"power-atlas.market-asking-rent-snapshot.v1")
        self.assertEqual(d["measure"]["statistic"],
          "provider-reported average advertised rent by bedroom and property type")
        self.assertTrue(d["source"]["url"].startswith("https://www.trulia.com/"))
        self.assertFalse(d["geography"]["zipSpecific"])
        self.assertEqual(d["geography"]["kind"],"municipality")
        self.assertEqual(d["geography"]["name"],"Cliffside Park")
        self.assertEqual(d["geography"]["relatedZipCode"],"07010")
        self.assertIn("not signed leases",d["measure"]["notices"][0].lower())
        self.assertIn("not an automatic live listing feed",d["measure"]["notices"][3].lower())
        self.assertLessEqual((date.today()-date.fromisoformat(d["retrievedOn"])).days,120)

    def test_bedroom_property_type_rents_are_not_invented(self):
        d=self.data["propertyTypes"]
        self.assertEqual(d["all"]["bedrooms"],{"1":2000,"2":2850,"3":4200,"4":5500})
        self.assertEqual(d["apartment_condo"]["bedrooms"],{"1":2000,"2":2850,"3":3200,"4":3678})
        self.assertEqual(d["house"]["bedrooms"],{"1":2350,"2":2400,"3":4200,"4":5500})
        self.assertIsNone(d["townhouse"]["bedrooms"]["2"])
        self.assertEqual(d["townhouse"]["bedrooms"]["3"],5200)
        for group in d.values():
            for bedroom in ["1","2","3","4"]:
                self.assertIn(bedroom,group["bedrooms"])
                value=group["bedrooms"][bedroom]
                self.assertTrue(value is None or (isinstance(value,int) and 400<=value<=50000))

    def test_no_unlicensed_guesses_or_previous_false_substitution(self):
        c=self.client
        self.assertIn('const SUPPORTED="07010"',c)
        self.assertIn('if(zip!==SUPPORTED){',c)
        self.assertIn('Promise.resolve().then(()=>{if(run===serial)emit(zip,"unavailable");})',c)
        self.assertIn('m.geography.zipSpecific!==false',c)
        self.assertIn('Market snapshot is stale',c)
        self.assertIn('poweratlas:market-rent-ready',c)
        self.assertNotIn('poweratlas:hud-benchmarks-ready',c)
        self.assertNotIn('1837',c+self.visual)
        self.assertNotIn('4450',c+self.visual)
        self.assertIn("provider-reported",DATA.read_text(encoding="utf-8").lower())

    def test_market_primary_hud_optional_comparison(self):
        self.assertIn('src="market-rent-primary.js"',HOME.read_text(encoding="utf-8"))
        self.assertIn('src="hud-rent-current.js"',HOME.read_text(encoding="utf-8"))
        self.assertIn("MARKET ASKING RENT",self.visual)
        self.assertIn('vs6-zip-market-select',self.visual)
        self.assertIn("No verified, recent asking-rent figures for this ZIP",self.visual)
        self.assertIn("HUD voucher benchmark",self.visual)
        self.assertIn("HUD Small Area Fair Market Rents",HUD.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
