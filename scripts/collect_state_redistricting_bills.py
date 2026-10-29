"""Bounded, keyless state redistricting bill and recorded-vote collector.

Source: Bill Commons public REST API; source records from official state
legislatures and Open States, with attribution depending on each bill.
Fetch search metadata only for <=6 terms, <=40 returned per term.
Enrich at most 10 strongly topic-matched bills with recorded vote tallies.
Do NOT claim this is exhaustive nationwide coverage or mapmaking causality.
No personal details, donor records, text documents, or unlicensed bulk mirrors.
"""
from __future__ import annotations
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError,URLError
from pathlib import Path
import json
import re
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/legislation/state-redistricting-bills.json'
VOTES=ROOT/'data/legislation/state-redistricting-votes.json'
BASE='https://api.billcommons.org/api/v1'
TERMS=('redistricting','gerrymandering','reapportionment','congressional district')
TOPIC=('redistrict','gerrymander','reapportion','congressional district')
MAX_REQUEST_BYTES=250_000
MAX_VOTE_BILLS=4
MAX_SEARCH_BILLS=240

def get(url):
    req=Request(url,headers={'User-Agent':'PowerAtlasPublicResearch/1.0 (source-linked civic research)',
                             'Accept':'application/json'})
    with urlopen(req,timeout=10) as response:
        if response.status!=200:
            raise RuntimeError('Public API returned non-200')
        payload=response.read(MAX_REQUEST_BYTES+1)
        if len(payload)>MAX_REQUEST_BYTES:
            raise RuntimeError('Public API response exceeds byte limit')
    return json.loads(payload)

def classify(title):
    t=title.lower()
    return 'redistricting_specific_title' if any(x in t for x in TOPIC) else 'keyword_search_candidate_unverified'

def jurisdictions():
    mapped={}
    for page in (1,2):
        d=get(BASE+'/jurisdictions?'+urlencode({'per_page':50,'page':page}))
        rows=d.get('data')
        if not isinstance(rows,list):raise RuntimeError('Unexpected jurisdiction schema')
        for r in rows:
            code=str(r.get('abbreviation') or '').upper()
            uid=str(r.get('id') or '')
            if re.fullmatch(r'[A-Z]{2}',code) and uid:
                mapped[uid]=code
        if d.get('pagination',{}).get('total_pages',1)<=page:break
    if len(mapped)<50:
        raise RuntimeError('Fewer than 50 jurisdictions returned; source coverage uncertain')
    return mapped

