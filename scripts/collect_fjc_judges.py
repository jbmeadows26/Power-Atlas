"""Official federal Article III judge appointment history from Federal Judicial Center.

Public domain FJC exports. One record per judicial service appointment.
Only appointment metadata and original FJC biography URLs; no demographic,
professional-history, personal contact fields, or raw document storage.
FJC's directory notice reports data current as of 2026-10-23.
"""
from __future__ import annotations
from urllib.request import Request, urlopen
from pathlib import Path
from io import StringIO
from collections import Counter
import csv
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/judiciary/fjc-appointments.json'
INDEX=ROOT/'data/judiciary/fjc-appointment-index.json'
BASE='https://www.fjc.gov/sites/default/files/history/'
LANDING='https://www.fjc.gov/node/7436'
MAX_BYTES=7_500_000

def norm(s):
    return '_'.join(re.sub(r'[,/]', ' ', s or '').replace('\n',' ').lower().split())

def fetch(name):
    request=Request(BASE+name,headers={'User-Agent':'PowerAtlasResearch/1.0 (public Article III judicial data)'})
    with urlopen(request,timeout=35) as response:
        if response.status!=200:
            raise RuntimeError('Federal Judicial Center file unavailable: '+name)
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise RuntimeError('FJC file exceeds memory bound: '+name)
    decoded=raw.decode('utf-8-sig',errors='replace')
    reader=csv.DictReader(StringIO(decoded))
    if not reader.fieldnames:
        raise RuntimeError('FJC CSV missing header: '+name)
    mapped={}
    for row in reader:
        parsed={norm(k):str(v or '').strip() for k,v in row.items() if k}
        uid=parsed.get('nid','')
        if not re.fullmatch(r'[0-9]{1,10}',uid):
            continue
        mapped.setdefault(uid,[]).append(parsed)
    if len(mapped)<1000:
        raise RuntimeError('Unusual FJC directory size for '+name+': '+str(len(mapped)))
    return mapped

def names(demo):
    people={}
    for uid,arr in demo.items():
        row=arr[0]
        first=row.get('first_name') or row.get('given_name') or ''
        last=row.get('last_name') or row.get('surname') or ''
        name=(first+' '+last).strip()
        if not name:
            name=row.get('name') or ''
        people[uid]=' '.join(name.split())[:110] if name else 'Judge FJC '+uid
    return people

def collect():
    demo=fetch('demographics.csv')
    service=fetch('federal-judicial-service.csv')
    people=names(demo)
    out={}
    keys={'court_name','appointing_president','confirmation_date','commission_date'}
    sample=next(iter(service.values()))[0]
    if not keys.issubset(set(sample)):
        raise RuntimeError('FJC changed required service columns: '+str(sorted(sample))[:400])
    for nid,appointments in service.items():
        for row in appointments:
            court=row.get('court_name','')
            president=row.get('appointing_president','')
            if not court or not president:
                continue
            seq=str(row.get('sequence') or '1')
            if not re.fullmatch(r'[0-9]{1,2}',seq):
                continue
            key='fjc-service-'+nid+'-'+seq
            item={
                'id':key,'nid':nid,'name':people.get(nid,'Judge FJC '+nid),
                'court':court[:180], 'appointingPresident':president[:80],
                'source':'https://www.fjc.gov/node/'+nid,
                'sourceTable':BASE+'federal-judicial-service.csv',
                'reviewStatus':'official_FJC_appointment_indexed',
                'claimScope':'An appointment is a documented government action; this record does not establish partisan judicial conduct'
            }
            for target,field in [
                ('presidentParty','party_of_appointing_president'),
                ('appointmentTitle','appointment_title'),
                ('seatId','seat_id'),('nominationDate','nomination_date'),
                ('confirmationDate','confirmation_date'),
                ('commissionDate','commission_date'),
                ('terminationDate','termination_date')]:
                val=row.get(field)
                if val:
                    item[target]=val[:100]
            out[key]=item
    if not 4000<=len(out)<=6000:
        raise RuntimeError('Unexpected FJC appointment count '+str(len(out)))
    active=sum(not x.get('terminationDate') for x in out.values())
    presidents=Counter(x['appointingPresident'] for x in out.values())
    document={
        'schema':'power-atlas.fjc.article-iii-appointments.v1',
        'publicationStatus':'official_source_indexed_claims_require_review',
        'sourceCatalog':LANDING,'license':'US federal public domain',
        'sourceAsOf':'2026-10-23',
        'limitations':'FJC directory updates currently paused; missing termination date is not a guarantee of currently sitting service. Appointing president or party does not establish a judge ideology or wrongful conduct.',
        'appointments':sorted(out.values(),key=lambda x:x['id'])
    }
    body=json.dumps(document,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(body.encode())>3000000:
        raise RuntimeError('FJC appointment dataset exceeded compact output cap')
    summary={
        'schema':'power-atlas.fjc.appointment-index.v1',
        'sourceCatalog':LANDING,'sourceAsOf':'2026-10-23',
        'publicationStatus':'official_source_indexed',
        'appointmentRecords':len(out),'withoutTerminationRecorded':active,
        'presidents':[{'name':k,'appointments':v} for k,v in sorted(presidents.items())]
    }
    summary_text=json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=body:
        OUT.write_text(body,encoding='utf-8')
    if not INDEX.exists() or INDEX.read_text(encoding='utf-8')!=summary_text:
        INDEX.write_text(summary_text,encoding='utf-8')
    print('FJC Article III appointment records:',len(out),'missing termination:',active,
          'bytes:',len(body.encode()))

if __name__=='__main__':
    collect()
