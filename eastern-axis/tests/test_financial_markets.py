import datetime as dt
import importlib.util
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "collect_financial_markets.py"
spec = importlib.util.spec_from_file_location("collect_financial_markets", SOURCE)
market = importlib.util.module_from_spec(spec)
spec.loader.exec_module(market)


def metric(series_id, values, now=dt.date(2026, 11, 20)):
    observations = [
        ((now - dt.timedelta(days=len(values)-1-i)).isoformat(), val)
        for i, val in enumerate(values)
    ]
    return market.build_metric(market.SPECS[series_id], observations,
                               "2026-11-20T20:00:00Z", now)


class MarketCollectorTests(unittest.TestCase):
    def test_fred_csv_filters_future_missing_and_infinite(self):
        content = "DATE,SP500\n2026-11-16,7000\n2026-11-17,.\n2026-11-18,6900\n2026-11-19,NaN\n2026-11-21,9999\n"
        rows = market.parse_csv(content, "SP500", dt.date(2026, 11, 20))
        self.assertEqual(rows, [("2026-11-16", 7000.0), ("2026-11-18", 6900.0)])

    def test_observation_date_column(self):
        rows = market.parse_csv("observation_date,VIXCLS\n2026-11-18,25\n2026-11-19,32\n",
                                "VIXCLS", dt.date(2026, 11, 20))
        self.assertEqual(len(rows), 2)

    def test_market_correction_is_not_a_credit_default(self):
        sp = metric("SP500", [100, 105, 104, 103, 100, 97, 90])
        nd = metric("NASDAQCOM", [100, 105, 104, 103, 100, 95, 86])
        signals = market.derive_signals([sp, nd])
        self.assertTrue(any(s["id"] == "equity-stress" for s in signals))
        self.assertFalse(any(s["id"] == "credit-spread-stress" for s in signals))
        self.assertFalse(any(s["id"] == "cross-market-stress" for s in signals))

    def test_credit_spread_requires_actual_widening(self):
        hy = metric("BAMLH0A0HYM2", [3.2, 3.2, 3.3, 3.3, 3.5, 3.6, 3.9])
        signals = market.derive_signals([hy])
        self.assertTrue(any(s["id"] == "credit-spread-stress" for s in signals))
        self.assertFalse(any(s["id"] == "cross-market-stress" for s in signals))

    def test_stale_quotes_do_not_trigger_new_alerts(self):
        sp = metric("SP500", [100, 105, 104, 103, 100, 97, 90])
        sp["status"] = "stale"
        self.assertEqual(market.derive_signals([sp]), [])

    def test_invalid_csv_does_not_become_zero(self):
        def bad_fetcher(_):
            return "invalid,data\n2026-11-20,0\n"
        snapshot = market.collect(dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc), fetcher=bad_fetcher)
        self.assertEqual(snapshot["status"], "unavailable")
        self.assertEqual(snapshot["metrics"], [])
        self.assertEqual(len(snapshot["sources"]), len(market.SERIES))
        self.assertTrue(all(s["status"] == "error" for s in snapshot["sources"]))

    def test_date_staleness_is_distinct_from_collection_time(self):
        m = market.build_metric(market.SPECS["SP500"], [("2026-11-02", 7000.0)],
                                "2026-11-20T23:00:00Z", dt.date(2026, 11, 20))
        self.assertEqual(m["status"], "stale")
        self.assertEqual(m["ageDays"], 18)
        self.assertIsNone(m["change1Pct"])


if __name__ == "__main__":
    unittest.main()
