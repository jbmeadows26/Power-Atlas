"""Incrementally expand state redistricting source coverage across 50 states + DC.

Each action searches at most 8 jurisdictions per run via public no-key API.
Maintains checkpoint and all prior bill IDs; no full text, addresses or
donor details. Rate/auth restrictions are respected, not circumvented.
A completed search is first-page keyword coverage, NOT a bill census.
"""
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json
import re
import time

ROOT=Path(__file__).resolve().parents[1]
BILLS=ROOT/'data/legislation/state-redistricting-bills.json'
CHECKPOINT=ROOT/'data/legislation/state-redistricting-jurisdictions.json'
API='https://api.billcommons.org/api/v1/search'
STATES='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV DC'.split()+['WY']
# Correct the US set against the public source's 51 jurisdictions.
STATES=sorted(set(STATES))
MAX_PER_RUN=8
END=date(2026,10,30)
MAX_BYTES=220000

def fetch_state(state):
    """Bounded official-link index search; shrink page only for slow IL/TX.

    A smaller page is explicitly checkpointed and never called an exhaustive
    jurisdiction search. Access/rate errors stop immediately, without fallback.
    """
    page_sizes=(20,10,5) if state in ('IL','TX') else (20,)
    failures=[]
    requests=0
    for per_page in page_sizes:
        q=urlencode({'q':'redistricting','jurisdiction':state,'per_page':per_page,'page':1})
        url=API+'?'+q
        req=Request(url,headers={'User-Agent':'PowerAtlasPublicResearch/1.0 state legislative index',
                                 'Accept':'application/json'})
        retries=2 if per_page==20 else 1
        for attempt in range(retries):
            requests+=1
            try:
                with urlopen(req,timeout=18) as resp:
                    if resp.status!=200:raise RuntimeError('Unexpected source response')
                    raw=resp.read(MAX_BYTES+1)
                    if len(raw)>MAX_BYTES:raise RuntimeError('State search exceeded bounded size')
                body=json.loads(raw)
                if not isinstance(body.get('data'),list):raise ValueError('Unexpected state search schema')
                return body,url,per_page
            except HTTPError as exc:
                if exc.code not in (500,502,503,504):
                    exc.requestsAttempted=requests
                    exc.pageSizesAttempted=list(page_sizes[:page_sizes.index(per_page)+1])
                    raise
                failures.append(exc)
            except (URLError,OSError,TimeoutError) as exc:
                failures.append(exc)
            if attempt+1<retries:
                time.sleep(1.5)
    last=failures[-1]
    last.requestsAttempted=requests
    last.pageSizesAttempted=list(page_sizes)
    raise last

def record(raw,state):
    uid=str(raw.get('id') or '')
    if not re.fullmatch(r'[A-Fa-f0-9-]{36}',uid):return None
    source=str(raw.get('source_url') or '')
    title=' '.join(str(raw.get('title') or '').split())[:250]
    identifier=str(raw.get('identifier') or '')[:45]
    if not source.startswith('https://') or not title or not identifier:return None
    terms=('redistrict','gerrymander','reapportion','congressional district')
    return {'id':'state-bill-'+uid,'billUuid':uid,'state':state,
            'identifier':identifier,'title':title,
            'issueClass':'redistricting_specific_title' if any(k in title.lower() for k in terms) else 'keyword_search_candidate_unverified',
            'latestActionDate':str(raw.get('latest_action_date') or '')[:18],
            'latestAction':str(raw.get('latest_action_text') or '')[:180],
            'status':str(raw.get('status') or 'not_indexed')[:70],
            'source':source,
            'sourceIndex':'https://billcommons.org/',
            'retrievalScope':'first_20_state_specific_keyword_results_only',
            'reviewStatus':'third_party_index_official_source_review_required'}

def select_jurisdictions(states,completed,attempts,limit):
    """Least-attempted first; keep failures eligible, never skip a state forever."""
    return sorted((s for s in states if s not in completed),
                  key=lambda s:(int(attempts.get(s,0)),s))[:limit]

