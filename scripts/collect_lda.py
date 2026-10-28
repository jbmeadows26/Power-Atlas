"""Anonymous, bounded Senate LDA filing index. No personal lobbyist details or documents."""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re
import datetime

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/lobbying/lda-filings.json'
API = 'https://lda.gov/api/v1/filings/'
TERMS = ('redistricting', 'voting rights', 'election integrity')
MAX_BYTES = 350000

def fetch(term):
    query=urlencode({'client_name':term,'filing_year':2026,'page_size':20})
    req=Request(API+'?'+query,headers={'User-Agent':'PowerAtlasResearch/1.0; public filing index'})
    with urlopen(req,timeout=25) as response:
        if response.status!=200:
            raise RuntimeError('Senate API HTTP error')
        content=response.read(MAX_BYTES+1)
        if len(content)>MAX_BYTES:
            raise RuntimeError('LDA response exceeded safety limit')
    doc=json.loads(content)
    if not isinstance(doc.get('results'),list):
        raise ValueError('Unexpected LDA schema')
    return doc['results']

def collect():
    old=json.loads(DEST.read_text(encoding='utf-8'))['records'] if DEST.exists() else []
    by_id={r['id']:r for r in old}
    successes=0
    failures=[]
    for term in TERMS:
        try:
            filings=fetch(term)
        except Exception as exc:
            failures.append((term,type(exc).__name__))
            continue
        successes+=1
        for filing in filings:
            uid=str(filing.get('filing_uuid') or '')
            if not re.fullmatch(r'[0-9a-fA-F-]{36}',uid):
                continue
            registrant=filing.get('registrant') or {}
            client=filing.get('client') or {}
            if not isinstance(registrant,dict) or not isinstance(client,dict):
                continue
            client_name=str(client.get('name') or '')[:125]
            firm=str(registrant.get('name') or '')[:125]
            if not client_name or not firm:
                continue
            year=filing.get('filing_year')
            if year!=2026:
                continue
            record={
                'id':'lda-'+uid,
                'filingId':uid,'client':client_name,'registrant':firm,
                'year':year,'period':str(filing.get('filing_period') or '')[:35],
                'type':str(filing.get('filing_type') or '')[:20],
                'source':'https://lda.gov/filings/public/filing/search/',
                'sourceApi':API+uid+'/',
                'dateAccessed':datetime.date.today().isoformat(),
                'reviewStatus':'federal_lobbying_filing_unreviewed',
                'claimScope':'Filing existence only; neither the lobbying issue nor redistricting involvement is verified'
            }
            for k in ('income','expenses'):
                value=filing.get(k)
                if isinstance(value,(int,float)) and not isinstance(value,bool):
                    record[k+'USD']=round(float(value),2)
            by_id[record['id']]=record
    if not successes:
        raise RuntimeError('No Senate API queries succeeded; preserve prior data: '+str(failures))
    if len(by_id)>150:
        by_id=dict(sorted(by_id.items(),reverse=True)[:150])
    body={'schema':'power-atlas.lda-filings.v1','publicationStatus':'review_required',
          'attribution':'Data retrieved from US Senate Office of Public Records. The Office cannot vouch for analyses derived after retrieval.',
          'records':sorted(by_id.values(),key=lambda r:r['id'])}
    rendered=json.dumps(body,indent=2,ensure_ascii=False)+'\n'
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if not DEST.exists() or DEST.read_text(encoding='utf-8')!=rendered:
        DEST.write_text(rendered,encoding='utf-8')
    print('Senate LDA filings:',len(by_id),'queries succeeded:',successes,'failed:',failures)

if __name__=='__main__':
    collect()
