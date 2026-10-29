"""Bounded official FEC Schedule B committee-recipient aggregates.

Aggregate by recipient committee ID avoids storing individual payees, names,
addresses or memoed line items. It is NOT a complete transaction ledger.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json
import os
import re
import time

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/finance/fec-recipient-aggregates.json'
API='https://api.open.fec.gov/v1/schedules/schedule_b/by_recipient_id/'
KEY=os.environ.get('FEC_API_KEY') or 'DEMO_KEY'
COMMITTEES=('C00630707','C00747279') if KEY=='DEMO_KEY' else (
    'C00630707','C00747279','C00561837')
CYCLE=2024
MAX_BYTES=220_000
ID=re.compile(r'^C[0-9]{8}$')

def fetch(cid):
    url=API+'?'+urlencode({'committee_id':cid,'cycle':CYCLE,
                             'per_page':20,'page':1,'api_key':KEY})
    req=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0; committee aggregates only',
                             'Accept':'application/json'})
    for attempt in range(2):
        try:
            with urlopen(req,timeout=24) as response:
                if response.status!=200:
                    raise RuntimeError('FEC recipient aggregates HTTP '+str(response.status))
                body=response.read(MAX_BYTES+1)
                if len(body)>MAX_BYTES:
                    raise RuntimeError('FEC recipient aggregate response exceeded bound')
            break
        except (HTTPError,URLError,TimeoutError) as exc:
            if isinstance(exc,HTTPError) and exc.code not in (500,502,503,504):
                raise
            if attempt:
                raise
            time.sleep(2)
    doc=json.loads(body)
    if not isinstance(doc.get('results'),list):
        raise ValueError('Unexpected FEC recipient aggregate schema')
    return doc

def collect():
    prior=json.loads(DEST.read_text(encoding='utf-8')) if DEST.exists() else {}
    by_id={r['id']:r for r in prior.get('records',[])}
    failures=[]
    successes=0
    inspected=0
    for cid in COMMITTEES:
        try:
            doc=fetch(cid)
        except (HTTPError,URLError,TimeoutError,RuntimeError,ValueError) as exc:
            failures.append({'committeeId':cid,'error':type(exc).__name__+': '+str(exc)[:120]})
            if isinstance(exc,HTTPError) and exc.code in (401,403,429):
                break
            continue
        successes+=1
        for row in doc['results']:
            inspected+=1
            if not isinstance(row,dict):
                continue
            payer=str(row.get('committee_id') or '')
            recipient=str(row.get('recipient_id') or '')
            if payer!=cid or not ID.fullmatch(recipient):
                continue
            if row.get('cycle')!=CYCLE or not isinstance(row.get('total'),(int,float)):
                continue
            if not isinstance(row.get('count'),int) or row['count']<0:
                continue
            rid=f'fec-recipient-aggregate-{CYCLE}-{cid}-{recipient}'
            by_id[rid]={
                'id':rid,'cycle':CYCLE,
                'sourceCommitteeId':cid,'recipientCommitteeId':recipient,
                'recipientCommitteeName':str(row.get('committee_name') or '')[:130],
                'amountUSD':round(float(row['total']),2),
                'disbursementCount':row['count'],
                'source':API+'?'+urlencode({'committee_id':cid,'cycle':CYCLE,'per_page':20,'page':1}),
                'reviewStatus':'official_fec_aggregate_unreviewed',
                'relationshipType':'reported_aggregate_committee_disbursements',
                'limitation':'Schedule B recipient-ID aggregate excludes memo items; not a complete itemized payment ledger'
            }
    if not successes:
        raise RuntimeError('No successful official FEC recipient-aggregate query; prior data preserved: '+str(failures))
    result={
        'schema':'power-atlas.fec-committee-recipient-aggregates.v1',
        'source':API,
        'licenseNote':'FEC public campaign finance data; no individual contributor or payee information stored',
        'method':'First 20 recipient committee IDs for each of up to three scoped redistricting committees in 2024; incomplete',
        'queriedCommittees':list(COMMITTEES),
        'successfulQueries':successes,
        'failedQueries':failures,
        'rawAggregateRowsInspected':inspected,
        'records':sorted(by_id.values(),key=lambda x:x['id'])
    }
    DEST.parent.mkdir(parents=True,exist_ok=True)
    rendered=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if not DEST.exists() or DEST.read_text(encoding='utf-8')!=rendered:
        DEST.write_text(rendered,encoding='utf-8')
    print('FEC committee-recipient aggregate rows:',len(by_id),'successful:',successes,'failed:',len(failures))

if __name__=='__main__':
    collect()
