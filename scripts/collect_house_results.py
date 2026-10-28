"""Ingest compact certified-source US House party vote summaries.

Election Data API serves MIT Election Data and Science Lab's CC0 dataset.
Fetch only year partitions; never retain raw ballots, candidate PII, or CSV archives.
These are election outcomes, *not* standalone gerrymandering measurements.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen
import datetime
import json
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/elections/house-districts.json'
API = 'https://api.electiondata.dev/v1/house-results'
YEARS = (2024, 2022, 2020, 2018, 2016, 2014, 2012, 2010)
MAX_DOWNLOAD = 8_000_000
MAX_ROWS = 20_000

def source_year(year):
    url = f'{API}/table/{year}.json'
    req = Request(url, headers={'User-Agent':'PowerAtlasPublicResearch/1.0',
                                'Accept':'application/json'})
    with urlopen(req, timeout=35) as resp:
        if resp.status != 200:
            raise RuntimeError(f'House data HTTP {resp.status}: {year}')
        raw = resp.read(MAX_DOWNLOAD + 1)
        if len(raw) > MAX_DOWNLOAD:
            raise RuntimeError(f'House source exceeded download bound: {year}')
        version = resp.headers.get('X-Data-Version', '')
    body = json.loads(raw)
    rows = body.get('rows')
    if not isinstance(rows, list) or len(rows) > MAX_ROWS or len(rows) < 300:
        raise RuntimeError(f'Unexpected US House partition row count: {year}')
    license_name = str(body.get('meta', {}).get('license', 'CC0 1.0'))
    if license_name and 'CC0' not in license_name.upper().replace('-', ''):
        raise RuntimeError(f'Unrecognized dataset license: {license_name}')
    return rows, version, url

def calc(rows, year, version, source_url):
    # Candidate-total vote rows are repeated by ballot line/mode; use one
    # maximum per candidate. Never sum candidate_total_votes across rows.
    candidates = defaultdict(dict)
    for item in rows:
        try:
            if int(item.get('year', -1)) != year:
                continue
            if str(item.get('stage','')).lower() not in ('gen', 'general'):
                continue
            if item.get('special') in (True, 'true', 'True', 1):
                continue
            state = str(item.get('state_po') or '').upper()
            district = int(item.get('district'))
            if len(state) != 2 or not (0 <= district <= 99):
                continue
            candidate = str(item.get('candidate') or '').strip().upper()
            party = str(item.get('party') or '').strip().upper()
            if not candidate or not party:
                continue
            total = item.get('candidate_total_votes')
            mode = str(item.get('mode') or 'TOTAL').upper().strip()
            if total is None:
                if mode not in ('TOTAL',''):
                    continue
                total = item.get('candidatevotes')
            if total is None:
                continue
            votes = int(total)
            if votes < 0 or not math.isfinite(votes):
                continue
        except (TypeError,ValueError,OverflowError):
            continue
        key = (state, district)
        old = candidates[key].get((candidate,party),0)
        candidates[key][(candidate,party)] = max(old,votes)
    output = []
    for (state,district), options in sorted(candidates.items()):
        dv = sum(v for (name,p),v in options.items() if p in ('DEMOCRAT','DEMOCRATIC'))
        rv = sum(v for (name,p),v in options.items() if p in ('REPUBLICAN',))
        output.append({
            'id':f'house-{year}-{state}-{district:02d}',
            'year':year,'state':state,'district':district,
            'democraticVotes':dv,'republicanVotes':rv,
            'twoPartyVotes':dv+rv,
            'source':source_url,
            'datasetVersion':version or 'unversioned_current',
            'reviewStatus':'derived_from_CC0_MEDSL_candidate_totals_unreviewed',
            'metricMeaning':'Two-party candidate vote totals only; not partisan bias or map causality'
        })
    if not 330 <= len(output) <= 445:
        raise RuntimeError(f'Unexpected number of district records for {year}: {len(output)}')
    if sum(r['twoPartyVotes']>0 for r in output)<320:
        raise RuntimeError(f'Too few usable two-party district vote totals: {year}')
    return output

def main():
    # A failed year must not erase the previous corpus.
    old = json.loads(OUT.read_text(encoding='utf-8'))['records'] if OUT.exists() else []
    prior = {x['id']:x for x in old}
    successes = []
    for year in YEARS:
        rows,version,url = source_year(year)
        results = calc(rows,year,version,url)
        for item in results:
            prior[item['id']] = item
        successes.append({'year':year,'districts':len(results),'version':version})
        print('Processed year',year,'districts',len(results))
    new_doc = {
        'schema':'power-atlas.house-district-v1',
        'sourceDataset':'MIT Election Data and Science Lab U.S. House 1976-2024',
        'sourceLicense':'CC0 1.0',
        'sourceCatalog':'https://electiondata.dev/datasets/',
        'sourceProvider':'Election Data',
        'publicationStatus':'derived_requires_validation',
        'validation':'Two-party aggregates exclude independents, third parties and special elections. Not a gerrymandering score.',
        'years':successes,
        'records':sorted(prior.values(),key=lambda r:r['id'])
    }
    output=json.dumps(new_doc,indent=2,ensure_ascii=False)+'\n'
    if len(output.encode())>3_000_000:
        raise RuntimeError('Output exceeded minimal storage cap')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=output:
        OUT.write_text(output,encoding='utf-8')
    print('House district-year rows',len(prior),'stored bytes',len(output.encode()))

if __name__=='__main__':
    main()
