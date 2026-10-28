"""Index current US Congress members with stable Bioguide/FEC crosswalks.
Source: unitedstates/congress-legislators (CC0-1.0). Public office identity
metadata only, no private addresses, contact details or social accounts.
"""
import datetime
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/people/congress-members.json'
SOURCE='https://unitedstates.github.io/congress-legislators/legislators-current.json'
REPO='https://github.com/unitedstates/congress-legislators'
TODAY=datetime.date.today()
MAX_BYTES=2_000_000

def fetch():
    with urlopen(Request(SOURCE,headers={'User-Agent':'PowerAtlasResearch/1.0','Accept':'application/json'}),timeout=30) as response:
        if response.status!=200:
            raise RuntimeError('Public congressional roster source HTTP error')
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise RuntimeError('Roster exceeded bounded download limit')
    data=json.loads(raw)
    if not isinstance(data,list) or not 500<=len(data)<=650:
        raise RuntimeError('Unexpected roster size; existing data preserved')
    return data

def current_term(terms):
    candidates=[]
    for term in terms:
        if not isinstance(term,dict):
            continue
        try:
            start=datetime.date.fromisoformat(term['start'])
            end=datetime.date.fromisoformat(term['end'])
        except (KeyError,ValueError,TypeError):
            continue
        if start<=TODAY<end and term.get('type') in ('rep','sen'):
            candidates.append((start,term))
    if not candidates:
        return None
    return max(candidates,key=lambda row:row[0])[1]

def collect():
    data=fetch()
    people={}
    for item in data:
        if not isinstance(item,dict):
            continue
        ids=item.get('id') or {}
        bio=str(ids.get('bioguide') or '').upper()
        if not re.fullmatch(r'[A-Z][0-9]{6}',bio):
            continue
        term=current_term(item.get('terms') or [])
        if not term:
            continue
        names=item.get('name') or {}
        display=' '.join(str(names.get(k) or '').strip() for k in ('first','last')).strip()
        state=str(term.get('state') or '').upper()
        if not display or not re.fullmatch('[A-Z]{2}',state):
            continue
        chamber='House' if term.get('type')=='rep' else 'Senate'
        party=str(term.get('party') or 'Unknown')
        result={
            'id':'bioguide-'+bio,'name':display[:100],'bioguideId':bio,
            'chamber':chamber,'state':state,'party':party[:48],
            'termStart':term['start'],'termEnd':term['end'],
            'source':'https://bioguide.congress.gov/search/bio/'+bio,
            'sourceRegistry':SOURCE,'sourceLicense':'CC0-1.0',
            'reviewStatus':'public_legislator_registry_unreviewed',
            'claimScope':'Current congressional service only; no presumed redistricting involvement'
        }
        if chamber=='House':
            district=term.get('district')
            if isinstance(district,int) and 0<=district<=99:
                result['district']=district
        fec_ids=ids.get('fec') or []
        if isinstance(fec_ids,list):
            valid=sorted(set(x for x in fec_ids if isinstance(x,str) and re.fullmatch(r'[HS][0-9]{8}',x)))
            if valid:
                result['fecCandidateIds']=valid[:6]
        people[result['id']]=result
    house=sum(p['chamber']=='House' for p in people.values())
    senate=sum(p['chamber']=='Senate' for p in people.values())
    if not 380<=house<=440 or not 85<=senate<=105:
        raise RuntimeError(f'Unexpected live roster counts House={house} Senate={senate}; preserving prior data')
    doc={
        'schema':'power-atlas.congress-members.v1','sourceCatalog':REPO,
        'license':'CC0-1.0','publicationStatus':'requires_official_bioguide_crosscheck',
        'asOfDate':TODAY.isoformat(),
        'coverage':{'houseMembers':house,'senators':senate},
        'records':sorted(people.values(),key=lambda r:r['id'])
    }
    body=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
    if len(body.encode())>440_000:
        raise RuntimeError('Unexpectedly large congressional roster export')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=body:
        OUT.write_text(body,encoding='utf-8')
    print('Congress members indexed:',len(people),'House:',house,'Senate:',senate)

if __name__=='__main__':
    collect()
