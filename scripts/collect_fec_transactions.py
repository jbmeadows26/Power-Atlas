"""Incremental FEC Schedule B disbursements for already-indexed committee IDs.
No personal addresses, recipient contact details, bulk archives, or paid services.
"""
import json
import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'data/batches/fec-committees.json'
OUT = ROOT / 'data/finance/fec-disbursements.json'
API = 'https://api.open.fec.gov/v1/schedules/schedule_b/'
KEY = os.environ.get('FEC_API_KEY') or 'DEMO_KEY'
MAX_COMMITTEES = 2 if KEY == 'DEMO_KEY' else 7
PER_PAGE = 20
MAX_ITEMS = 250

def fetch(cid):
    query = urlencode({'api_key':KEY,'committee_id':cid,'per_page':PER_PAGE,
                       'sort':'-disbursement_date','two_year_transaction_period':2026})
    req = Request(API + '?' + query,headers={'User-Agent':'PowerAtlas/1.0 public-interest research'})
    with urlopen(req,timeout=25) as response:
        if response.status != 200:
            raise RuntimeError('FEC HTTP response not successful')
        data = response.read(400001)
        if len(data) > 400000:
            raise RuntimeError('FEC response size limit exceeded')
    body = json.loads(data)
    if not isinstance(body.get('results'),list):
        raise ValueError('FEC response missing results')
    return body['results']

def collect():
    if not INDEX.exists():
        raise RuntimeError('Committee discovery has not completed; refusing unscoped ingestion')
    committees = json.loads(INDEX.read_text(encoding='utf-8'))['records']
    allow = [row['id'][4:] for row in committees
             if re.fullmatch(r'fec-C[0-9]{8}',row.get('id',''))][:MAX_COMMITTEES]
    existing = json.loads(OUT.read_text(encoding='utf-8'))['records'] if OUT.exists() else []
    by_id = {row['id']:row for row in existing}
    added = 0
    for cid in allow:
        for raw in fetch(cid):
            sub = str(raw.get('sub_id') or '')
            if not sub.isdigit():
                continue
            key = 'fec-disbursement-'+sub
            amount = raw.get('disbursement_amount')
            day = raw.get('disbursement_date')
            if not isinstance(amount,(int,float)) or not isinstance(day,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):
                continue
            # Private individual recipients can occur in Schedule B; retain only formal committee IDs,
            # not arbitrary payee names, addresses, or occupations.
            recipient_id = str(raw.get('recipient_committee_id') or '')
            if not re.fullmatch(r'C[0-9]{8}',recipient_id):
                continue
            item = {
                'id':key,'committeeId':cid,'recipientCommitteeId':recipient_id,
                'date':day,'amountUSD':round(float(amount),2),
                'source':'https://www.fec.gov/data/disbursements/?committee_id='+cid,
                'status':'official_fec_filing_unreviewed',
                'scope':'2026 Schedule B report; financial transfer is not evidence of misconduct'
            }
            if key not in by_id:
                by_id[key]=item
                added+=1
            if len(by_id)>=MAX_ITEMS:
                break
        if len(by_id)>=MAX_ITEMS:
            break
    # No destruction when API returns an empty page; keep previous data.
    output={'schema':'power-atlas.fec.disbursements.v1','reviewStatus':'requires_filing_review',
            'records':sorted(by_id.values(),key=lambda x:x['id'])}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(output,indent=2,ensure_ascii=False)+'\n'
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=text:
        OUT.write_text(text,encoding='utf-8')
    print('FEC linked committee payments: total',len(by_id),'added',added)
if __name__=='__main__':
    collect()
