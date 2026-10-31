"""Offline positive and negative tests for official ACS B01001 district-age ingestion."""
import csv
import io
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ingest_acs_2025_house_age import build, PREFIX


def fixture():
    # Synthetic keys exercise parser validation, NOT observed district data.
    seats = [{'seatKey':f'X-{i:03d}', 'censusStateDistrictKey':f'{i:04d}',
              'memberBioguideId': None} for i in range(435)]
    crosswalk = {'schema':'power-atlas.political-authenticity.house-district-crosswalk.v1',
                 'boundaryCongress':119,'memberSnapshotDate':'2026-10-30','records':seats}
    fields = ['GEO_ID'] + [f'B01001_{k}{i:03d}' for i in range(1,50) for k in ('E','M')]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, delimiter='|', lineterminator='\n')
    writer.writeheader()
    for seat in seats:
        row = {f'B01001_E{i:03d}':10 for i in range(1,50)}
        row.update({f'B01001_M{i:03d}':2 for i in range(1,50)})
        row['GEO_ID'] = PREFIX + seat['censusStateDistrictKey']
        row['B01001_E002'] = 230
        row['B01001_E026'] = 230
        row['B01001_E001'] = 460
        writer.writerow(row)
    return out.getvalue().encode(), crosswalk


class TestCensus2025(unittest.TestCase):
    def test_435_districts_and_age_moe(self):
        raw,crosswalk = fixture()
        d=build(raw,crosswalk,'2026-10-31T12:00:00+00:00')
        self.assertEqual(d['districtCount'],435)
        self.assertEqual(d['districtMissingCount'],0)
        self.assertEqual(d['records'][0]['populationAge25plusEstimate'],300)
        self.assertEqual(d['records'][0]['populationAge25to34Estimate'],40)
        self.assertEqual(d['records'][0]['populationAge25to34MOE90Approx'],4)
    def test_missing_district_fails_closed(self):
        raw,crosswalk=fixture(); rows=raw.decode().splitlines()
        with self.assertRaisesRegex(ValueError,'Missing 1 congressional'):
            build(('\n'.join(rows[:-1])+'\n').encode(),crosswalk,'now')
    def test_duplicate_geo_fails(self):
        raw,crosswalk=fixture(); rows=raw.decode().splitlines()
        with self.assertRaisesRegex(ValueError,'Duplicate congressional'):
            build(('\n'.join(rows+[rows[1]])+'\n').encode(),crosswalk,'now')
    def test_suppressed_cells_not_zero(self):
        raw,crosswalk=fixture(); rows=raw.decode().splitlines()
        fields=rows[0].split('|'); idx=fields.index('B01001_M011')
        vals=rows[1].split('|'); vals[idx]='-555555555'; rows[1]='|'.join(vals)
        with self.assertRaisesRegex(ValueError,'suppressed'):
            build(('\n'.join(rows)+'\n').encode(),crosswalk,'now')
    def test_wrong_congress_fails(self):
        raw,crosswalk=fixture(); crosswalk['boundaryCongress']=118
        with self.assertRaisesRegex(ValueError,'119th'):
            build(raw,crosswalk,'now')
    def test_wrong_prefix_fails_missing(self):
        raw,crosswalk=fixture()
        with self.assertRaisesRegex(ValueError,'Missing 435'):
            build(raw.replace(b'5001900US',b'5001800US'),crosswalk,'now')
    def test_age_inconsistency_fails(self):
        raw,crosswalk=fixture(); rows=raw.decode().splitlines()
        fields=rows[0].split('|'); idx=fields.index('B01001_E011')
        vals=rows[1].split('|'); vals[idx]='11'; rows[1]='|'.join(vals)
        with self.assertRaisesRegex(ValueError,'age-bin sum'):
            build(('\n'.join(rows)+'\n').encode(),crosswalk,'now')


if __name__=='__main__':
    unittest.main()