def run():
    if date.today()>END:
        print('Deadline passed; no new source requests')
        return
    if not BILLS.exists():
        raise RuntimeError('Initialize bounded national source index first')
    body=json.loads(BILLS.read_text(encoding='utf-8'))
    indexed={row['id']:row for row in body['records']}
    previous=json.loads(CHECKPOINT.read_text(encoding='utf-8')) if CHECKPOINT.exists() else {}
    done=previous.get('jurisdictions',{})
    if not isinstance(done,dict):raise ValueError('Invalid previous coverage checkpoint')
    if len(STATES)!=51:
        raise RuntimeError('Expected 50 states and District of Columbia; received '+str(len(STATES)))
    # Try never-attempted jurisdictions before retrying slow/failed ones.
    # This avoids repeatedly spending the entire bounded run on the same
    # timeouts while preserving all failed jurisdictions for later retries.
    attempts=previous.get('attemptCounts',{})
    if not isinstance(attempts,dict):raise ValueError('Invalid jurisdiction attempt checkpoint')
    # Persist state-level failures across batches; latestBatch alone is overwritten.
    failures=previous.get('sourceFailures',{})
    if not isinstance(failures,dict):raise ValueError('Invalid state source failure checkpoint')
    if 'attemptCounts' not in previous:
        for item in previous.get('latestBatch',[]):
            state=item.get('state')
            if state in STATES and state not in done:
                attempts[state]=max(1,int(attempts.get(state,0)))
    selected=select_jurisdictions(STATES,done,attempts,MAX_PER_RUN)
    results=[]
    for state in selected:
        attempts[state]=int(attempts.get(state,0))+1
        try:
            response,url,per_page=fetch_state(state)
        except HTTPError as exc:
            restricted=exc.code in (401,403,429)
            status='access_or_rate_deferred' if restricted else 'http_failure'
            failures[state]={'status':status,'httpStatus':exc.code,
                             'lastAttemptUTC':date.today().isoformat(),
                             'sourceEndpoint':API,
                             'requestsAttempted':getattr(exc,'requestsAttempted',1),
                             'perPageVariantsAttempted':getattr(exc,'pageSizesAttempted',[20]),
                             'retryPolicy':'do_not_retry_access_or_rate_restrictions' if restricted else 'bounded_retry_only_for_5xx'}
            results.append({'state':state,'status':status,'http':exc.code})
            if restricted:break
            continue
        except (URLError,OSError,TimeoutError,RuntimeError,ValueError) as exc:
            error_type=type(exc).__name__
            failures[state]={'status':'temporary_unavailable','errorType':error_type,
                             'lastAttemptUTC':date.today().isoformat(),
                             'sourceEndpoint':API,
                             'requestsAttempted':getattr(exc,'requestsAttempted',1),
                             'perPageVariantsAttempted':getattr(exc,'pageSizesAttempted',[20]),
                             'retryPolicy':'bounded_network_retry_then_later_batch'}
            results.append({'state':state,'status':'temporary_unavailable','errorType':error_type})
            continue
        failures.pop(state,None)
        new=0
        for row in response['data']:
            parsed=record(row,state)
            if parsed is None:continue
            if parsed['id'] not in indexed:
                indexed[parsed['id']]=parsed;new+=1
        done[state]={
            'query':'redistricting','searchPage':1,'perPage':per_page,
            'totalMatchesReported':response.get('pagination',{}).get('total'),
            'newIndexedRecords':new,
            'status':'first_page_indexed_not_exhaustive'
        }
        results.append({'state':state,'status':'indexed_first_page','newRows':new})
        time.sleep(0.33)
    old_count=len(body['records'])
    body['records']=sorted(indexed.values(),key=lambda r:r['id'])
    body['publicationStatus']='candidate_search_scope_is_not_exhaustive'
    body['incrementalJurisdictionsScanned']=len(done)
    body['coverageWarning']='Combined bounded national keyword searches plus at most first 20 per jurisdiction. Some years, sessions and bills absent; original state record controls.'
    if not len(body['records'])<=1200:
        raise RuntimeError('Incremental bill index exceeded record storage cap')
    render=json.dumps(body,indent=2,ensure_ascii=False)+'\n'
    if len(render.encode())>850000:
        raise RuntimeError('Incremental state bill index exceeded byte cap; prior data retained')
    check={'schema':'power-atlas.state-redistricting-query-coverage.v1',
           'status':'partial_keyword_page_one_not_complete',
           'provider':'https://billcommons.org/docs/api',
           'jurisdictionsTotal':len(STATES),
           'jurisdictionsScanned':len(done),
           'jurisdictions':done,
           'attemptCounts':attempts,
           'sourceFailures':failures,
           'latestBatch':results,
           'remainingJurisdictions':[s for s in STATES if s not in done],
           'meaning':'First-page search coverage only. No source implies zero bills or no state-level redistricting activity.'}
    checkpoint_render=json.dumps(check,indent=2,ensure_ascii=False)+'\n'
    for path,text in ((BILLS,render),(CHECKPOINT,checkpoint_render)):
        if not path.exists() or path.read_text(encoding='utf-8')!=text:
            path.write_text(text,encoding='utf-8')
    print('State keyword first-page checks:',len(done),'/',len(STATES),
          'new bill candidates:',len(indexed)-old_count,
          'batch:',results)

if __name__=='__main__':
    run()
