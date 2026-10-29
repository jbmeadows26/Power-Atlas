"""Offline parser tests for authentic Census fixed-width legacy format.

A synthetic fixture tests *format behavior* only, never creates fiscal estimates.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import collect_state_fiscal_legacy as legacy


def row(state, item="F01", amount="000000001234", survey="13", data_year="13", origin="00"):
    s = f"{state:02d}"+"0"*12+item+amount+survey+data_year+origin
    assert len(s) == 35, (s,len(s))
    return s


def fixture():
    states = sorted(int(x) for x in legacy.STATE_CODES)
    return ("\n".join(row(st, code) for st in states for code in ("F01","G01","K01"))+"\n").encode("ascii")


class CensusLegacyFormatTests(unittest.TestCase):
    def test_format_sample_valid_without_claiming_real_fiscal_data(self):
        r = legacy.parse_records(fixture(), 2013)
        self.assertEqual(r["stateGovernmentCount"], 50)
        self.assertEqual(r["capitalFamilyRowsRetained"], 150)
        self.assertEqual(r["capitalFamilyRowCounts"], {"F":50,"G":50,"K":50})
        self.assertEqual(r["records"][0]["amountAsPublished"], "000000001234")

    def test_reject_misaligned_fixed_width(self):
        bad = fixture().splitlines()
        bad[0] += b"X"
        with self.assertRaisesRegex(ValueError,"Invalid record width"):
            legacy.parse_records(b"\n".join(bad),2013)

    def test_reject_duplicate_government_code_items(self):
        rows = fixture()
        with self.assertRaisesRegex(ValueError,"Repeated"):
            legacy.parse_records(rows + rows.splitlines()[0]+b"\n",2013)

    def test_invalid_source_decade_and_vintage(self):
        for yr in (1999,2016,2022,2026):
            with self.assertRaisesRegex(ValueError,"2000-2015"):
                legacy.read_source(yr,fetcher=lambda _:fixture())

    def test_dont_accept_non_ascii(self):
        with self.assertRaisesRegex(ValueError,"ASCII"):
            legacy.parse_records(fixture()+b"\xff",2013)

    def test_no_state_code_09_for_dc(self):
        raw = fixture().decode()
        for code in ("F01", "G01", "K01"):
            raw = raw.replace(row(1,code),row(9,code))
        raw = raw.encode()
        result=legacy.parse_records(raw,2013)
        self.assertEqual(result["stateGovernmentCount"],49)
        self.assertNotIn("09", {r["stateGovernmentCode"][:2] for r in result["records"]})

    def test_reject_undercoverage(self):
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            legacy.parse_records((row(1)+"\n")*9,2013)

    def test_preserve_but_dont_sum_raw_amounts(self):
        obj=legacy.make_document(2013, fixture(), "https://www2.census.gov/govs/state/13state35.txt")
        self.assertEqual(obj["currencyUnits"],"unverified_do_not_assume_raw_amount_scale")
        self.assertEqual(obj["publicationStatus"],"official_raw_code_family_staged_not_harmonized")
        self.assertNotIn("capitalSpendingShare",obj)
        self.assertEqual(obj["source"]["bytesRead"], len(fixture()))

    def test_bounded_fetcher_and_no_network_fixture(self):
        def get(url):
            self.assertEqual(url,"https://www2.census.gov/govs/state/13state35.txt")
            return fixture()
        data,url=legacy.read_source(2013,fetcher=get)
        self.assertEqual(data,fixture())

    def test_atomic_fetch_validation_precedes_writes(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(legacy,"OUTPUT",Path(temp)):
            def bad_fy(url):
                return fixture() if "13state35" in url else b"not a 35 character file"
            with self.assertRaises(ValueError):
                legacy.write_outputs([2013,2014],fetcher=bad_fy)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_generate_index_is_readiness_guard_not_estimate(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(legacy,"OUTPUT",Path(tmp)):
            d=legacy.write_outputs([2013],fetcher=lambda _:fixture())
            self.assertEqual(d["spendingShares"],None)
            self.assertEqual(d["electionCycleEstimates"],None)
            self.assertEqual(d["years"],[2013])
            saved=json.loads((Path(tmp)/"fy2013.json").read_text())
            self.assertEqual(len(saved["records"]),150)
            self.assertEqual(d["sources"][0]["capitalFamilyRowsRetained"],150)

    def test_output_stability(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(legacy,"OUTPUT",Path(tmp)):
            legacy.write_outputs([2013],fetcher=lambda _:fixture())
            one=(Path(tmp)/"fy2013.json").read_bytes()
            legacy.write_outputs([2013],fetcher=lambda _:fixture())
            self.assertEqual(one,(Path(tmp)/"fy2013.json").read_bytes())


if __name__=="__main__":
    unittest.main()
