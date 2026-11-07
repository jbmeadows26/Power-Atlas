"""Public-disclosure interval and source-coverage regression tests."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from congress_disclosure_intervals import disclosure_band, disclosed_position_interval, validate_member_annual_disclosure

DATA = ROOT / "data/research/political-authenticity"

def item(lo, hi, owner="self"):
    return {"owner": owner, "valueStatus": "reported_range" if hi is not None else "reported_open_upper",
            "valueMinUSD": lo, "valueMaxUSD": hi}

class FinancialDisclosureQualityTests(unittest.TestCase):
    def test_exact_ranges_never_used_as_point_wealth(self):
        actual = disclosed_position_interval([item(1001,15000)], [item(10001,15000)],
                  asset_section_complete=True, liability_section_complete=True)
        self.assertEqual(actual["disclosedNetLowerUSD"], -13999)
        self.assertEqual(actual["disclosedNetUpperUSD"], 4999)
        self.assertNotIn("estimatedWealthUSD", actual)
    def test_open_ended_asset_has_no_upper_bound(self):
        result = disclosed_position_interval([item(1000000,None)], [item(0,0)],
                    asset_section_complete=True, liability_section_complete=True)
        self.assertEqual(result["disclosedNetLowerUSD"],1000000)
        self.assertIsNone(result["disclosedNetUpperUSD"])
    def test_open_ended_liability_has_no_lower_bound(self):
        result = disclosed_position_interval([item(1000,2000)], [item(1000,None)],
                    asset_section_complete=True, liability_section_complete=True)
        self.assertIsNone(result["disclosedNetLowerUSD"])
        self.assertEqual(result["disclosedNetUpperUSD"],1000)
    def test_missing_schedules_are_not_zero(self):
        result = disclosed_position_interval([],[],asset_section_complete=False,liability_section_complete=True)
        self.assertIsNone(result["assets"])
        self.assertEqual(result["status"],"not_estimable_incomplete_schedules")
        self.assertIsNone(result["disclosedNetUpperUSD"])
    def test_genuinely_verified_empty_schedules_can_be_zero(self):
        result = disclosed_position_interval([],[],asset_section_complete=True,liability_section_complete=True)
        self.assertEqual(result["disclosedNetLowerUSD"],0)
        self.assertEqual(result["disclosedNetUpperUSD"],0)
    def test_unreported_or_reversed_values_fail_closed(self):
        for lo,hi in [(None,15000),(50000,1000),(-100,500),(True,1000)]:
            with self.assertRaises(ValueError):disclosure_band(item(lo,hi))
    def test_spouse_is_not_silently_converted_to_self(self):
        self.assertEqual(disclosure_band(item(1001,15000,owner="spouse")),(1001,15000))
        with self.assertRaises(ValueError):disclosure_band(item(1001,15000,owner="unknown person"))
    def test_one_stale_daily_trade_delta_is_not_congress_census(self):
        x=json.loads((DATA/"congress-trades-source-audit-2026-11-05.json").read_text(encoding="utf-8"))
        s=x["sample"]
        self.assertEqual(x["status"],"OBSERVED_STALE_NONREPRESENTATIVE_DAILY_DELTA")
        self.assertEqual(s["transactionRows"],58)
        self.assertEqual(s["uniqueTransactionIDs"],s["transactionRows"])
        self.assertEqual(s["uniqueBioguideIDs"],3)
        self.assertEqual(sum(s["chambers"].values()),58)
        self.assertEqual(sum(s["sides"].values()),58)
        self.assertEqual(sum(s["ownerType"].values()),58)
        self.assertEqual(s["rowsWithoutPrimarySourceURL"],0)
        self.assertLess(s["amountRangeSumLowerUSD"],s["amountRangeSumUpperUSD"])
    def test_annual_holdings_count_is_not_all_member_wealth(self):
        x=json.loads((DATA/"congress-holdings-2025-source-coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(x["readableMemberReports"],508)
        self.assertEqual(x["membersWithSp500DirectSharesOrOptions"],178)
        self.assertAlmostEqual(x["holderShareAmongReadableReports"],178/508)
        self.assertEqual(x["paperScannedReportsUnparsed"],43)
        self.assertEqual(sum(s["positions"] for s in x["sectorSummaries"]), x["sp500Positions"])
        self.assertAlmostEqual(x["sectorRoundedShareSumPct"],100.1)
        self.assertNotIn("estimatedNetWorth",x)
    def _verified_record(self):
        return {
            "bioguideId": "A000001",
            "reportType": "annual",
            "filingIdentity": "annual-2025-a",
            "originalFilingURL": "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025/123.pdf",
            "filingDate": "2026-05-01",
            "observedAt": "2026-11-07",
            "licenseOrReuseRestriction": "5 USC 13107(c)",
            "primarySourceVerified": True,
            "assetScheduleComplete": True,
            "liabilityScheduleComplete": True,
            "assets": [{**item(1001, 15000), "sourcePage": "p2"}],
            "liabilities": [{**item(0, 1000), "sourcePage": "p4"}],
        }
    def test_official_filing_complete_intervals(self):
        x = validate_member_annual_disclosure(self._verified_record())
        self.assertEqual(x["interval"]["disclosedNetLowerUSD"], 1)
        self.assertEqual(x["interval"]["disclosedNetUpperUSD"], 15000)
        self.assertIn("not exact", x["interpretation"])
    def test_unverified_filing_keeps_intervals_unknown(self):
        x = self._verified_record()
        x["primarySourceVerified"] = False
        result = validate_member_annual_disclosure(x)
        self.assertIsNone(result["interval"]["disclosedNetLowerUSD"])
        self.assertIsNone(result["interval"]["disclosedNetUpperUSD"])
    def test_partial_schedule_keeps_unknown_net_bounds(self):
        x = self._verified_record()
        x["liabilityScheduleComplete"] = False
        result = validate_member_annual_disclosure(x)
        self.assertIsNone(result["interval"]["disclosedNetLowerUSD"])
    def test_no_lookalike_or_http_filing_sources(self):
        for url in (
            "https://disclosures-clerk.house.gov.evil.example/2025/123.pdf",
            "http://disclosures-clerk.house.gov/2025/123.pdf",
            "https://evil.example@disclosures-clerk.house.gov/2025/123.pdf",
            "https://disclosures-clerk.house.gov/",
        ):
            x = self._verified_record()
            x["originalFilingURL"] = url
            with self.assertRaises(ValueError):
                validate_member_annual_disclosure(x)
    def test_source_metadata_required(self):
        for field in ("filingIdentity", "filingDate", "observedAt", "licenseOrReuseRestriction"):
            x = self._verified_record()
            x[field] = None
            with self.assertRaises(ValueError):
                validate_member_annual_disclosure(x)
    def test_spouse_and_filing_locator_preserved(self):
        x = self._verified_record()
        x["assets"][0]["owner"] = "spouse"
        self.assertEqual(validate_member_annual_disclosure(x)["interval"]["assets"]["lowerUSD"], 1001)
        x["assets"][0].pop("sourcePage")
        with self.assertRaises(ValueError):
            validate_member_annual_disclosure(x)
    def test_transactions_rejected_as_holdings(self):
        x = self._verified_record()
        x["reportType"] = "periodic_transaction"
        with self.assertRaises(ValueError):
            validate_member_annual_disclosure(x)
    def test_frontend_preserves_source_and_missingness_language(self):
        js=(ROOT/"site/political-authenticity.js").read_text(encoding="utf-8")
        self.assertIn("paFinanceMetrics",js)
        self.assertIn("2025 annual holdings",js)
        self.assertIn("STALE September 2026",js)

if __name__ == "__main__":
    unittest.main()
