"""Financial transmission source and classification tests. No network calls."""
import datetime as dt
import importlib.util
import pathlib
import sys
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "collect_market_transmission.py"
spec = importlib.util.spec_from_file_location("collect_market_transmission", SCRIPT)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
TODAY = dt.date(2026, 11, 20)


class FinancialTransmissionTests(unittest.TestCase):
    def test_household_parse_distinguishes_missing_future_and_valid_zero(self):
        csv_text = "DATE,UNRATE\n2026-11-01,4.3\n2026-11-10,.\n2026-11-19,0\n2026-11-21,999\n"
        parsed = collector.parse_fred_csv(csv_text, "UNRATE", TODAY)
        self.assertEqual(parsed, [("2026-11-01", 4.3), ("2026-11-19", 0.0)])

    def test_household_quarterly_observation_date_is_not_refresh_date(self):
        spec = next(s for s in collector.HOUSEHOLD_SERIES if s[0] == "TDSP")
        values = [("2026-01-01", 11.2), ("2026-04-01", 11.1)]
        m = collector.household_metric(spec, values, "2026-11-20T23:00:00Z", TODAY)
        self.assertEqual(m["period"], "2026-04-01")
        self.assertEqual(m["status"], "ok")
        self.assertEqual(m["changePoints"], -0.1)

    def test_invalid_fred_cannot_masquerade_as_no_delinquency(self):
        def bad(url, accept="application/json"):
            return "DATE,WRONG_SERIES\n2026-11-20,0\n"
        m, sources = collector.collect_households(
            dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc), fetch=bad
        )
        self.assertEqual(m, [])
        self.assertTrue(all(s["status"] == "error" for s in sources))

    def test_sec_cik_mapping_cannot_confuse_symbols(self):
        symbols = {
            "0": {"ticker": "NVDA", "cik_str": 1045810, "title": "NVIDIA CORP"},
            "1": {"ticker": "ANT", "cik_str": 2130357, "title": "ANTHROPIC PBC"},
            "2": {"ticker": "NOT_WATCHED", "cik_str": 1, "title": "OTHER"},
        }
        mapped = collector.parse_company_tickers(symbols)
        self.assertEqual(set(mapped), {"NVDA", "ANT"})
        self.assertEqual(mapped["ANT"]["cik"], 2130357)

    def test_filings_differentiate_debt_issuance_from_distress(self):
        company = {"cik": 1045810, "ticker": "NVDA", "name": "NVIDIA CORP"}
        rows = {
            "filings": {"recent": {
                "accessionNumber": ["0001045810-26-000123", "0001045810-26-000124", "0001045810-26-000126"],
                "form": ["8-K", "8-K", "10-Q"],
                "filingDate": ["2026-11-19", "2026-11-17", "2026-11-02"],
                "primaryDocument": ["financing.htm", "acceleration.htm", "report.htm"],
                "items": ["2.03", "2.04, 1.03", ""],
            }}
        }
        found, latest = collector.parse_sec_filings(rows, company, TODAY)
        self.assertEqual(len(found), 3)
        self.assertEqual({f["item"] for f in found}, {"2.03", "2.04", "1.03"})
        self.assertTrue(all(f["sourceUrl"].startswith("https://www.sec.gov/Archives/edgar/") for f in found))
        self.assertEqual(latest["form"], "10-Q")
        self.assertEqual([f["classification"] for f in found if f["item"] == "2.03"], ["financing-context"])

    def test_unsafe_filename_and_accession_rejected(self):
        self.assertIsNone(collector.sec_filing_url(1045810, "invalid", "ok.htm"))
        self.assertIsNone(collector.sec_filing_url(1045810, "0001045810-26-000123", "../file.htm"))
        self.assertIsNone(collector.sec_filing_url(1045810, "0001045810-26-000123", "bad/file.htm"))

    def test_balance_sheet_facts_keep_reported_periods(self):
        facts = {"cik": 1045810, "facts": {"us-gaap": {
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
                {"val": 1000, "end": "2026-07-31", "filed": "2026-09-01", "form": "10-Q", "accn": "0001045810-26-000123"},
                {"val": 900, "end": "2026-04-30", "filed": "2026-06-01", "form": "10-Q", "accn": "0001045810-26-000124"},
            ]}},
            "LongTermDebtNoncurrent": {"units": {"USD": [
                {"val": 200, "end": "2026-04-30", "filed": "2026-06-01", "form": "10-Q", "accn": "0001045810-26-000124"},
            ]}},
        }}}
        parsed = collector.parse_company_facts(facts, TODAY)
        self.assertEqual(parsed["cash"]["valueUSD"], 1000)
        self.assertNotEqual(parsed["cash"]["periodEnd"], parsed["longTermDebt"]["periodEnd"])
        self.assertNotIn("netDebt", parsed)

    def test_alerts_are_separate_issuer_and_household_evidence(self):
        fred = [{
            "id": "DRCCLACBS", "status": "ok", "changePoints": 0.31
        }, {
            "id": "BAMLC0A0CM", "status": "ok", "changePoints": 0.30
        }]
        filings = [
            {"id": "ABC:recent", "item": "2.04", "filed": "2026-11-19"},
            {"id": "ABC:finance", "item": "2.03", "filed": "2026-11-19"},
        ]
        alerts = collector.derive_alerts(fred, filings, TODAY)
        self.assertEqual({s["id"] for s in alerts},
                         {"ig-spread-widening", "card-delinquency", "sec-disclosure-review"})
        self.assertEqual([s["evidenceIds"] for s in alerts if s["id"] == "sec-disclosure-review"],
                         [["ABC:recent"]])

    def test_stale_data_never_creates_watch(self):
        data = [{"id": "DRCCLACBS", "status": "stale", "changePoints": 25}]
        self.assertEqual(collector.derive_alerts(data, [], TODAY), [])


if __name__ == "__main__":
    unittest.main()
