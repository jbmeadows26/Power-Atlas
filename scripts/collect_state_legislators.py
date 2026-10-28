"""Index serving US state legislators from Open States' public CC0 CSV feeds.

One source per state, bounded parallelism and downloads, no proprietary API keys.
Store only office identity, district, party, stable person ID and source pointers.
No personal addresses, birth dates, emails, biographies or social accounts.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import csv
import datetime
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/people/state-legislators.json'
SOURCE='https://data.openstates.org/people/current/'
SOURCE_REPO='https://github.com/openstates/people'
STATES='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR'.split()
MAX_DOWNLOAD=400000
MAX_JSON=2_300_000

class AccessBlocked(Exception):
    pass

def fetch_state(abbr):
    url=SOURCE+abbr+'.csv'
    request=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public records indexing',
                                 'Accept':'text/csv'})
    try:
        with urlopen(request,timeout=30) as response:
            if response.status!=200:
                raise RuntimeError(f'Unexpected Open States HTTP {response.status}')
            raw=response.read(MAX_DOWNLOAD+1)
            if len(raw)>MAX_DOWNLOAD:
                raise RuntimeError('Unusually large state CSV: '+abbr)
    except HTTPError as exc:
        if exc.code in (401,403,429):
            raise AccessBlocked(f'Static Open States CSV access/rate restriction HTTP {exc.code}') from exc
        raise
    text=raw.decode('utf-8-sig')
    reader=csv.DictReader(StringIO(text))
    expected={'id','name','current_party','current_district','current_chamber'}
    if not expected.issubset(reader.fieldnames or []):
        raise RuntimeError('Unexpected Open States CSV schema: '+abbr)
    rows={}
    for row in reader:
        pid=str(row.get('id') or '').strip()
        name=str(row.get('name') or '').strip()
        district=str(row.get('current_district') or '').strip()
        chamber=str(row.get('current_chamber') or '').strip().lower()
        party=str(row.get('current_party') or '').strip()
        if not re.fullmatch(r'ocd-person/[a-zA-Z0-9-]{20,50}',pid):
            continue
        if not name or chamber not in ('upper','lower') or not district or not party:
            continue
        row_id='state-person-'+pid.split('/')[-1]
        item={
            'id':row_id,'ocdPersonId':pid,'name':name[:110],'state':abbr,
            'chamber':chamber,'district':district[:60],'party':party[:55],
            'source':url,'sourceCatalog':SOURCE_REPO,
            'sourceLicense':'CC0-1.0',
            'reviewStatus':'curated_state_legislator_unreviewed',
            'claimScope':'Legislative office identification only; no redistricting vote or improper influence established'
        }
        rows[row_id]=item
    if not rows:
        raise RuntimeError('No valid state legislators returned for '+abbr)
    return abbr,rows

def collect():
    old=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    existing={row['id']:row for row in old.get('records',[])}
    by_state={}
    for row in existing.values():
        by_state.setdefault(row['state'],{})[row['id']]=row
    succeeded,failed=[],{}
    blocked=None
    with ThreadPoolExecutor(max_workers=4) as pool:
        future_map={pool.submit(fetch_state,abbr):abbr for abbr in STATES}
        for future in as_completed(future_map):
            abbr=future_map[future]
            try:
                state,items=future.result()
            except AccessBlocked as exc:
                blocked=str(exc)
                failed[abbr]=type(exc).__name__
                continue
            except (HTTPError,URLError,TimeoutError,UnicodeError,ValueError,RuntimeError,OSError) as exc:
                failed[abbr]=type(exc).__name__
                continue
            by_state[state]=items
            succeeded.append(state)
    if blocked:
        raise RuntimeError(blocked+'; keeping existing records')
    if not succeeded:
        raise RuntimeError('No Open States files fetched; retaining last good corpus')
    if not existing and len(succeeded)<40:
        raise RuntimeError('Initial national index has fewer than 40 successful jurisdictions; retry later')
    output=[]
    for state in sorted(by_state):
        output.extend(by_state[state].values())
    if not 4000<=len(output)<=10000:
        raise RuntimeError('Unexpected national state-legislator roster size '+str(len(output)))
    data={
        'schema':'power-atlas.state-legislators.v1',
        'publicationStatus':'current_roster_requires_state_source_crosscheck',
        'license':'CC0-1.0',
        'sourceCatalog':SOURCE_REPO,
        'asOfDate':datetime.date.today().isoformat(),
        'coverage':{'jurisdictionsFetched':len(succeeded),'jurisdictionsTotal':len(STATES),
                    'jurisdictionsFailed':sorted(failed),
                    'totalPeopleIndexed':len(output)},
        'records':sorted(output,key=lambda r:r['id'])
    }
    content=json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(content.encode())>MAX_JSON:
        raise RuntimeError('Compact state-legislator dataset exceeds '+str(MAX_JSON)+' bytes')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=content:
        OUT.write_text(content,encoding='utf-8')
    print('State legislators:',len(output),'jurisdictions refreshed:',len(succeeded),'failed:',failed)

if __name__=='__main__':
    collect()
