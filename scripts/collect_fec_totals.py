"""Free, bounded FEC cycle summaries. Never store individual-donor data."""
from __future__ import annotations
import json
import math
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/batches/fec-committees.json'
OUTPUT = ROOT / 'data/finance/fec-totals.json'
API = 'https://api.open.fec.gov/v1/committee/'
CYCLES = (2026, 2024)
KEY = os.environ.get('FEC_API_KEY') or 'DEMO_KEY'
MAX_COMMITTEES = 2 if KEY == 'DEMO_KEY' else 7
FIELDS = ('receipts', 'disbursements', 'cash_on_hand_end_period', 'debts_owed_by_committee')
MAX_BYTES = 160000

def read_api(committee_id: str, cycle: int):
    params = urlencode({'api_key': KEY, 'cycle': cycle, 'per_page': 20})
    request = Request(API + committee_id + '/totals/?' + params, headers={
        'User-Agent': 'PowerAtlas/1.0 (public-interest committee finance indexing)',
        'Accept': 'application/json'})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError('FEC returned non-200 response')
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError('Oversized FEC totals response')
    doc = json.loads(payload)
    if not isinstance(doc.get('results'), list):
        raise ValueError('Unexpected FEC totals schema')
    return doc['results']

def normalize(item: dict, committee_id: str, cycle: int):
    if str(item.get('committee_id', '')) != committee_id or item.get('cycle') != cycle:
        return None
    record = {
        'id': f'fec-total-{committee_id}-{cycle}', 'committeeId': committee_id,
        'cycle': cycle,
        'source': f'https://www.fec.gov/data/committee/{committee_id}/?cycle={cycle}',
        'reviewStatus': 'official_cycle_summary_unreviewed',
        'meaning': 'Aggregate filed totals; not proof of redistricting influence'
    }
    for key in FIELDS:
        amount = item.get(key)
        if isinstance(amount, (int, float)) and not isinstance(amount, bool) and math.isfinite(amount):
            record[key] = round(float(amount), 2)
    return record if any(key in record for key in FIELDS) else None

def collect():
    if not INPUT.exists():
        raise FileNotFoundError('FEC committee discovery is missing')
    source = json.loads(INPUT.read_text(encoding='utf-8'))['records']
    committees = [row['id'][4:] for row in source if
                  re.fullmatch(r'fec-C[0-9]{8}', row.get('id', ''))]
    # Disclosed federal PACs with previously observed reporting rows first.
    preferred = ('C00630707', 'C00747279')
    committees = sorted(committees, key=lambda cid: (cid not in preferred, cid))[:MAX_COMMITTEES]
    old = json.loads(OUTPUT.read_text(encoding='utf-8'))['records'] if OUTPUT.exists() else []
    indexed = {item['id']: item for item in old}
    successes, missing, errors = 0, 0, []
    for committee_id in committees:
        for cycle in CYCLES:
            try:
                entries = read_api(committee_id, cycle)
            except (HTTPError, URLError, ValueError, OSError, RuntimeError) as exc:
                code = getattr(exc, 'code', None)
                errors.append((committee_id, cycle, 'HTTP '+str(code) if code else type(exc).__name__))
                if code in (401,403,429):
                    raise RuntimeError('FEC access or rate restriction; wait for permitted reset: HTTP '+str(code)) from exc
                continue
            successes += 1
            matched = False
            for entry in entries:
                record = normalize(entry, committee_id, cycle)
                if record:
                    indexed[record['id']] = record
                    matched = True
            if not matched:
                missing += 1
    if not successes:
        raise RuntimeError('All FEC requests failed; keeping prior data. Errors: ' + str(errors)[:250])
    document = {
        'schema': 'power-atlas.fec.cycle-totals.v1',
        'publicationStatus': 'requires_source_review',
        'records': sorted(indexed.values(), key=lambda x: x['id'])
    }
    output = json.dumps(document, ensure_ascii=False, indent=2) + '\n'
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != output:
        OUTPUT.write_text(output, encoding='utf-8')
    print('FEC totals records:', len(indexed), 'successful API queries:', successes,
          'queries with no summary:', missing, 'query errors:', len(errors))
    if errors:
        print('Partial failures:', errors)

if __name__ == '__main__':
    collect()
