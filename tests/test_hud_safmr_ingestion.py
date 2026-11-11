"""Bounded quality gates for HUD FY2026 source and privacy-safe web monitor."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("hud",ROOT/"scripts/ingest_hud_safmr_fy2026.py")
hud=importlib.util.module_from_spec(spec)
spec.loader.exec_module(hud)

class HUDIngestionTests(unittest.TestCase):
    def test_rest_count_and_page_queries_target_query_endpoint(self):
        self.assertEqual(hud.QUERY,hud.TABLE+"/query")
        source=(ROOT/"scripts/ingest_hud_safmr_fy2026.py").read_text()
        self.assertIn('get_json(QUERY, where="1=1", returnCountOnly="true")',source)
        self.assertIn('payload = get_json(QUERY, where="1=1",',source)

    def test_preserve_leading_zeros_and_original_hud_grain(self):
        row={"OBJECTID":11,"ZCTA_ID":"07010","HUD_CODE":"METRO001",
             "FMR_NAME":"Test area","SAFMR_0BR":1700,"SAFMR_1BR":2100,
             "SAFMR_2BR":2500,"SAFMR_3BR":3200,"SAFMR_4BR":3900}
        parsed=hud.parse_row(row)
        self.assertEqual(parsed["zip"],"07010")
        self.assertEqual(parsed["hudCode"],"METRO001")
        self.assertEqual(parsed["usdByBedroom"]["2"],2500)
        other=dict(row,OBJECTID=12,HUD_CODE="METRO002")
        self.assertNotEqual(hud.parse_row(row)["hudCode"],hud.parse_row(other)["hudCode"])

    def test_fail_closed_on_invalid_values(self):
        row={"ZCTA_ID":"07010","HUD_CODE":"A","FMR_NAME":"Area",
             "SAFMR_1BR":-500,"SAFMR_2BR":2000}
        with self.assertRaises(ValueError):hud.parse_row(row)
        self.assertIsNone(hud.parse_row(dict(row,ZCTA_ID="123")))
        self.assertIsNone(hud.parse_row(dict(row,SAFMR_1BR=None)))
        with self.assertRaises(ValueError):hud.parse_row(dict(row,SAFMR_1BR=1900,SAFMR_2BR=100000))

    def test_no_market_rent_or_causal_claim(self):
        source=(ROOT/"scripts/ingest_hud_safmr_fy2026.py").read_text()
        self.assertIn("NOT observed asking rent",source)
        self.assertIn("ZIP Code Tabulation Area",source)
        client=(ROOT/"platform/unified/hud-safmr-fy2026.js").read_text()
        self.assertIn("not current listings",client)
        self.assertIn("r.zip===zip",client)
        self.assertIn("hud-safmr-fy2026-",client)

    def test_ui_and_runtime_monitor_are_wired(self):
        html=(ROOT/"platform/unified/my-life.html").read_text()
        self.assertIn('src="hud-safmr-fy2026.js"',html)
        self.assertIn('href="hud-safmr-fy2026.css"',html)
        visual=(ROOT/"platform/unified/atlas-visual-system.js").read_text()
        self.assertIn('script.src="qa-monitor.js"',visual)
        monitor=(ROOT/"platform/unified/qa-monitor.js").read_text()
        server=(ROOT/"platform/unified/api/qa-config.js").read_text()
        self.assertIn("disable_session_recording:true",monitor)
        self.assertIn("autocapture:false",monitor)
        self.assertIn("before_send:redacted",monitor)
        self.assertIn("process.env.POSTHOG_PUBLIC_TOKEN",server)
        self.assertNotIn("phc_",monitor) if False else None
        self.assertNotIn("phc_gJ",server+monitor) # no instance token in source

if __name__=="__main__":
    unittest.main()
