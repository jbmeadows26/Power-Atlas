"""Compact state-legislator identity index sourced from canonical CC0 GitHub YAML.

Open States' separate nightly CSV host may return HTTP 403. Do not retry or
evade its access controls. Use the openly licensed canonical openstates/people
GitHub repository, checked out through a standard public Git clone.

Each state's people are stored separately for lazy loading by the mobile app.
Private addresses, email, phones, images, biographies and birth dates omitted.
"""
from pathlib import Path
import datetime
import json
import os
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=Path(os.environ.get('OPENSTATES_PEOPLE_DIR','../openstates-people')).resolve()
OUT=ROOT/'data/people/states'
INDEX=ROOT/'data/people/state-legislators-index.json'
LICENSE='CC0-1.0'
TODAY=datetime.date.today()
STATES='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR'.split()

def day(value):
    if isinstance(value,datetime.datetime):
        return value.date()
    if isinstance(value,datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except (ValueError,TypeError):
        return None

def choose_role(roles):
    valid=[]
    for role in roles or []:
        if not isinstance(role,dict) or role.get('type') not in ('upper','lower'):
            continue
        start=day(role.get('start_date'))
        end=day(role.get('end_date'))
        if start and start>TODAY:
            continue
        if end and end<=TODAY:
            continue
        if not str(role.get('district') or '').strip():
            continue
        valid.append((start or datetime.date(1900,1,1),role))
    return max(valid,key=lambda r:r[0])[1] if valid else None

def choose_party(parties):
    active=[]
    for p in parties or []:
        if not isinstance(p,dict):
            continue
        begin=day(p.get('start_date'))
        end=day(p.get('end_date'))
        if begin and begin>TODAY or end and end<=TODAY:
            continue
        if p.get('name'):
            active.append((begin or datetime.date(1900,1,1),p.get('name')))
    return str(max(active,key=lambda r:r[0])[1])[:55] if active else 'Not indexed'

def read_state(abbr):
    folder=UPSTREAM/'data'/abbr.lower()/'legislature'
    if not folder.is_dir():
        raise RuntimeError('Missing canonical Open States legislature folder: '+abbr)
    result={}
    files=sorted(folder.glob('*.yml'))
    if not 5<=len(files)<=800:
        raise RuntimeError('Unexpected canonical legislature file count for '+abbr)
    for path in files:
        if path.stat().st_size>50000:
            raise RuntimeError('Unusually large upstream person file: '+abbr+'/'+path.name)
        obj=yaml.safe_load(path.read_text(encoding='utf-8'))
        if not isinstance(obj,dict):
            continue
        uid=str(obj.get('id') or '')
        if not re.fullmatch(r'ocd-person/[a-zA-Z0-9-]{20,50}',uid):
            continue
        name=str(obj.get('name') or '').strip()
        role=choose_role(obj.get('roles'))
        if not name or not role:
            continue
        id='state-person-'+uid.split('/')[-1]
        record={
            'id':id,'ocdPersonId':uid,'name':name[:110],'state':abbr,
            'chamber':role['type'],'district':str(role['district'])[:60],
            'party':choose_party(obj.get('party')),
            'source':'https://github.com/openstates/people/blob/main/data/'+abbr.lower()+'/legislature/'+path.name,
            'sourceCatalog':'https://github.com/openstates/people',
            'sourceLicense':LICENSE,'reviewStatus':'third_party_legislator_registry_unreviewed',
            'claimScope':'Current state legislative role only; does not establish redistricting action or misconduct'
        }
        result[id]=record
    if len(result)<5:
        raise RuntimeError('No usable serving state legislators from '+abbr)
    return sorted(result.values(),key=lambda r:r['id'])

def collect():
    if not (UPSTREAM/'LICENSE').is_file():
        raise RuntimeError('Canonical CC0 source not checked out; refusing unrelated source')
    OUT.mkdir(parents=True,exist_ok=True)
    index=[]
    total=0
    for abbr in STATES:
        people=read_state(abbr)
        body=json.dumps({
            'schema':'power-atlas.state-legislators.state.v1',
            'publicationStatus':'source_registry_crosscheck_pending',
            'state':abbr,'license':LICENSE,'records':people
        },ensure_ascii=False,separators=(',',':'))+'\n'
        if len(body.encode())>210000:
            raise RuntimeError('Exceeded mobile-sized state record cap: '+abbr)
        target=OUT/(abbr+'.json')
        if not target.exists() or target.read_text(encoding='utf-8')!=body:
            target.write_text(body,encoding='utf-8')
        index.append({'state':abbr,'members':len(people),
                      'source':'https://github.com/openstates/people/tree/main/data/'+abbr.lower()+'/legislature',
                      'reviewStatus':'curated_CC0_source_unreviewed'})
        total+=len(people)
    if not 4000<=total<=10000:
        raise RuntimeError('Unexpected nationwide state legislative record count '+str(total))
    doc={
        'schema':'power-atlas.state-legislators.index.v1',
        'publicationStatus':'source_registry_crosscheck_pending',
        'license':LICENSE,'sourceCatalog':'https://github.com/openstates/people',
        'asOfDate':TODAY.isoformat(),'jurisdictions':index,'totalIndexed':total
    }
    encoded=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
    if not INDEX.exists() or INDEX.read_text(encoding='utf-8')!=encoded:
        INDEX.write_text(encoded,encoding='utf-8')
    print('Indexed state legislators:',total,'jurisdictions:',len(index),
          'bytes in index:',len(encoded.encode()))

if __name__=='__main__':
    collect()
