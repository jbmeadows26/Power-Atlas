"""Bounded state redistricting search pagination; never extrapolate completeness.

Continue only the already observed 'redistricting' state search, 1-based pages
from the official-link secondary Bill Commons index. Preserve all prior
candidate IDs and checkpoint each page. Max 6 page requests per GitHub run;
don't retry access-denied/rate-limited requests in the same run.
"""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from datetime import date
import json,time

ROOT=Path(__file__).resolve().parents[1]
BILLS=ROOT/'data/legislation/state-redistricting-bills.json'
BASELINE=ROOT/'data/legislation/state-redistricting-jurisdictions.json'
CHECK=ROOT/'data/legislation/state-redistricting-pagination.json'
API='https://api.billcommons.org/api/v1/search'
MAX_PAGES=6
MAX_BYTES=210000
DEADLINE=date(2026,10,30)  # Deadline sprint must not request new pages after this date.
from expand_state_bill_coverage import record

def get(state,page,per_page):
    url=API+'?'+urlencode({'q':'redistricting','jurisdiction':state,'page':page,'per_page':per_page})
    req=Request(url,headers={'User-Agent':'PowerAtlasPublicResearch/1.0 public state legislative index','Accept':'application/json'})
    with urlopen(req,timeout=16) as response:
        if response.status!=200:raise RuntimeError('Public source returned non-200')
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise RuntimeError('Source response exceeds compact bound')
    doc=json.loads(raw)
    if not isinstance(doc.get('data'),list):raise ValueError('Unexpected search schema')
    return doc,url

def main():
    if date.today()>DEADLINE:
        print('October 30 ingestion deadline passed; no further keyword pagination requests or writes.')
        return
    baseline_doc=json.loads(BASELINE.read_text(encoding='utf-8'))
    base=baseline_doc['jurisdictions']
    previous=json.loads(CHECK.read_text(encoding='utf-8')) if CHECK.exists() else {}
    pages=previous.get('pages',{})
    paused=previous.get('paused',{})
    bill_doc=json.loads(BILLS.read_text(encoding='utf-8'))
    by_id={b['id']:b for b in bill_doc['records']}
    scheduled=[]
    for state,entry in sorted(base.items()):
        reported=entry.get('totalMatchesReported')
        per_page=int(entry.get('perPage') or 20)
        if not isinstance(reported,int) or reported<=per_page:continue
        done=pages.get(state,{})
        max_page=min(6,(reported+per_page-1)//per_page)
        for page in range(2,max_page+1):
            if str(page) in done:continue
            if paused.get(state,{}).get('date')==date.today().isoformat():break
            scheduled.append((state,page,per_page,max_page,reported))
            break
    # Larger reported pending states first, then alphabetical; avoid repeating
    # page-1 indexing already completed in all 51 jurisdictions.
    scheduled.sort(key=lambda x:(-x[4],x[0],x[1]))
    scanned=[]
    rate_stop=False
    for state,page,per_page,max_page,reported in scheduled[:MAX_PAGES]:
        try:
            doc,url=get(state,page,per_page)
        except HTTPError as exc:
            paused[state]={'date':date.today().isoformat(),'reason':'rate_or_access_restriction' if exc.code in (401,403,429) else 'HTTP_error','status':exc.code}
            scanned.append({'state':state,'page':page,'status':'HTTP_'+str(exc.code)})
            if exc.code in (401,403,429):
                rate_stop=True
                break
            continue
        except (URLError,TimeoutError,OSError,RuntimeError,ValueError) as exc:
            paused[state]={'date':date.today().isoformat(),'reason':type(exc).__name__}
            scanned.append({'state':state,'page':page,'status':'deferred_network'})
            continue
        rows=doc['data']
        total=doc.get('pagination',{}).get('total')
        # Unknown page size/total drift must not be labeled as exhausted.
        if total is not None and int(total)!=reported:
            paused[state]={'date':date.today().isoformat(),'reason':'source_result_count_drift','previous':reported,'current':total}
            scanned.append({'state':state,'page':page,'status':'count_drift_deferred'})
            continue
        new=0
        for row in rows:
            value=record(row,state,per_page)
            if not value:continue
            if value['id'] not in by_id:
                value['retrievalScope']=f'redistricting_state_keyword_page_{page}_of_up_to_{max_page}'
                by_id[value['id']]=value
                new+=1
        pages.setdefault(state,{})[str(page)]={'rowsReturned':len(rows),'newUniqueRows':new,'source':url,'status':'indexed_keyword_page_not_exhaustive'}
        paused.pop(state,None)
        scanned.append({'state':state,'page':page,'status':'indexed','new':new})
        time.sleep(0.25)
    if len(by_id)>2400:raise RuntimeError('Unexpected candidate bill growth; no changes persisted')
    bill_doc['records']=sorted(by_id.values(),key=lambda b:b['id'])
    # Page-two-plus candidates must update the original first-page checkpoint's
    # persisted counts. Otherwise the corpus contract sees a stale denominator
    # and correctly rejects the new source records before publication.
    by_state={}
    for row in bill_doc['records']:
        state=row.get('state')
        if state in base:
            by_state[state]=by_state.get(state,0)+1
    for state,entry in base.items():
        count=by_state.get(state,0)
        entry['persistedCandidateRows']=count
        if count:
            entry['status']='first_page_indexed_not_exhaustive'
        elif isinstance(entry.get('totalMatchesReported'),int) and entry['totalMatchesReported']>0:
            entry['status']='first_page_matches_reported_no_candidates_persisted'
        else:
            entry['status']='first_page_empty_search_not_no_bills'
    bill_doc['publicationStatus']='candidate_search_not_primary_source_verified'
    bill_doc['paginationStatus']='bounded_extra_pages_of_redistricting_keyword_only'
    bill_body=json.dumps(bill_doc,indent=2,ensure_ascii=False)+'\n'
    if len(bill_body.encode())>1650000:
        raise RuntimeError('Bill index exceeds minimal storage limit; no writes')
    progress={'schema':'power-atlas.state-bill-keyword-pagination.v1',
              'status':'partial_keyword_pagination_not_complete_all_legislation',
              'scope':'Only public redistricting keyword/state results with more matches than page one; many bills, terms and sessions omitted',
              'provider':'https://billcommons.org/docs/api',
              'maxPagesPerRun':MAX_PAGES,
              'pages':pages,'paused':paused,
              'lastRun':scanned,
              'additionalPagesIndexed':sum(len(x) for x in pages.values()),
              'jurisdictionsWithAdditionalPages':sum(bool(x) for x in pages.values()),
              'candidateBillRows':len(by_id),
              'sourceRateStop':rate_stop}
    checkpoint=json.dumps(progress,indent=2,ensure_ascii=False)+'\n'
    baseline_render=json.dumps(baseline_doc,indent=2,ensure_ascii=False)+'\n'
    if not scanned:
        print('No currently eligible pagination tasks. Nothing overwritten.')
    for dest,content in ((BILLS,bill_body),(BASELINE,baseline_render),(CHECK,checkpoint)):
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists() or dest.read_text(encoding='utf-8')!=content:
            dest.write_text(content,encoding='utf-8')
    print('Additional pages:',progress['additionalPagesIndexed'],'rows:',len(by_id),'batch:',scanned)

if __name__=='__main__':
    main()
