"""CoreCivic-specific UEI, date and no-fabricated-aggregation tests."""
import datetime as dt
import unittest
from scripts import collect_corecivic_awards as core


class CoreCivicAwardTests(unittest.TestCase):
    def test_exact_registered_recipient(self):
        self.assertEqual(core.CORECIVIC["uei"], "HJGMJN1JKL46")
        self.assertEqual(core.CORECIVIC["fecCommitteeId"], "C00366468")
        self.assertTrue(core.CORECIVIC["identitySource"].startswith("https://www.usaspending.gov/"))
        self.assertNotEqual(core.CORECIVIC["uei"], "JMLKZZ1NL2Z6")

    def test_complete_period_and_zero_are_distinct_from_missing(self):
        def mock(request):
            self.assertEqual(request["filters"]["recipient_search_text"], ["HJGMJN1JKL46"])
            return {"results": [], "page_metadata": {"hasNext": False}, "limit": 100}
        d = core.collect(today=dt.date(2026, 11, 6), fetcher=mock)
        self.assertEqual(d["schema"], "power-atlas.corecivic-federal-contracts.v1")
        self.assertEqual(len(d["entity"]["years"]), 10)
        self.assertEqual(d["entity"]["years"][-1]["fiscalYear"], 2027)
        self.assertTrue(d["entity"]["years"][-1]["partialFiscalYear"])
        self.assertEqual(d["entity"]["years"][-1]["transactionCount"], 0)
        self.assertIn("No FEC political donation", d["limitations"][3])

    def test_malformed_response_cannot_be_published(self):
        with self.assertRaises(ValueError):
            core.collect(today=dt.date(2026, 11, 6), fetcher=lambda req: {"results": []})
        with self.assertRaises(ValueError):
            core.publish({"schema": "wrong", "entity": {"uei": "HJGMJN1JKL46", "years": [1]}})

if __name__ == "__main__":
    unittest.main()
