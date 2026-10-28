from pathlib import Path
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
records = {}
relationships = {}

def match_key(row):
    title = re.sub(r',\s*(?:TX|GA|TN|LA|FL|NY|NC|SC)\s*$', '', row['title'], flags=re.I)
    normalized = re.sub(r'[^a-z0-9]+', ' ', title.casefold()).strip()
    # Candidate duplicate only: year must also match; never infer two cases are identical from title alone.
    year = str(row.get('date', ''))[:4]
    return normalized, year

for file in sorted((ROOT / 'data/batches').glob('*.json')):
    doc = json.loads(file.read_text(encoding='utf-8'))
    for row in doc['records']:
        if not row.get('id') or not str(row.get('source', '')).startswith('https://'):
            raise ValueError(f'Invalid record in {file}')
        compact = {k: row[k] for k in (
            'id', 'title', 'state', 'date', 'asOf', 'source', 'status',
            'reviewStatus', 'claimScope'
        ) if k in row}
        if not compact.get('status') and not compact.get('reviewStatus'):
            compact['status'] = doc.get('status') or doc.get('publicationStatus') or 'source_indexed_unreviewed'
        if compact.get('date'):
            compact['datePrecision'] = 'year' if re.fullmatch(r'[0-9]{4}', str(compact['date'])) else 'day'
        compact['source_sha256'] = hashlib.sha256(compact['source'].encode()).hexdigest()[:16]
        if compact['id'] in records and records[compact['id']] != compact:
            raise ValueError(f'Conflicting record ID: {compact["id"]}')
        records[compact['id']] = compact
        for link in row.get('candidateLinks', []):
            cid = link.get('candidateId', '')
            if not re.fullmatch(r'[A-Z][0-9]{8}', cid):
                continue
            edge_id = 'fec-edge-' + hashlib.sha256((compact['id'] + ':' + cid).encode()).hexdigest()[:16]
            relationships[edge_id] = {
                'id': edge_id,
                'from': compact['id'],
                'to': 'fec-candidate-' + cid,
                'type': 'reported_candidate_committee_association',
                'source': 'https://api.open.fec.gov/v1/committee/' + compact['id'].removeprefix('fec-') + '/candidates/',
                'reviewStatus': 'official_fec_link_unreviewed'
            }

# Flag likely duplicates for review instead of deleting source-specific records.
seen = {}
for item in sorted(records.values(), key=lambda x: (0 if x['id'].startswith('doj-') and not x['id'].startswith('doj-index') else 1, x['id'])):
    key = match_key(item)
    if key[1] and key in seen:
        item['possibleDuplicateOf'] = seen[key]
    else:
        seen[key] = item['id']

output = {
    'schema': 'power-atlas.compact.v1',
    'publicationStatus': 'review_required',
    'records': sorted(records.values(), key=lambda row: row['id'])
}
path = ROOT / 'data/research.json'
content = json.dumps(output, indent=2, ensure_ascii=False) + '\n'
if not path.exists() or path.read_text(encoding='utf-8') != content:
    path.write_text(content, encoding='utf-8')
edges_path = ROOT / 'data/relationships.json'
edges = {'schema': 'power-atlas.relationships.v1', 'publicationStatus': 'review_required',
         'relationships': sorted(relationships.values(), key=lambda row: row['id'])}
edge_content = json.dumps(edges, indent=2, ensure_ascii=False) + '\n'
if not edges_path.exists() or edges_path.read_text(encoding='utf-8') != edge_content:
    edges_path.write_text(edge_content, encoding='utf-8')
print(f'Validated {len(records)} source-specific records and {len(relationships)} FEC links')

def read_finance(filename):
    file = ROOT / 'data/finance' / filename
    if not file.exists():
        return []
    doc = json.loads(file.read_text(encoding='utf-8'))
    rows = doc.get('records', [])
    if not isinstance(rows, list):
        raise ValueError('Expected finance records array: ' + filename)
    return rows

totals = read_finance('fec-totals.json')
payments = read_finance('fec-disbursements.json')
state_file = ROOT / 'data/geography/states.json'
states = json.loads(state_file.read_text(encoding='utf-8'))['states'] if state_file.exists() else []
uncovered = [
    'state_campaign_finance', 'state_roll_calls', 'district_geospatial',
    'litigation_dockets', 'judicial_selection', 'national_election_returns'
]
feed = {
    'schema': 'power-atlas.frontend.v1',
    'publicationStatus': 'review_required',
    'records': output['records'],
    'relationships': edges['relationships'],
    'states': states,
    'finance': {
        'committeeTotals': totals,
        'committeePayments': payments
    },
    'coverage': {
        'sourceIndexedRecords': len(records),
        'relationshipRecords': len(relationships),
        'committeeTotalRows': len(totals),
        'paymentRows': len(payments),
        'stateSourceReferences': len(states),
        'uncovered': uncovered,
        'warning': 'Index counts are not reviewed unique-case or influence counts'
    }
}
feed_path = ROOT / 'data/app-feed.json'
feed_content = json.dumps(feed, ensure_ascii=False, indent=2) + '\n'
if not feed_path.exists() or feed_path.read_text(encoding='utf-8') != feed_content:
    feed_path.write_text(feed_content, encoding='utf-8')
print('Frontend feed: ' + str(len(feed_content.encode('utf-8'))) + ' bytes')

