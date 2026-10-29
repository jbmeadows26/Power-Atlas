"""Deterministic source/evidence reconciliation for Power Atlas static deployment.

No database needed at runtime. Staged candidates never become verified bills
or certified roll calls just because a provider returned rows.
Official source reconciliation is a separate, future signed-off action.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import json
import re

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
OUT=DATA/'reconciliation'
VOTE_STATUSES=('unverified','partially_parsed','certified_tally')
COVERAGE_STATUSES=('pending','page1_complete','full_sweep')
LEGAL_STANDARDS=(
    {'id':'VRA_Sec2_Milligan_2023','decisionDate':'2023-06-08',
     'source':'https://www.supremecourt.gov/docket/docketfiles/html/public/21-1086.html'},
    {'id':'VRA_Sec2_Callais_2026','decisionDate':'2026-04-29',
     'source':'https://www.supremecourt.gov/docket/docketfiles/html/public/24-109.html'}
)

def read(path):
    return json.loads((DATA/path).read_text(encoding='utf-8'))

def write(path, doc):
    OUT.mkdir(parents=True,exist_ok=True)
    dest=OUT/path
    text=json.dumps(doc,indent=2,ensure_ascii=False)+'\n'
    if not dest.exists() or dest.read_text(encoding='utf-8')!=text:
        dest.write_text(text,encoding='utf-8')

def date_standard(date):
    """Historical reference only. Not a legal holding for an individual map."""
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(date or '')):
        return None
    if date >= '2026-04-29':
        return 'VRA_Sec2_Callais_2026'
    if date >= '2023-06-08':
        return 'VRA_Sec2_Milligan_2023'
    return None

def main():
    source=read('legislation/state-redistricting-bills.json')
    votes=read('legislation/state-redistricting-votes.json')
    progress=read('legislation/state-redistricting-jurisdictions.json')
    elections=read('elections/official-source-index.json')
    all_states=sorted({r['state'] for r in elections['records']})
    if len(all_states)!=51 or progress.get('jurisdictionsTotal')!=51:
        raise ValueError('National state election authority/search jurisdiction mismatch')
    bills=source['records']
    vote_rows=votes['records']
    if len({b['id'] for b in bills}) != len(bills):
        raise ValueError('Duplicate staged source bill ID')
    if len({v['id'] for v in vote_rows}) != len(vote_rows):
        raise ValueError('Duplicate staged roll-call ID')
    bill_ids={b['id'] for b in bills}
    # Staging deliberately excludes unlicensed full texts, contact details and names of donors.
    staging={
        'schema':'power-atlas.raw-ingestion.v1',
        'publicationStatus':'raw_candidates_not_production_bills',
        'counts':{'rawLegislativeBillCandidates':len(bills),
                  'topicKeywordMatches':sum(b.get('issueClass')=='redistricting_specific_title' for b in bills)},
        'records':[
            {'id':b['id'],'domain':'legislation','sourceRecordId':b.get('billUuid'),
             'jurisdictionId':b['state'],'sourceURL':b['source'],
             'topic':'redistricting' if b.get('issueClass')=='redistricting_specific_title' else 'keyword_candidate',
             'stage':'raw_ingestion','verificationStatus':'raw_candidate',
             'reportedStatus':b.get('status'),
             'statusIsVerified':False,
             'sourceTitle':b['title']}
            for b in bills]
    }
    write('raw-legislative-ingestion.json',staging)
    # State index: ONLY a first page does not imply exhaustive state coverage.
    pages=progress.get('jurisdictions',{})
    if not isinstance(pages,dict) or not set(pages).issubset(all_states):
        raise ValueError('Jurisdiction search progress contains unknown codes')
    rows=[]
    tasks=[]
    for state in all_states:
        record=pages.get(state,{})
        indexed=int(record.get('searchPage',0) or 0)
        perpage=int(record.get('perPage',20) or 20)
        total=record.get('totalMatchesReported')
        try:total=int(total) if total is not None else None
        except (TypeError,ValueError):total=None
        if indexed and indexed!=1:
            raise ValueError('Unexpected non-first-page search coverage: '+state)
        if indexed and perpage<1:
            raise ValueError('Bad perPage for '+state)
        state_status='page1_complete' if indexed else 'pending'
        if state_status not in COVERAGE_STATUSES:raise ValueError('Invalid coverage status')
        indexed_count=int(record.get('newIndexedRecords',0) or 0)
        row={
            'jurisdictionId':state,
            'provider':'Bill Commons','query':'redistricting',
            'searchDepth':1 if indexed else 0,
            'pageIndexed':indexed,'perPage':perpage,
            'reportedTotalMatches':total,
            'coverageStatus':state_status,
            'sourceStatus':'page_one_indexed_not_certified' if indexed else 'pending_first_page',
            'newUniqueRecordsFromPageOne':indexed_count,
            'recordCountIsNotLegislativeTotal':True,
            'source':'https://billcommons.org/docs/api'
        }
        rows.append(row)
        # A '0 hits' page can be complete for this single exact query,
        # but never establishes complete all-terms legislative coverage.
        if not indexed:
            tasks.append({'id':f'state-bills-{state}-page1','jurisdictionId':state,
                          'domain':'state_legislation','query':'redistricting',
                          'nextPage':1,'priority':'baseline_gap',
                          'reason':'No successful page-one query indexed',
                          'state':'pending'})
        elif total is None or total > perpage:
            tasks.append({'id':f'state-bills-{state}-page2','jurisdictionId':state,
                          'domain':'state_legislation','query':'redistricting',
                          'nextPage':2,'priority':'pagination_gap',
                          'reason':'First page insufficient or reported matches unknown',
                          'state':'pending'})
    summary={
        'schema':'power-atlas.search-coverage.v1',
        'publicationStatus':'page_coverage_only_no_exhaustive_state_sweep',
        'enums':list(COVERAGE_STATUSES),
        'jurisdictionsTotal':51,
        'page1Complete':sum(x['coverageStatus']=='page1_complete' for x in rows),
        'pendingFirstPage':sum(x['coverageStatus']=='pending' for x in rows),
        'fullSweep':0,
        'searchDepthMeaning':'Depth per single keyword/state combination, not complete legislative history',
        'records':rows
    }
    write('search-coverage.json',summary)
    write('ingestion-queue.json',{
        'schema':'power-atlas.ingestion-queue.v1',
        'publicationStatus':'queued_not_claimed_scheduled',
        'pendingBaselineStates':[x['jurisdictionId'] for x in tasks if x['priority']=='baseline_gap'],
        'count':len(tasks),'tasks':tasks
    })
    state_roll_rows=[]
    verified=[]
    for v in vote_rows:
        if v['billId'] not in bill_ids:
            raise ValueError('Orphaned vote reference: '+v['id'])
        counts=v.get('counts') or {}
        if not isinstance(counts,dict):raise ValueError('Bad vote tally structure')
        yea,nay,other=(counts.get('yes_count'),counts.get('no_count'),counts.get('other_count'))
        numeric=all(isinstance(q,int) and not isinstance(q,bool) and q>=0 for q in (yea,nay,other))
        # A complete secondary-source numeric tally is not yet independently
        # matched to an official state chamber's recorded division.
        status='partially_parsed' if numeric else 'unverified'
        if status not in VOTE_STATUSES:raise ValueError('Bad vote status')
        item={
            'id':v['id'],'billId':v['billId'],'jurisdictionId':v['state'],
            'motion':v.get('motion') or 'Motion not indexed',
            'date':v.get('date'),'voteVerificationStatus':status,
            'tally':{'yea':yea,'nay':nay,'abstainOrOther':other} if numeric else None,
            'officialTallyVerified':False,
            'officialSource':v['source'],
            'secondaryIndexURL':v.get('sourceIndex'),
            'reviewStatus':'official_state_chamber_rollcall_crosscheck_required',
            'evidenceMeaning':'Legislative roll call, never a statewide election vote or campaign finance transaction'
        }
        if item['voteVerificationStatus']=='certified_tally':
            verified.append(item)
        state_roll_rows.append(item)
    write('rollcall-staging.json',{
        'schema':'power-atlas.rollcall-staging.v1',
        'publicationStatus':'no_official_aggregate_tallies_yet',
        'voteVerificationEnum':list(VOTE_STATUSES),
        'counts':{'unverified':sum(x['voteVerificationStatus']=='unverified' for x in state_roll_rows),
                  'partially_parsed':sum(x['voteVerificationStatus']=='partially_parsed' for x in state_roll_rows),
                  'certified_tally':len(verified)},
        'records':state_roll_rows
    })
    # A secondary-index 'pass' result is NOT sufficient to promote a bill
    # into the authoritative production roll_calls/bills entity sets.
    write('verified-production.json',{
        'schema':'power-atlas.verified-production.v1',
        'publicationStatus':'official_primary_source_review_required',
        'productionBills':[],
        'certifiedLegislativeRollCalls':[],
        'explanation':'Production remains empty until bill text/status and each motion, chamber, yea/nay/abstain count are individually verified with the authoritative state records.'
    })
    official_entries=[]
    for x in elections['records']:
        official_entries.append({
            'jurisdictionId':x['state'],
            'electionOfficeURL':x['electionOfficeURL'],
            'certificationStatus':'pending_download',
            'certifiedCanvassURL':None,
            'reconciledContestCount':0,
            'dataDomain':'election_results',
            'reviewStatus':'official_office_link_not_an_election_canvass'
        })
    write('official-election-sources.json',{
        'schema':'power-atlas.official-election-source-status.v1',
        'publicationStatus':'state_certification_directory_not_votecounts',
        'counts':{'jurisdictions':len(official_entries),
                  'pendingDownload':len(official_entries),
                  'reconciledOfficial':0},
        'records':official_entries
    })
    # Legal framework stores BOTH map drawing date and adjudication date when
    # available. The latter controls which precedent is cited in a court
    # analysis, subject to actual scope/retroactivity/legal review.
    scotus=read('research.json')['records']
    legal=[]
    for c in scotus:
        if c['id'].startswith('scotus-') and c.get('date'):
            legal.append({
                'caseId':c['id'],'caseName':c['title'],
                'decisionDate':c['date'],
                'historicalFrameworkMarker':date_standard(c['date']),
                'frameworkAtDrawing':None,
                'frameworkAtAdjudication':date_standard(c['date']),
                'mapDrawingDate':None,
                'legalApplicability':'requires_case_specific_review_no_automated_retroactivity',
                'source':c['source']
            })
    write('legal-framework-timeline.json',{
        'schema':'power-atlas.temporal-legal-framework.v1',
        'publicationStatus':'legal_research_markers_only_not_risk_scores',
        'frameworks':list(LEGAL_STANDARDS),
        'reviewWarning':'A 2022 map challenged in 2026 can be affected by Callais; selecting a framework solely from the drawing date is inadequate. Retain claim type, timing, procedural posture, higher-court decision dates, and actual legal holdings.',
        'cases':legal
    })
    write('domain-integrity.json',{
        'schema':'power-atlas.domain-integrity.v1',
        'productionStatus':'reconciliation_staging_no_live_database_migration',
        'domainDefinitions':{
          'election_results':{'table':'election_returns','countMeaning':'certified votes in a particular election contest','crossDomainVoteAggregationAllowed':False},
          'legislative_roll_calls':{'table':'roll_calls','countMeaning':'recorded votes on a legislative motion','crossDomainVoteAggregationAllowed':False},
          'campaign_finance':{'table':'finance_transactions','countMeaning':'reported transaction amount in USD','crossDomainVoteAggregationAllowed':False}},
        'summary':{
          'billCandidatesStaged':len(bills),
          'redistrictingTitleMatches':staging['counts']['topicKeywordMatches'],
          'legislativeVoteReferencesStaged':len(state_roll_rows),
          'legislativeVotesWithPartiallyParsedTallies':sum(x['voteVerificationStatus']=='partially_parsed' for x in state_roll_rows),
          'officiallyVerifiedLegislativeTallies':len(verified),
          'candidateBillsPromotedToProduction':0,
          'electionDirectoryPendingCanvasses':len(official_entries),
          'jurisdictionPageOneCompleted':summary['page1Complete'],
          'jurisdictionFirstPagePending':summary['pendingFirstPage'],
          'jurisdictionFullSearchSweeps':summary['fullSweep']
        }
    })
    print('Reconciliation: staged bill candidates',len(bills),
          'roll references',len(state_roll_rows),'official verified',len(verified),
          'jurisdiction first page',summary['page1Complete'],'pending',summary['pendingFirstPage'])

if __name__=='__main__':
    main()
