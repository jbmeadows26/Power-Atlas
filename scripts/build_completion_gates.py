"""Machine-readable research readiness gate for Power Atlas.
Never infer nationwide completeness from bounded source counts.
This is derived solely from already persisted source files, no paid services.
"""
from pathlib import Path
import json,datetime

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/health/completion-gates.json'

def load(relative):
    p=ROOT/relative
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

def metric(id,description,observed,scope,status,next_work,source=None):
    row={'id':id,'description':description,'observed':observed,
         'scope':scope,'status':status,'nextAction':next_work}
    if source:row['source']=source
    return row

def build():
    c=load('data/coverage.json').get('coverage',{})
    roll=load('data/health/political-authenticity-ci.json')
    pagination=load('data/legislation/state-redistricting-pagination.json')
    bills=load('data/legislation/state-redistricting-jurisdictions.json')
    wa=load('data/legislation/wa-2023-24-rollcalls/source-rollcalls.json')
    if not c:raise RuntimeError('Missing reconciled corpus coverage; no readiness claims allowed')
    wa_rows=wa.get('records',[])
    if wa and (wa.get('publicationStatus')!='official_original_member_rollcall_sample_not_full_biennium'
               or wa.get('historicalSessionComplete') is not False
               or wa.get('allStateRollCallsComplete') is not False
               or wa.get('officialSourceService')!='https://wslwebservices.leg.wa.gov/LegislationService.asmx/GetRollCalls'
               or wa.get('rollCalls')!=len(wa_rows)
               or wa.get('memberVoteRows')!=sum(len(row.get('memberVotes',[])) for row in wa_rows)):
        raise ValueError('WA source sample has invalid provenance or counts; do not publish misleading readiness')
    wa_count=len(wa_rows) if wa else 0
    gates=[
        metric('federal_house_2025_150_roll_window',
               'Official House roll calls in requested 1–150 pilot window',
               roll.get('officialRolls',0),
               'bounded_2025_roll_window_150',
               'complete_bounded_primary_source_window' if roll.get('officialRolls')==150 else 'partial_source_window',
               'Extend to additional years and chambers; identify substantive map-related votes separately',
               'https://clerk.house.gov/evs/2025/'),
        metric('state_bill_page_one_keyword',
               'State/DC first page of the single redistricting keyword search',
               c.get('stateBillFirstPageJurisdictions',0),
               '51_jurisdictions_first_page_one_keyword',
               'complete_limited_first_page_only' if c.get('stateBillFirstPageJurisdictions')==51 else 'partial',
               'Expand pagination, dates, synonyms and official bill adjudication',
               'https://billcommons.org/docs/api'),
        metric('state_bill_extra_keyword_pages',
               'Additional state redistricting keyword search pages persisted',
               pagination.get('additionalPagesIndexed',0),
               'more_than_first_page_of_same_keyword_only',
               'partial_keyword_pagination',
               'Continue free source-compliant bounded pagination and record gaps',
               'https://billcommons.org/docs/api'),
        metric('state_bill_full_history',
               'States/DC with verified exhaustive historical legislative redistricting census',
               c.get('stateBillFullSweepJurisdictions',0),
               '51_jurisdictions_multi_term_multi_session',
               'partial_not_exhaustive',
               'Reconcile official legislative indexes and all relevant sessions',
               'https://billcommons.org/docs/api'),
        metric('state_certified_election_canvasses',
               'Official state/DC canvass totals actually downloaded and reconciled',
               c.get('officialStateCanvassesRetrieved',0),
               '51_state_DC_authorities',
               'incomplete',
               'Retrieve certified state election contest/year/office totals from the 51 indexed authority URLs',
               'https://www.fec.gov/introduction-campaign-finance/how-to-research-public-records/state-election-offices/'),
        metric('state_campaign_finance',
               'Nationwide state-level donor to PAC/candidate/recipient transaction coverage',
               0,
               'all_states_multi_cycle',
               'not_established',
               'Prioritize licensed official state election campaign finance exports, with privacy minimization'),
        metric('official_state_rollcalls',
               'State bill aggregate tallies independently verified against an official chamber source',
               c.get('rollcallOfficialVerifiedTallies',0),
               'national_state_redistricting_votes',
               'partial_sample_not_member_ballot_census',
               'Obtain official chamber roll-call member votes and dates, not merely secondary bill search metadata'),
        metric('official_wa_2023_24_member_rollcall_sample',
               'Official WA member-level legislative votes for 42 sampled 2023–24 bills; not a redistricting vote census',
               wa_count,
               'WA_2023_24_42_requested_bills_21_with_votes',
               'complete_bounded_primary_source_sample' if wa_count and wa.get('billsRequested')==42 else 'not_established',
               'Extend only with official source access and explicit topic tagging; never merge general WA votes into redistricting tallies',
               'https://wslwebservices.leg.wa.gov/LegislationService.asmx/GetRollCalls'),
        metric('verified_committee_financial_transfers',
               'Individual, source-supported committee-to-committee transfer records',
               c.get('paymentRows',0),
               'federal_and_state_financial_edges',
               'not_proven_by_aggregates',
               'Connect FEC itemized disbursements or official state filings to legally identified recipients'),
        metric('official_fec_pac_party_cycle_summaries',
               'Official FEC PAC/party election-cycle financial summary rows',
               c.get('FECpacPartyCycleSummaryRows',0),
               'already_indexed_committees_2024_2026',
               'completed_bounded_cycle_summary_source',
               'Keep totals separate from recipient transfers and map influence claims',
               'https://www.fec.gov/campaign-finance-data/pac-and-party-summary-file-description/'),
        metric('nationwide_lower_court_case_lifecycle',
               'Completed nationwide election-map litigation docket, motion, judgment and appeal census',
               None,'federal_and_state_trial_appellate_courts',
               'not_verified_nationwide',
               'Connect accessible official dockets or CourtListener records with final dispositions and dates'),
        metric('state_judicial_selection',
               'Verified nationwide state judicial selection, retention, election and appointment chain',
               None,'all_state_judiciaries_history',
               'not_verified_nationwide',
               'Collect official state judicial records, term dates, election commissions and nominating actors'),
        metric('district_legal_maps_history',
               'Source-verified legal redistricting plan histories including superseded, enjoined and enacted maps',
               None,'all_states_all_relevant_plan_eras',
               'not_verified_nationwide',
               'Reconcile official plan geometries, legal effective dates and court-ordered plans to election results'),
        metric('causal_decision_graph',
               'Verified complete actor-to-decision chain linking money, consultation, votes, enactment, lawsuits and electoral effects',
               None,'case_by_case_with_primary_source_temporal_provenance',
               'not_established',
               'Require dated primary sources for each action; graph affiliations are not guilt or causation')
    ]
    blocking=[g['id'] for g in gates if g['status'] in ('incomplete','not_established','not_verified_nationwide','not_proven_by_aggregates','partial_sample_not_member_ballot_census','partial_not_exhaustive')]
    out={
        'schema':'power-atlas.completion-gates.v1',
        'publicationStatus':'source_coverage_audit_not_research_conclusion',
        'asOfDate':datetime.date.today().isoformat(),
        'deadline':'2026-10-30',
        'disposition':'not_nationwide_research_complete' if blocking else 'limited_source_gates_met',
        'foundationalPersistedCounts':{
            'billCandidates':c.get('stateBillCandidateRows',0),
            'officialFECsummaries':c.get('FECpacPartyCycleSummaryRows',0),
            'sourceAttributedRelationships':c.get('relationshipRecords',0),
            'federalCourtAppointments':c.get('federalJudicialAppointments',0)
        },
        'gates':gates,
        'blockingGates':blocking,
        'warning':'This is a static corpus quality assessment. A source collector run marked success does not establish that nationwide records are exhaustive or that gerrymandering, illegal conduct, or motives are proven.'
    }
    encoded=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
    if len(encoded)>23000:raise ValueError('Audit summary exceeds concise storage budget')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=encoded:OUT.write_text(encoded,encoding='utf-8')
    print('Readiness:',out['disposition'],'blocking gates:',len(blocking),'official roll window:',roll.get('officialRolls'))
if __name__=='__main__':
    build()
