from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[1]
records = {}
for file in sorted((ROOT / 'data/batches').glob('*.json')):
    doc = json.loads(file.read_text(encoding='utf-8'))
    for row in doc['records']:
        if not row.get('id') or not str(row.get('source', '')).startswith('https://'):
            raise ValueError(f'Invalid record in {file}')
        compact = {k: row[k] for k in ('id', 'title', 'state', 'date', 'source', 'status', 'reviewStatus', 'claimScope') if k in row}
        compact['source_sha256'] = hashlib.sha256(compact['source'].encode()).hexdigest()[:16]
        if compact['id'] in records and records[compact['id']] != compact:
            raise ValueError(f'Conflicting record ID: {compact["id"]}')
        records[compact['id']] = compact

output = {
    'schema': 'power-atlas.compact.v1',
    'publicationStatus': 'review_required',
    'records': sorted(records.values(), key=lambda row: row['id'])
}
path = ROOT / 'data/research.json'
content = json.dumps(output, indent=2, ensure_ascii=False) + '\n'
if not path.exists() or path.read_text(encoding='utf-8') != content:
    path.write_text(content, encoding='utf-8')
print(f'Validated {len(records)} unique compact records; {len(content.encode())} bytes')
