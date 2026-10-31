#!/usr/bin/env python3
"""Source-verified 2025 ACS B01001 district age estimates; keyless Census FTP.

Run: python scripts/ingest_acs_2025_house_age.py
No respondent-level data, private API keys, or external dependencies.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ('https://www2.census.gov/programs-surveys/acs/summary_file/2025/'
          'table-based-SF/data/1YRData/acsdt1y2025-b01001.dat')
CROSSWALK = ROOT / 'data/research/political-authenticity/house-district-crosswalk-119.json'
OUTPUT = ROOT / 'data/research/political-authenticity/acs-2025-house-district-age.json'
PREFIX = '5001900US'  # Census Summary File GEO_ID: 500=CD, 119th Congress
GEO_RE = re.compile(r'^5001900US([0-9]{4})$')
YOUNG = (11, 12, 35, 36)  # B01001: male/female 25-29 and 30-34
ADULT = (*range(11, 26), *range(35, 50))  # both sexes 25+
ALL_AGE = (*range(3, 26), *range(27, 50))


def value(row: dict[str, str], field: str) -> int:
    raw = row.get(field)
    if raw is None or not re.fullmatch(r'\d+', raw):
        raise ValueError(f'Missing/suppressed/invalid Census cell {field}: {raw!r}')
    return int(raw)


def summed(row: dict[str, str], indexes: tuple[int, ...], kind: str) -> int | float:
    numbers = [value(row, f'B01001_{kind}{i:03d}') for i in indexes]
    # Census 90% MOEs of sums are approximated via RSS; covariance unavailable.
    return math.sqrt(sum(n*n for n in numbers)) if kind == 'M' else sum(numbers)


def build(raw: bytes, crosswalk: dict, retrieved_at: str) -> dict:
    if crosswalk.get('schema') != 'power-atlas.political-authenticity.house-district-crosswalk.v1' or crosswalk.get('boundaryCongress') != 119:
        raise ValueError('Expected the 119th congressional crosswalk')
    seats = crosswalk['records']
    if len(seats) != 435 or len({r['censusStateDistrictKey'] for r in seats}) != 435:
        raise ValueError('Expected 435 unique voting district keys')
    expected = {r['censusStateDistrictKey']: r for r in seats}
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter='|')
    required = {'GEO_ID', 'B01001_E001', 'B01001_E002', 'B01001_E026'}
    required.update(f'B01001_{kind}{i:03d}' for kind in ('E', 'M') for i in ADULT)
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError('2025 B01001 official estimate/MOE columns absent')
    found = {}
    for row in reader:
        geo = row.get('GEO_ID', '')
        match = GEO_RE.fullmatch(geo)
        if not match or match.group(1) not in expected:
            continue  # other Census geography types, DC/delegate geographies
        key = match.group(1)
        if key in found:
            raise ValueError(f'Duplicate congressional GEO_ID: {geo}')
        total = value(row, 'B01001_E001')
        if total <= 0 or value(row, 'B01001_E002') + value(row, 'B01001_E026') != total:
            raise ValueError(f'B01001 male+female != total: {geo}')
        if summed(row, ALL_AGE, 'E') != total:
            raise ValueError(f'B01001 age-bin sum != total: {geo}')
        adult = int(summed(row, ADULT, 'E'))
        young = int(summed(row, YOUNG, 'E'))
        if not (0 <= young <= adult <= total):
            raise ValueError(f'Impossible age distribution: {geo}')
        seat = expected[key]
        found[key] = {
            'seatKey': seat['seatKey'], 'censusStateDistrictKey': key, 'GEO_ID': geo,
            'memberBioguideIdAtSnapshot': seat['memberBioguideId'],
            'populationAllAgesEstimate': total,
            'populationAge25plusEstimate': adult,
            'populationAge25plusMOE90Approx': round(summed(row, ADULT, 'M'), 2),
            'populationAge25to34Estimate': young,
            'populationAge25to34MOE90Approx': round(summed(row, YOUNG, 'M'), 2),
            'age25to34ShareOf25plusDescriptive': round(young/adult, 6) if adult else None,
        }
    missing = sorted(set(expected) - set(found))
    if missing:
        raise ValueError(f'Missing {len(missing)} congressional district estimates; first: {missing[:8]}')
    records = [found[r['censusStateDistrictKey']] for r in seats]
    return {
        'schema': 'power-atlas.political-authenticity.acs2025-district-age.v1',
        'status': 'observed_official_acs2025_119th_district_aggregates_not_causal',
        'surveyYear': 2025, 'acsReleaseDate': '2026-10-29',
        'retrievedAtUTC': retrieved_at, 'sourceTable': 'B01001',
        'sourceUrl': SOURCE, 'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'sourceLicense': 'United States federal government public-domain statistical data',
        'geography': '119th congressional districts (2025 ACS 1-year, GEO_ID prefix 5001900US)',
        'memberSnapshotDate': crosswalk['memberSnapshotDate'],
        'sourceCrosswalkSha256': hashlib.sha256(json.dumps(crosswalk, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'districtCount': len(records), 'districtMissingCount': len(missing),
        'moeMethod': 'RSS of published B01001 age-bin 90% MOEs; approximation without covariance, not an official aggregate MOE',
        'cautions': [
            'Resident population, not citizenship-eligible voter or candidate universe',
            'Age-band sum MOEs are approximations; covariance unavailable',
            'Age shares have no valid directly estimated MOE; do not test significance from shares alone',
            'District 2025 survey estimates vs member roster snapshot at a different date',
            'No member-level wealth, ideology, survey responses, or causal effects inferred',
            'B01001 total population MOE uses Census suppression sentinel; not used as zero',
        ],
        'records': records,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source-file', type=Path, help='Optional local copy of official B01001 .dat')
    p.add_argument('--crosswalk', type=Path, default=CROSSWALK)
    p.add_argument('--output', type=Path, default=OUTPUT)
    args = p.parse_args()
    crosswalk = json.loads(args.crosswalk.read_text(encoding='utf-8'))
    if args.source_file:
        raw = args.source_file.read_bytes()
    else:
        with urlopen(SOURCE, timeout=75) as response:
            raw = response.read(15_000_001)
        if len(raw) > 15_000_000:
            raise ValueError('Official B01001 file unexpectedly large')
    doc = build(raw, crosswalk, dt.datetime.now(dt.timezone.utc).isoformat())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
    print(json.dumps({'districts': doc['districtCount'], 'missing': doc['districtMissingCount'],
                      'sourceSha256': doc['sourceSha256'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
