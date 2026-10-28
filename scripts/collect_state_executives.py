"""Index public serving governors and state executive posts from CC0 Open States.
Names, parties, roles, source links only; no personal contact fields.
"""
from pathlib import Path
import datetime
import json
import os
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=Path(os.environ.get('OPENSTATES_PEOPLE_DIR','../openstates-people')).resolve()
OUT=ROOT/'data/people/state-executives.json'
STATES='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR'.split()
ASOF=datetime.date.today()
TYPES={'governor','lt_governor','lieutenant governor','attorney general','secretary of state'}

def parse(d):
    if isinstance(d,datetime.datetime):
        return d.date()
    if isinstance(d,datetime.date):
        return d
    try:
        return datetime.date.fromisoformat(str(d)[:10])
    except (TypeError,ValueError):
        return None

def active(roles):
    valid=[]
    for r in roles or []:
        if not isinstance(r,dict):
            continue
        if str(r.get('type','')).lower() not in TYPES:
            continue
        start,end=parse(r.get('start_date')),parse(r.get('end_date'))
        if (start and start>ASOF) or (end and end<=ASOF):
            continue
        valid.append((start or datetime.date(1900,1,1),r))
    return max(valid,key=lambda x:x[0])[1] if valid else None

def read():
    found={}
    skipped=[]
    for state in STATES:
        folder=UPSTREAM/'data'/state.lower()/'executive'
        if not folder.is_dir():
            skipped.append(state)
            continue
        for file in folder.glob('*.yml'):
            if file.stat().st_size>50000:
                continue
            doc=yaml.safe_load(file.read_text(encoding='utf-8'))
            if not isinstance(doc,dict):
                continue
            role=active(doc.get('roles') or [])
            uid=str(doc.get('id') or '')
            name=str(doc.get('name') or '')
            if not role or not name or not re.fullmatch(r'ocd-person/[a-zA-Z0-9-]{20,50}',uid):
                continue
            parties=doc.get('party') or []
            party=str(parties[-1].get('name') or '')[:55] if parties and isinstance(parties[-1],dict) else 'Not indexed'
            found[uid]={
                'id':uid,'name':name[:110],'state':state,
                'role':str(role['type'])[:50],'party':party,
                'source':'https://github.com/openstates/people/blob/main/data/'+state.lower()+'/executive/'+file.name,
                'reviewStatus':'third_party_executive_registry_unreviewed'
            }
    governors=sum(row['role']=='governor' for row in found.values())
    if not 40<=governors<=55:
        raise RuntimeError('Unexpected governor coverage: '+str(governors)+'; previous dataset retained')
    doc={'schema':'power-atlas.state-executives.v1',
         'license':'CC0-1.0',
         'sourceCatalog':'https://github.com/openstates/people',
         'asOfDate':ASOF.isoformat(),
         'publicationStatus':'state_office_identity_requires_official_confirmation',
         'claimScope':'Serving executive office does not prove involvement in a redistricting decision',
         'coverage':{'governors':governors,'totalExecutivePosts':len(found),'statesWithoutExecutiveFolder':skipped},
         'records':sorted(found.values(),key=lambda x:x['id'])}
    content=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=content:
        OUT.write_text(content,encoding='utf-8')
    print('Executive roles:',len(found),'governors:',governors,'missing folders:',skipped)

if __name__=='__main__':
    read()
