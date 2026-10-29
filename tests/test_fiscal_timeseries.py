"""Offline synthetic validation of real Census time-series aggregate ingestion.

No synthetic rows are published; fixtures are used solely to test invariants.
"""
import io
import unittest
import zipfile

from scripts.collect_census_state_timeseries import METRICS, process_archive, YEAR_SET


def build_fixture(error=None):
    header=["#GEO_ID","ST","GEOTYPE","GOVTYPE","YEAR","CATEGORY","AGG_DESC",
            "AGG_DESC_LABEL","ITEM_CODE","AMOUNT","AMOUNT_F"]
    lines=["|".join(header)]
    states=[f"{i:02d}" for i in list(range(1,9))+list(range(10,52))]
    for state in states:
        for year in sorted(YEAR_SET):
            for code,(key,label) in METRICS.items():
                if error=="missing" and state=="01" and year==2013 and code=="SF0178":
                    continue
                amount={"SF0132":14000,"SF0175":10000,"SF0176":9000,
                        "SF0177":3000,"SF0178":1000}[code]
                if error=="capital_gt_total" and state=="01" and year==2013 and code=="SF0178":
                    amount=12000
                if error=="missing_numeric" and state=="01" and year==2013 and code=="SF0178":
                    amount="."
                if error=="wrong_label" and state=="01" and year==2013 and code=="SF0178":
                    label="Not Official Label"
                fields=[f"0400000US{state}",state,"02","002",str(year),"02",code,
                        label,"AGG",str(amount),""]
                lines.append("|".join(fields))
    if error=="duplicate":
        lines.append(lines[1])
    data=("\n".join(lines)+"\n").encode("utf-8")
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("GOVSSTATEFINTIMESERIES.dat",data)
        z.writestr("GOVSSTATEFINTIMESERIES_FIELDS.txt",
                   "Field_Name|Label|Field_Type|Field_Length|Number_of_Decimals\n"
                   "AMOUNT|Amount ($1,000)|NUMBER|20|0\n")
    return buffer.getvalue()


class CensusStateTimeSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.correct=build_fixture()

    def test_state_and_year_keys_are_complete(self):
        d=process_archive(self.correct,enforce_source_hash=False)
        self.assertEqual(len(d["records"]),650)
        self.assertEqual(d["coverage"]["yearCount"],13)
        self.assertEqual(d["coverage"]["stateGovernmentsPerYear"],50)
        self.assertEqual(d["coverage"]["officialAggregateRowsRetained"],3250)
        self.assertEqual(d["coverage"]["sourceRowsInspected"],3250)

    def test_ratio_is_direct_capital_outlay_over_total_direct(self):
        d=process_archive(self.correct,enforce_source_hash=False)
        r=next(row for row in d["records"] if row["fipsState"]=="01" and row["fiscalYear"]==2016)
        self.assertEqual(r["totalsThousandsUSD"]["capitalOutlay"],1000)
        self.assertEqual(r["totalsThousandsUSD"]["directExpenditure"],10000)
        self.assertEqual(r["capitalOutlayShareOfDirectExpenditureBasisPoints"],1000)
        self.assertNotIn("FPlusGPlusK",r)

    def test_historical_break_does_not_silently_get_combined(self):
        d=process_archive(self.correct,enforce_source_hash=False)
        regimes={r["fiscalYear"]:r["classificationRegime"] for r in d["records"]}
        self.assertEqual(regimes[2021],"pre_2022")
        self.assertEqual(regimes[2022],"post_2022_reclassified")
        self.assertFalse(d["electionClockAttached"])
        self.assertIsNone(d["causalEstimates"])
        self.assertIsNone(d["electoralShortTermismModel"])

    def test_unverified_source_change_does_not_publish(self):
        with self.assertRaisesRegex(ValueError,"Official source ZIP changed"):
            process_archive(self.correct,enforce_source_hash=True)

    def test_missing_year_state_aggregate_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing required official summary aggregates"):
            process_archive(build_fixture("missing"),enforce_source_hash=False)

    def test_wrong_published_metric_label_fails(self):
        with self.assertRaisesRegex(ValueError,"published aggregate label changed"):
            process_archive(build_fixture("wrong_label"),enforce_source_hash=False)

    def test_aggregate_exceeding_total_fails(self):
        with self.assertRaisesRegex(ValueError,"aggregate arithmetic sanity"):
            process_archive(build_fixture("capital_gt_total"),enforce_source_hash=False)

    def test_unknown_numeric_value_fails(self):
        with self.assertRaisesRegex(ValueError,"missing or negative published aggregate"):
            process_archive(build_fixture("missing_numeric"),enforce_source_hash=False)

    def test_duplicate_key_fails(self):
        with self.assertRaisesRegex(ValueError,"duplicate official aggregate"):
            process_archive(build_fixture("duplicate"),enforce_source_hash=False)


if __name__=="__main__":
    unittest.main()