def collect():
    codes=jurisdictions()
    bills={}
    query_stats=[]
    successful_searches=0
    for term in TERMS:
        url=BASE+'/search?'+urlencode({'q':term,'per_page':40,'page':1})
        try:
            response=get(url)
        except HTTPError as exc:
            if exc.code in (401,403,429):
                raise RuntimeError('Source access or rate restriction HTTP '+str(exc.code)+'; existing corpus preserved') from exc
            query_stats.append({'query':term,'status':'http_error','httpCode':exc.code})
            continue
        except (TimeoutError,URLError,OSError,RuntimeError) as exc:
            query_stats.append({'query':term,'status':'temporary_network_failure','errorType':type(exc).__name__})
            continue
        successful_searches+=1
        rows=response.get('data')
        if not isinstance(rows,list):
            raise RuntimeError('Unexpected public state search records')
        for r in rows:
            uid=str(r.get('id') or '')
            code=codes.get(str(r.get('jurisdiction_id') or ''))
            source=str(r.get('source_url') or '')
            title=' '.join(str(r.get('title') or '').split())[:250]
            number=str(r.get('identifier') or '')[:45]
            if not uid or not code or not source.startswith('https://') or not title or not number:
                continue
            if not re.fullmatch(r'[A-Fa-f0-9-]{36}',uid):
                continue
            current=bills.get(uid)
            if current:
                continue
            bills[uid]={
                'id':'state-bill-'+uid,'billUuid':uid,'state':code,
                'identifier':number,'title':title,
                'issueClass':classify(title),
                'latestActionDate':str(r.get('latest_action_date') or '')[:18],
                'latestAction':str(r.get('latest_action_text') or '')[:180],
                'status':str(r.get('status') or 'not_indexed')[:70],
                'source':source,
                'sourceIndex':'https://billcommons.org/',
                'retrievalScope':'top_40_per_query_no_complete_jurisdiction_census',
                'reviewStatus':'third_party_index_official_source_review_required'
            }
        query_stats.append({'query':term,'rowsReturned':len(rows),
                            'totalReported':response.get('pagination',{}).get('total'),
                            'pagesQueried':1})
        time.sleep(0.17)
    if successful_searches<1:
        raise RuntimeError('All bounded state bill source searches failed; retained previous output')
    if not 1<=len(bills)<=MAX_SEARCH_BILLS:
        raise RuntimeError('Unexpected state legislative candidate volume '+str(len(bills)))
    # Capture explicit recorded roll-call tallies for bills with a directly
    # redistricting-related title. Do not infer any legislator's vote by name.
    votes=[]
    selected=sorted(
        (b for b in bills.values() if b['issueClass']=='redistricting_specific_title'),
        key=lambda b:(b['state'],b['identifier'])
    )[:MAX_VOTE_BILLS]
    attempts=[]
    for item in selected:
        uid=item['billUuid']
        url=BASE+'/bills/'+uid+'/votes'
        try:
            details=get(url)
        except HTTPError as exc:
            if exc.code in (401,403,429):
                attempts.append({'billId':item['id'],'status':'deferred_rate_or_auth_restriction','http':exc.code})
                break
            attempts.append({'billId':item['id'],'status':'HTTP '+str(exc.code)})
            continue
        except (TimeoutError,URLError,OSError,RuntimeError) as exc:
            attempts.append({'billId':item['id'],'status':'detail_unavailable','errorType':type(exc).__name__})
            continue
        if not isinstance(details,list):
            attempts.append({'billId':item['id'],'status':'unexpected_schema'})
            continue
        for v in details[:12]:
            if not isinstance(v,dict):continue
            vid=str(v.get('id') or '')
            if not re.fullmatch(r'[A-Fa-f0-9-]{36}',vid):continue
            counts={k:v.get(k) for k in ('yes_count','no_count','other_count')
                    if isinstance(v.get(k),int) and v.get(k)>=0}
            if counts and not any(value>0 for value in counts.values()):
                # Zero-coded placeholders in upstream vote fixtures may mean
                # missing tallies; do not present these as 0-to-0 roll calls.
                counts={}
            record={
                'id':'state-roll-'+vid,
                'billId':item['id'],'state':item['state'],
                'identifier':item['identifier'],
                'motion':str(v.get('motion_text') or '')[:155],
                'classification':str(v.get('motion_classification') or '')[:70],
                'date':str(v.get('start_date') or '')[:20],
                'result':str(v.get('result') or '')[:75],
                'counts':counts,
                'tallyStatus':'reported_positive_tally' if counts else 'not_reported_or_unverifiable',
                'source':item['source'],
                'sourceIndex':url,
                'reviewStatus':'secondary_recorded_state_rollcall_needs_official_verification',
                'limitations':'Only aggregate member voting counts; incomplete bill sample; official source controls'
            }
            votes.append(record)
        attempts.append({'billId':item['id'],'status':'read','returnedVoteRows':len(details)})
        time.sleep(0.17)
    # Preserve old record-level observations if no new vote data returned.
    existing_votes=json.loads(VOTES.read_text(encoding='utf-8'))['records'] if VOTES.exists() else []
    merged_votes={v['id']:v for v in existing_votes}
    merged_votes.update({v['id']:v for v in votes})
    bill_data={
        'schema':'power-atlas.state-redistricting-bill-candidates.v1',
        'publicationStatus':'search_candidate_needs_primary_source_verification',
        'provider':'https://billcommons.org/docs/api',
        'attribution':'Bill Commons (official state/Open States and possibly optional CC-BY-4.0 LegiScan, record-specific source licensing must be checked before reuse); metadata and source references only',
        'coverageWarning':'First 40 results per query; not complete nationwide or state legislative coverage. An empty result is not evidence that a bill does not exist.',
        'searches':query_stats,'successfulSearches':successful_searches,'jurisdictionsLookupCount':len(codes),
        'records':sorted(bills.values(),key=lambda x:x['id'])
    }
    vote_data={
        'schema':'power-atlas.state-redistricting-bill-rollcalls.v1',
        'publicationStatus':'partial_secondary_vote_tallies_need_official_review',
        'provider':'https://billcommons.org/docs/api',
        'sourceScope':'Only first ten strongly titled bill candidates; tallies only and source URLs; zero rows does not mean no votes occurred',
        'attempts':attempts,
        'warning':'Zero-coded unverified upstream tallies are treated as unavailable, never as confirmed zero votes.',
        'records':sorted(merged_votes.values(),key=lambda x:x['id'])
    }
    rendered_bills=json.dumps(bill_data,indent=2,ensure_ascii=False)+'\n'
    rendered_votes=json.dumps(vote_data,indent=2,ensure_ascii=False)+'\n'
    if len(rendered_bills.encode())>240000 or len(rendered_votes.encode())>200000:
        raise RuntimeError('Source-indexed outputs exceed compact storage caps')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    for p,text in ((OUT,rendered_bills),(VOTES,rendered_votes)):
        if not p.exists() or p.read_text(encoding='utf-8')!=text:
            p.write_text(text,encoding='utf-8')
    print('Indexed bills:',len(bills),'redistricting title matches:',
          sum(x['issueClass']=='redistricting_specific_title' for x in bills.values()),
          'vote rows:',len(merged_votes),'state codes:',len({b['state'] for b in bills.values()}))

if __name__=='__main__':
    collect()
