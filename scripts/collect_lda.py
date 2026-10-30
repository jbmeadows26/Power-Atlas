"""Bounded lobbying disclosure collector from US Senate Office of Public Records.
Anonymous API, only confirmed issue-text matches, no individual lobbyist details.
"""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import re
import datetime
import time

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/lobbying/lda-filings.json'
API = 'https://lda.gov/api/v1/filings/'
TERMS = ('redistricting', 'voting rights', 'congressional district')
YEARS = (2026, 2025)
MAX_BYTES = 350000

def fetch(term, year):
    # Keep response bodies under 350KB; dense congressional-district filings
    # need smaller pages. Same 20-record cap, not expanded search access.
    # A 2026 congressional-district filing made even a five-row response exceed
    # the 350KB safety bound. Use two rows per page for this one query.
    page_size = 2 if (term == 'congressional district' and year == 2026) else (5 if term == 'congressional district' else 10)
    found = []
    for page in range(1, (20 // page_size) + 1):
        # LDA.gov documents a 15-request/minute anonymous limit. Pace well
        # below that threshold; never retry a 429 or change identity/host.
        time.sleep(4.5)
        query = urlencode({'filing_specific_lobbying_issues':term,
                           'filing_year':year,'page_size':page_size,'page':page})
        req = Request(API+'?'+query,headers={'User-Agent':'PowerAtlasResearch/1.0; public filing index',
                                              'Accept':'application/json'})
        for attempt in range(2):
            try:
                with urlopen(req,timeout=25) as response:
                    if response.status!=200:
                        raise RuntimeError('Senate API HTTP error: '+str(response.status))
                    content=response.read(MAX_BYTES+1)
                    if len(content)>MAX_BYTES:
                        raise RuntimeError('LDA response exceeded safety limit at page_size='+str(page_size))
                break
            except (HTTPError, URLError, TimeoutError) as exc:
                # Retry temporary server/network faults only. Never retry 401,
                # 403 or 429 within the same run or evade access restrictions.
                if isinstance(exc,HTTPError) and exc.code not in (500,502,503,504):
                    raise
                if attempt:
                    raise
                time.sleep(1.0)
        doc=json.loads(content)
        if not isinstance(doc.get('results'),list):
            raise ValueError('Unexpected LDA schema')
        found.extend(doc['results'])
        if not doc.get('next'):
            break
    return found

def matching_issue(filing):
    activities = filing.get('lobbying_activities') or []
    if not isinstance(activities,list):
        return ''
    for row in activities:
        if not isinstance(row,dict):
            continue
        detail = str(row.get('description') or row.get('specific_lobbying_issues') or row.get('specific_issues') or '')
        if any(q in detail.lower() for q in TERMS):
            return ' '.join(detail.split())[:180]
    return ''

def collect():
    prior=json.loads(DEST.read_text(encoding='utf-8')) if DEST.exists() else {}
    old=prior.get('records',[])
    # Six bounded issue/year queries have already been collected today. Avoid
    # repeat requests that would consume the official anonymous rate budget.
    if (old and prior.get('successfulQueries',0)>=len(TERMS)*len(YEARS)
            and prior.get('failedQueries',0)==0
            and all(row.get('dateAccessed')==datetime.date.today().isoformat() for row in old)):
        print('Cached verified Senate LDA sample retained:',len(old),'records; no API requests')
        return
    by_id={r['id']:r for r in old}
    successes=0
    failures=[]
    fetched=0
    matched=0
    issue_hits=0
    activity_rows=0
    activity_filings=0
    example_activity_fields=[]
    example_filing_fields=[]
    for term in TERMS:
        for query_year in YEARS:
            try:
                filings=fetch(term,query_year)
            except HTTPError as exc:
                # Do not switch identities/hosts to circumvent 403/429.
                if exc.code in (401,403,429):
                    raise RuntimeError(f'LDA access or rate restriction: HTTP {exc.code}') from exc
                failures.append((term,query_year,'HTTP '+str(exc.code)))
                continue
            except (URLError,TimeoutError,ValueError,RuntimeError,OSError) as exc:
                failures.append((term,query_year,type(exc).__name__+': '+str(exc)[:130]))
                continue
            successes+=1
            fetched+=len(filings)
            for filing in filings:
                if not isinstance(filing,dict):
                    continue
                if not example_filing_fields:
                    example_filing_fields=sorted(filing.keys())[:55]
                activities=filing.get('lobbying_activities') or []
                if isinstance(activities,list):
                    activity_rows+=len(activities)
                    activity_filings+=bool(activities)
                    if not example_activity_fields and activities and isinstance(activities[0],dict):
                        example_activity_fields=sorted(activities[0].keys())[:45]
                issue=matching_issue(filing)
                if not issue:
                    continue
                issue_hits+=1
                uid=str(filing.get('filing_uuid') or '')
                if not re.fullmatch(r'[0-9a-fA-F-]{36}',uid):
                    continue
                registrant=filing.get('registrant') or {}
                client=filing.get('client') or {}
                if not isinstance(registrant,dict) or not isinstance(client,dict):
                    continue
                client_name=str(client.get('name') or '')[:125]
                firm=str(registrant.get('name') or '')[:125]
                try:
                    year=int(filing.get('filing_year'))
                except (TypeError,ValueError):
                    continue
                if not client_name or not firm or year!=query_year:
                    continue
                record={
                    'id':'lda-'+uid,
                    'filingId':uid,'client':client_name,'registrant':firm,
                    'year':year,'period':str(filing.get('filing_period') or '')[:35],
                    'type':str(filing.get('filing_type') or '')[:20],
                    'source':'https://lda.gov/filings/public/filing/search/',
                    'sourceApi':API+uid+'/',
                    'dateAccessed':datetime.date.today().isoformat(),
                    'specificIssuesExcerpt':issue,
                    'reviewStatus':'issue_text_matched_unreviewed',
                    'claimScope':'Text-matched lobbying disclosure only. No connection to map outcomes established.'
                }
                for k in ('income','expenses'):
                    value=filing.get(k)
                    if isinstance(value,(int,float)) and not isinstance(value,bool):
                        record[k+'USD']=round(float(value),2)
                by_id[record['id']]=record
                matched+=1
    if not successes:
        raise RuntimeError('All Senate API queries failed; preserve prior data: '+str(failures))
    if len(by_id)>150:
        by_id=dict(sorted(by_id.items(),reverse=True)[:150])
    body={'schema':'power-atlas.lda-filings.v1','publicationStatus':'review_required',
          'method':'up to 20 filings per issue term/year; 2-, 5- or 10-row pages to bound response size; incomplete search coverage',
          'attribution':'Senate Office of Public Records cannot vouch for the data or analyses derived from these data after the data have been retrieved from LDA.gov.',
          'successfulQueries':successes,'failedQueries':len(failures),
          'fetchedRowsInBoundedPages':fetched,'matchedRowsInBoundedPages':matched,
          'issueTextMatchedRows':issue_hits,'filingsWithActivities':activity_filings,
          'activityRowsInspected':activity_rows,
          'sampleFilingFieldNames':example_filing_fields,
          'sampleActivityFieldNames':example_activity_fields,
          'failedQueryDetails':[{'term':t,'year':y,'error':e} for t,y,e in failures],
          'records':sorted(by_id.values(),key=lambda r:r['id'])}
    rendered=json.dumps(body,indent=2,ensure_ascii=False)+'\n'
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if not DEST.exists() or DEST.read_text(encoding='utf-8')!=rendered:
        DEST.write_text(rendered,encoding='utf-8')
    print('LDA issue-matched filings:',len(by_id),'fetched:',fetched,'issue matches:',issue_hits,'matched:',matched,'activities:',activity_rows,'successful queries:',successes,'failed:',len(failures))
    if failures:
        print('Partial failures:',failures)

if __name__=='__main__':
    collect()
