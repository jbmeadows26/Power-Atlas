"""Safety and arithmetic regression checks for exact-UEI USAspending collection."""
from __future__ import annotations

import datetime as dt
import json
import unittest
from scripts import collect_business_federal_awards as m


class BusinessFederalAwardsTests(unittest.TestCase):
    def setUp(self):
        self.today = dt.date(2026, 11, 6)
        self.geo = m.ENTITIES[0]

    def record(self, amount="100.00", uei="JMLKZZ1NL2Z6", award="CONT_AWD_TEST_123", date="2024-03-01", mod="P00001"):
        return {
            "Action Date": date, "Recipient UEI": uei, "Recipient Name": "THE GEO GROUP, INC.",
            "Award ID": "TEST", "Mod": mod, "Transaction Amount": amount,
            "Awarding Agency": "Department of Homeland Security", "Awarding Sub Agency": "ICE",
            "Award Type": "DELIVERY ORDER", "generated_internal_id": award, "internal_id": "123",
        }

    def test_exact_uei_and_fiscal_dates(self):
        x = m.normalize_row(self.record(), "JMLKZZ1NL2Z6", dt.date(2023, 10, 1), dt.date(2024, 9, 30))
        self.assertEqual(x["_cents"], 10000)
        self.assertEqual(x["recipientUEI"], self.geo["uei"])
        self.assertIsNone(m.normalize_row(self.record(uei="OTHER1234567"), self.geo["uei"],
                                          dt.date(2023, 10, 1), dt.date(2024, 9, 30)))
        with self.assertRaisesRegex(ValueError, "lacks UEI"):
            m.normalize_row(self.record(uei=""), self.geo["uei"], dt.date(2023, 10, 1), dt.date(2024, 9, 30))
        with self.assertRaisesRegex(ValueError, "escaped"):
            m.normalize_row(self.record(date="2025-03-01"), self.geo["uei"], dt.date(2023, 10, 1), dt.date(2024, 9, 30))

    def test_obligation_netting_and_negative_modifications(self):
        def feed(p):
            self.assertEqual(p["filters"]["recipient_search_text"], ["JMLKZZ1NL2Z6"])
            return {"limit": m.PAGE_SIZE, "page_metadata": {"hasNext": False},
                    "results": [self.record(amount="1000.00", mod="A"),
                                self.record(amount="-400.00", mod="B"),
                                self.record(amount="150.00", mod="C", uei="SOMEOTHER123")]}
        fy = m.collect_year(self.geo, 2024, self.today, feed)
        self.assertEqual(fy["netObligationsUsd"], 600.0)
        self.assertEqual(fy["grossPositiveObligationsUsd"], 1000.0)
        self.assertEqual(fy["deobligationsUsd"], -400.0)
        self.assertEqual(fy["distinctPrimeAwards"], 1)
        self.assertEqual(fy["transactionCount"], 2)
        self.assertEqual(fy["otherRecipientUEIRowsExcluded"], 1)
        self.assertEqual(fy["sourcePagesRead"], 1)
        self.assertIn("2024", fy["endDate"])

    def test_cross_pages_and_deduplication(self):
        def page(p):
            if p["page"] == 1:
                return {"results": [self.record()], "page_metadata": {"hasNext": True}, "limit": 100}
            return {"results": [self.record(amount="20", mod="P2")],
                    "page_metadata": {"hasNext": False}, "limit": 100}
        r = m.collect_year(self.geo, 2024, self.today, page)
        self.assertEqual(r["netObligationsUsd"], 120)
        self.assertEqual(r["sourcePagesRead"], 2)
        def dup(p):
            return {"results": [self.record(), self.record()], "page_metadata": {"hasNext": False}, "limit": 100}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            m.collect_year(self.geo, 2024, self.today, dup)

    def test_fail_closed(self):
        for bad in ["nan", "Infinity", None, True]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    m.money_cents(bad)
        with self.assertRaises(ValueError):
            m.collect_year(self.geo, 2024, self.today,
                           lambda p: {"results": [], "page_metadata": {}})
        def runaway(p):
            return {"results": [self.record(mod=str(p["page"]))],
                    "page_metadata": {"hasNext": True}, "limit": 100}
        with self.assertRaisesRegex(RuntimeError, "page cap"):
            m.collect_year(self.geo, 2024, self.today, runaway)

    def test_partial_year_and_id_provenance(self):
        a, b = m.fiscal_window(2027, self.today)
        self.assertEqual(a.isoformat(), "2026-10-01")
        self.assertEqual(b.isoformat(), "2026-11-06")
        self.assertEqual({x["uei"] for x in m.ENTITIES},
                         {"JMLKZZ1NL2Z6", "L1WZRB6JKWJ4"})
        for entity in m.ENTITIES:
            self.assertTrue(entity["identitySource"].startswith("https://"))
        payload = m.build_request("L1WZRB6JKWJ4", a, b, 1)
        self.assertNotIn("api_key", json.dumps(payload))
        self.assertEqual(payload["filters"]["award_type_codes"], ["A", "B", "C", "D"])


if __name__ == "__main__":
    unittest.main()
