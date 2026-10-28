"""Bounded FEC committee discovery, with compact identifiers only and no donor data."""
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/batches/fec-committees.json'
API = 'https://api.open.fec.gov/v1/committees/'
TERMS = ('redistricting', 'republican state leadership', 'democratic legislative campaign')

def collect():
    records = {}
    for term in TERMS:
        query = urlencode({'api_key':'DEMO_KEY','q':term,'per_page':20,'page':1})
        req = Request(API+'?'+query,headers={'User-Agent':'PowerAtlasResearch/1.0'})
        with urlopen(req,timeout=20) as response:
            if response.status != 200:
                raise RuntimeError('FEC API unavailable; old data preserved')
            raw = response.read(250001)
            if len(raw) > 250000:
                raise RuntimeError('FEC response exceeded 250 KB')
        payload = json.loads(raw)
        if not isinstance(payload.get('results'),list):
            raise RuntimeError('Unexpected FEC response')
        for item in payload['results']:
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
    data={'batch':'fec-committee-discovery-v1','records':sorted(records.values(),key=lambda x:x['id'])}
    new=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
    if not DEST.exists() or DEST.read_text(encoding='utf-8')!=new:
        DEST.parent.mkdir(parents=True,exist_ok=True)
        DEST.write_text(new,encoding='utf-8')
    print('FEC committee candidate matches:',len(records))
if __name__=='__main__':
    collect()
