"""Bounded FEC committee discovery, with compact identifiers only and no donor data."""
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path
import os
import time
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/batches/fec-committees.json'
API = 'https://api.open.fec.gov/v1/committees/'
TERMS = ('redistricting', 'republican state leadership', 'democratic legislative campaign')
KEY = os.environ.get('FEC_API_KEY', 'DEMO_KEY')

def api_get(url):
    req = Request(url, headers={'User-Agent':'PowerAtlasResearch/1.0'})
    with urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError('FEC API unavailable')
        raw = response.read(250001)
        if len(raw) > 250000:
            raise RuntimeError('FEC response exceeded 250 KB')
    payload = json.loads(raw)
    if not isinstance(payload.get('results'),list):
        raise RuntimeError('Unexpected FEC response')
    return payload['results']

def collect():
    records = {}
    for term in TERMS:
        query = urlencode({'api_key':KEY,'q':term,'per_page':20,'page':1})
        for item in api_get(API+'?'+query):
            cid = item.get('committee_id')
            name = item.get('name')
            if not cid or not name:
                continue
            records['fec-'+cid] = {
                'id':'fec-'+cid,
                'title':name[:150],
                'state':item.get('state') or '',
                'source':'https://www.fec.gov/data/committee/'+cid+'/',
                'status':'official_fec_committee_match_unreviewed',
                'claimScope':'Name-search candidate; not evidence of redistricting involvement'
            }
    if not records:
        raise RuntimeError('No committee matches returned; old data preserved')
    # Only exact committee identifiers can establish a formal reported relationship.
    # Limit to 12 committee lookups per run (plus three name searches) to conserve quotas.
    for row in list(records.values())[:12]:
        cid = row['id'].removeprefix('fec-')
        url = API.rstrip('/') + '/' + cid + '/candidates/?' + urlencode({'api_key':KEY,'per_page':10})
        try:
            candidates = api_get(url)
        except Exception as exc:
            print('Candidate linkage skipped for', cid, type(exc).__name__)
            continue
        links = []
        for candidate in candidates:
            candidate_id = candidate.get('candidate_id')
            if candidate_id:
                links.append({
                    'candidateId':candidate_id,
                    'candidateName':str(candidate.get('name') or '')[:120],
                    'relationship':'reported_candidate_committee_association',
                    'evidenceUrl':'https://www.fec.gov/data/candidate/'+candidate_id+'/'
                })
        if links:
            row['candidateLinks'] = links
        time.sleep(0.15)
    data={'batch':'fec-committee-discovery-v1','records':sorted(records.values(),key=lambda x:x['id'])}
    new=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
    if not DEST.exists() or DEST.read_text(encoding='utf-8')!=new:
        DEST.parent.mkdir(parents=True,exist_ok=True)
        DEST.write_text(new,encoding='utf-8')
    print('FEC committee candidate matches:',len(records))
if __name__=='__main__':
    collect()
