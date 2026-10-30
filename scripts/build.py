from pathlib import Path
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
records = {}
relationships = {}

def match_key(row):
    title = re.sub(r',\s*(?:TX|GA|TN|LA|FL|NY|NC|SC)\s*$', '', row['title'], flags=re.I)
    normalized = re.sub(r'[^a-z0-9]+', ' ', title.casefold()).strip()
    # Candidate duplicate only: year must also match; never infer two cases are identical from title alone.
    year = str(row.get('date', ''))[:4]
    return normalized, year

for file in sorted((ROOT / 'data/batches').glob('*.json')):
    doc = json.loads(file.read_text(encoding='utf-8'))
    for row in doc['records']:
        if not row.get('id') or not str(row.get('source', '')).startswith('https://'):
            raise ValueError(f'Invalid record in {file}')
        compact = {k: row[k] for k in (
            'id', 'title', 'state', 'date', 'asOf', 'source', 'status',
            'reviewStatus', 'claimScope', 'court', 'docket', 'disposition', 'secondarySource'
        ) if k in row}
        if not compact.get('status') and not compact.get('reviewStatus'):
            compact['status'] = doc.get('status') or doc.get('publicationStatus') or 'source_indexed_unreviewed'
        if compact.get('date'):
            compact['datePrecision'] = 'year' if re.fullmatch(r'[0-9]{4}', str(compact['date'])) else 'day'
        compact['source_sha256'] = hashlib.sha256(compact['source'].encode()).hexdigest()[:16]
        if compact['id'] in records and records[compact['id']] != compact:
            raise ValueError(f'Conflicting record ID: {compact["id"]}')
        records[compact['id']] = compact
        for link in row.get('candidateLinks', []):
            cid = link.get('candidateId', '')
            if not re.fullmatch(r'[A-Z][0-9]{8}', cid):
                continue
            edge_id = 'fec-edge-' + hashlib.sha256((compact['id'] + ':' + cid).encode()).hexdigest()[:16]
            relationships[edge_id] = {
                'id': edge_id,
                'from': compact['id'],
                'to': 'fec-candidate-' + cid,
                'type': 'reported_candidate_committee_association',
                'source': 'https://api.open.fec.gov/v1/committee/' + compact['id'].removeprefix('fec-') + '/candidates/',
                'reviewStatus': 'official_fec_link_unreviewed'
            }

# Committee membership is a documented relationship, not proof of map control.
committee_file = ROOT / 'data/organizations/redistricting-committees.json'
committee_doc = json.loads(committee_file.read_text(encoding='utf-8')) if committee_file.exists() else {}
committees = committee_doc.get('committees', [])
committee_index = []
for committee in committees:
    committee_index.append({
        'id': committee['id'], 'state': committee['state'],
        'name': committee['name'], 'chamber': committee['chamber'],
        'topic': committee['topic'], 'members': len(committee.get('members', [])),
        'source': committee['source'], 'officialLink': committee.get('officialLink') or '',
        'reviewStatus': committee['reviewStatus']
    })
    for member in committee.get('members', []):
        member_id = str(member.get('personId') or '')
        if not re.fullmatch(r'ocd-person/[A-Za-z0-9-]{20,50}', member_id):
            continue
        key = 'state-committee-edge-' + hashlib.sha256(
            (committee['id'] + '/' + member_id).encode()
        ).hexdigest()[:16]
        relationships[key] = {
            'id': key, 'from': member_id, 'to': committee['id'],
            'type': 'documented_committee_membership', 'role': member.get('role') or 'member',
            'source': committee['source'], 'officialSource': committee.get('officialLink') or '',
            'reviewStatus': 'curated_CC0_state_committee_membership_unreviewed'
        }

# FEC candidate-committee links are direct registration associations, not money transfers.
fec_link_path = ROOT / 'data/finance/fec-candidate-links.json'
fec_link_doc = json.loads(fec_link_path.read_text(encoding='utf-8')) if fec_link_path.exists() else {}
fec_links = fec_link_doc.get('records', [])
for link in fec_links:
    candidate_id = str(link.get('fecCandidateId') or '')
    committee_id = str(link.get('committeeId') or '')
    if not re.fullmatch(r'[HSP][A-Z0-9]{8}', candidate_id) or not re.fullmatch(r'C[0-9]{8}', committee_id):
        continue
    link_id = str(link.get('id') or '')
    edge_id = 'fec-bulk-edge-' + hashlib.sha256(link_id.encode()).hexdigest()[:16]
    relationships[edge_id] = {
        'id': edge_id, 'from': 'fec-candidate-' + candidate_id,
        'to': 'fec-' + committee_id,
        'type': 'FEC_reported_candidate_committee_linkage',
        'designation': link.get('designation') or '',
        'fecElectionYear': link.get('fecYear'),
        'source': link['source'],
        'sourceDetails': 'https://www.fec.gov/campaign-finance-data/candidate-committee-linkage-file-description/',
        'reviewStatus': 'official_FEC_linkage_requires_designation_interpretation'
    }

# Current congressional member -> FEC candidate ID mapping comes from a
# separate CC0 registry, not from the FEC itself; mark crosswalks accordingly.
congress_source_file = ROOT / 'data/people/congress-members.json'
congress_members_source = json.loads(congress_source_file.read_text(encoding='utf-8'))['records'] if congress_source_file.exists() else []
for person in congress_members_source:
    bio = str(person.get('bioguideId') or '')
    if not re.fullmatch(r'[A-Z][0-9]{6}',bio):
        continue
    for candidate_id in person.get('fecCandidateIds', []):
        if not re.fullmatch(r'[HSP][A-Z0-9]{8}', candidate_id):
            continue
        cross_id = 'fec-roster-edge-' + hashlib.sha256((bio+'/'+candidate_id).encode()).hexdigest()[:16]
        relationships[cross_id] = {
            'id': cross_id, 'from': 'bioguide-' + bio,
            'to': 'fec-candidate-' + candidate_id,
            'type': 'CC0_roster_FEC_candidate_id_crosswalk',
            'source': 'https://github.com/unitedstates/congress-legislators',
            'reviewStatus': 'third_party_identity_crosswalk_requires_primary_FEC_confirmation'
        }

# Public legislative sponsorship is an explicit role, not a recorded roll call vote.
federal_bill_path = ROOT / 'data/legislation/federal-bill-candidates.json'
federal_bill_doc = json.loads(federal_bill_path.read_text(encoding='utf-8')) if federal_bill_path.exists() else {}
federal_bills = federal_bill_doc.get('records', [])
for bill in federal_bills:
    sponsor = str(bill.get('sponsorBioguideId') or '')
    if not re.fullmatch(r'[A-Z][0-9]{6}', sponsor):
        continue
    relation_id = 'bill-sponsor-' + hashlib.sha256((bill['id']+'/'+sponsor).encode()).hexdigest()[:16]
    relationships[relation_id] = {
        'id': relation_id, 'from': 'bioguide-'+sponsor, 'to': bill['id'],
        'type': 'source_reported_federal_bill_sponsorship',
        'source': bill['source'],
        'reviewStatus': 'secondary_index_primary_Congressgov_confirmation_pending'
    }

# State bill/vote relationships use Bill Commons as a secondary index.
# Recorded vote edges refer to a specific bill only; no person-level vote inferred.
state_bill_path = ROOT / 'data/legislation/state-redistricting-bills.json'
state_bill_doc = json.loads(state_bill_path.read_text(encoding='utf-8')) if state_bill_path.exists() else {}
state_bill_rows = state_bill_doc.get('records', [])
state_votes_path = ROOT / 'data/legislation/state-redistricting-votes.json'
state_votes_doc = json.loads(state_votes_path.read_text(encoding='utf-8')) if state_votes_path.exists() else {}
state_vote_rows = state_votes_doc.get('records', [])
wa_source_path = ROOT / 'data/legislation/wa-2023-24-rollcalls/source-rollcalls.json'
wa_source_doc = json.loads(wa_source_path.read_text(encoding='utf-8')) if wa_source_path.exists() else {}
wa_source_rows = wa_source_doc.get('records', [])
if wa_source_doc and (
    wa_source_doc.get('publicationStatus') != 'official_original_member_rollcall_sample_not_full_biennium'
    or wa_source_doc.get('historicalSessionComplete') is not False
    or wa_source_doc.get('allStateRollCallsComplete') is not False
    or wa_source_doc.get('rollCalls') != len(wa_source_rows)
    or wa_source_doc.get('memberVoteRows') != sum(len(r.get('memberVotes', [])) for r in wa_source_rows)
):
    raise ValueError('WA official member-vote sample provenance/counts inconsistent')
wa_sample_summary = {
    'state': 'WA', 'biennium': '2023-24',
    'officialMemberRollCalls': len(wa_source_rows),
    'memberVoteRows': wa_source_doc.get('memberVoteRows', 0),
    'billsRequested': wa_source_doc.get('billsRequested', 0),
    'billsWithAnyRollCalls': wa_source_doc.get('billsWithAnyRollCalls', 0),
    'source': wa_source_doc.get('officialSourceService', ''),
    'dataset': 'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/legislation/wa-2023-24-rollcalls/source-rollcalls.json',
    'status': 'official_primary_source_bounded_sample_not_redistricting_or_statewide_census',
    'warning': 'Sampled legislative bills, not a statewide or redistricting roll-call census; individual legislator votes are in the separately attributed official source dataset.'
}
official_spotchecks_path = ROOT / 'data/legislation/official-state-bill-spotchecks.json'
official_spotchecks_doc = json.loads(official_spotchecks_path.read_text(encoding='utf-8')) if official_spotchecks_path.exists() else {}
official_spotcheck_rows = official_spotchecks_doc.get('records', [])
official_arkansas_spotcheck_path = ROOT / 'data/legislation/official-arkansas-redistricting-2021.json'
official_arkansas_spotcheck_doc = json.loads(official_arkansas_spotcheck_path.read_text(encoding='utf-8')) if official_arkansas_spotcheck_path.exists() else {}
official_arkansas_spotcheck_rows = official_arkansas_spotcheck_doc.get('records', [])
official_idaho_commission_path = ROOT / 'data/legislation/official-idaho-commission-redistricting-2021.json'
official_idaho_commission_doc = json.loads(official_idaho_commission_path.read_text(encoding='utf-8')) if official_idaho_commission_path.exists() else {}
official_idaho_commission_rows = official_idaho_commission_doc.get('records', [])
for v in state_vote_rows:
    bill_id = str(v.get('billId') or '')
    vote_id = str(v.get('id') or '')
    if not re.fullmatch(r'state-bill-[A-Fa-f0-9-]{36}', bill_id) or not re.fullmatch(r'state-roll-[A-Fa-f0-9-]{36}', vote_id):
        continue
    edge_id = 'state-vote-edge-' + hashlib.sha256((vote_id+'/'+bill_id).encode()).hexdigest()[:16]
    relationships[edge_id] = {
        'id':edge_id, 'from':vote_id, 'to':bill_id,
        'type':'third_party_indexed_bill_recorded_vote',
        'source':v['source'],
        'reviewStatus':'third_party_rollcall_official_chamber_crosscheck_required'
    }

# Flag likely duplicates for review instead of deleting source-specific records.
seen = {}
for item in sorted(records.values(), key=lambda x: (0 if x['id'].startswith('doj-') and not x['id'].startswith('doj-index') else 1, x['id'])):
    key = match_key(item)
    if key[1] and key in seen:
        item['possibleDuplicateOf'] = seen[key]
    else:
        seen[key] = item['id']

output = {
    'schema': 'power-atlas.compact.v1',
    'publicationStatus': 'review_required',
    'records': sorted(records.values(), key=lambda row: row['id'])
}
path = ROOT / 'data/research.json'
content = json.dumps(output, indent=2, ensure_ascii=False) + '\n'
if not path.exists() or path.read_text(encoding='utf-8') != content:
    path.write_text(content, encoding='utf-8')
edges_path = ROOT / 'data/relationships.json'
edges = {'schema': 'power-atlas.relationships.v1', 'publicationStatus': 'review_required',
         'relationships': sorted(relationships.values(), key=lambda row: row['id'])}
edge_content = json.dumps(edges, indent=2, ensure_ascii=False) + '\n'
if not edges_path.exists() or edges_path.read_text(encoding='utf-8') != edge_content:
    edges_path.write_text(edge_content, encoding='utf-8')
print(f'Validated {len(records)} source-specific records and {len(relationships)} FEC links')

def read_finance(filename):
    file = ROOT / 'data/finance' / filename
    if not file.exists():
        return []
    doc = json.loads(file.read_text(encoding='utf-8'))
    rows = doc.get('records', [])
    if not isinstance(rows, list):
        raise ValueError('Expected finance records array: ' + filename)
    return rows

def read_reconciliation(filename):
    file = ROOT / 'data/reconciliation' / filename
    if not file.exists():
        return {}
    return json.loads(file.read_text(encoding='utf-8'))

reconcile_domain = read_reconciliation('domain-integrity.json')
reconcile_search = read_reconciliation('search-coverage.json')
reconcile_queue = read_reconciliation('ingestion-queue.json')
reconcile_vote = read_reconciliation('rollcall-staging.json')
reconcile_elections = read_reconciliation('official-election-sources.json')
reconcile_legal = read_reconciliation('legal-framework-timeline.json')
source_catalog_path = ROOT / 'data/redistricting/analytics-sources.json'
analytics_catalog = json.loads(source_catalog_path.read_text(encoding='utf-8')) if source_catalog_path.exists() else {}
totals = read_finance('fec-totals.json')
payments = read_finance('fec-disbursements.json')
recipient_aggregates = read_finance('fec-recipient-aggregates.json')
committee_master = read_finance('fec-committee-master.json')
pac_cycle_summaries = read_finance('fec-pac-party-summaries.json')
elections_path = ROOT / 'data/elections/house-summary.json'
house_summary = json.loads(elections_path.read_text(encoding='utf-8'))['records'] if elections_path.exists() else []
representation_path = ROOT / 'data/elections/representation-gaps.json'
representation = json.loads(representation_path.read_text(encoding='utf-8')) if representation_path.exists() else {}
representation_rows = representation.get('records', [])
house_district_path = ROOT / 'data/elections/house-districts.json'
house_district_rows = json.loads(house_district_path.read_text(encoding='utf-8'))['records'] if house_district_path.exists() else []
house_audit_path = ROOT / 'data/health/house-2024-audit.json'
house_2024_audit = json.loads(house_audit_path.read_text(encoding='utf-8')) if house_audit_path.exists() else {}
unopposed_path = ROOT / 'data/elections/house-2024-unopposed.json'
house_unopposed = json.loads(unopposed_path.read_text(encoding='utf-8'))['records'] if unopposed_path.exists() else []
lda_path = ROOT / 'data/lobbying/lda-filings.json'
lobbying = json.loads(lda_path.read_text(encoding='utf-8'))['records'] if lda_path.exists() else []
fjc_file = ROOT / 'data/judiciary/fjc-appointment-index.json'
fjc_index = json.loads(fjc_file.read_text(encoding='utf-8')) if fjc_file.exists() else {}
executive_file = ROOT / 'data/people/state-executives.json'
executives = json.loads(executive_file.read_text(encoding='utf-8'))['records'] if executive_file.exists() else []
state_people_file = ROOT / 'data/people/state-legislators-index.json'
state_people_doc = json.loads(state_people_file.read_text(encoding='utf-8')) if state_people_file.exists() else {}
state_people_index = state_people_doc.get('jurisdictions', [])
state_people_count = state_people_doc.get('totalIndexed', 0)
congress_file = ROOT / 'data/people/congress-members.json'
congress = json.loads(congress_file.read_text(encoding='utf-8'))['records'] if congress_file.exists() else []
map_editions = []
for map_congress,year in [(116,2020),(119,2025)]:
    map_path = ROOT / ('data/geography/districts-' + str(map_congress) + '.geojson')
    if map_path.exists():
        doc = json.loads(map_path.read_text(encoding='utf-8'))
        if doc.get('type') != 'FeatureCollection' or len(doc.get('features',[])) < 435:
            raise ValueError('Unexpected historical Census district map: '+str(map_congress))
        map_editions.append({
            'congress': map_congress, 'censusYear': year,
            'features':len(doc['features']),
            'source':doc['source'],
            'dataset':'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/geography/districts-'+str(map_congress)+'.geojson',
            'status':'generalized_display_geometry_not_legal_map'
        })
official_authority_file = ROOT / 'data/elections/official-source-index.json'
official_authorities = json.loads(official_authority_file.read_text(encoding='utf-8')) if official_authority_file.exists() else {}
official_authority_rows = official_authorities.get('records', [])
state_file = ROOT / 'data/geography/states.json'
states = json.loads(state_file.read_text(encoding='utf-8'))['states'] if state_file.exists() else []
scotus_decisions = [row for row in output['records'] if row['id'].startswith('scotus-') and row.get('docket')]
for decision in scotus_decisions:
    if decision.get('court') != 'Supreme Court of the United States':
        raise ValueError('Unexpected court label in Supreme Court decision index')
    if not re.fullmatch(r'[0-9]{2}-[0-9]{1,5}',decision.get('docket','')):
        raise ValueError('Unexpected Supreme Court docket ID')
    if decision['source'] != 'https://www.supremecourt.gov/docket/docketfiles/html/public/'+decision['docket']+'.html':
        raise ValueError('Supreme Court docket source mismatch')
uncovered = [
    'state_campaign_finance', 'state_roll_calls', 'state_legislative_district_polygons_and_legal_boundary_history',
    'lower_court_litigation_dockets_and_state_cases', 'state_judicial_selection_and_election_outcomes', 'statewide_local_returns_and_official_vote_reconciliation'
]
feed = {
    'schema': 'power-atlas.frontend.v1',
    'publicationStatus': 'review_required',
    'records': output['records'],
    'relationships': edges['relationships'],
    'states': states,
    'officialElectionAuthorities': {'records':official_authority_rows, 'authorityRule': 'State/local election offices certify election returns; this catalog does NOT contain certified vote totals', 'source':'https://www.fec.gov/introduction-campaign-finance/how-to-research-public-records/state-election-offices/'},
    'evidenceReconciliation': {
        'summary': reconcile_domain.get('summary', {}),
        'scope': reconcile_domain.get('productionStatus','unavailable'),
        'searchCoverage': {'jurisdictionsTotal':reconcile_search.get('jurisdictionsTotal',0),
                           'page1Complete':reconcile_search.get('page1Complete',0),
                           'pendingFirstPage':reconcile_search.get('pendingFirstPage',0),
                           'fullSweep':reconcile_search.get('fullSweep',0)},
        'ingestionQueue': {'count':reconcile_queue.get('count',0),
                            'pendingBaselineStates':reconcile_queue.get('pendingBaselineStates',[])},
        'rollcallVerification': reconcile_vote.get('counts',{}),
        'certificationStatus': reconcile_elections.get('counts',{}),
        'legalFrameworks': reconcile_legal.get('frameworks',[]),
        'legalCaseTimeline': reconcile_legal.get('cases',[]),
        'analyticsSourceCatalog': {'sources': len(analytics_catalog.get('sources',[])),
                                   'metrics':len(analytics_catalog.get('metrics',[]))}
    },

    'geography': {'congressionalMapEditions':map_editions, 'comparisonNote':'116th and 119th maps differ by both nationwide apportionment and boundary changes; a shape difference is not a measure of intent.'},
    'organizations': {'stateCommittees': committee_index, 'source': 'https://github.com/openstates/people', 'reviewStatus': 'topic_matching_and_membership_review_required'},
    'judiciary': {'federalAppointments': fjc_index, 'source': 'https://www.fjc.gov/node/7436', 'supremeCourtRedistrictingDecisions': scotus_decisions, 'supremeCourtDocketSource': 'https://www.supremecourt.gov/Docket/docket.aspx', 'scopeNote': 'Selected Supreme Court dispositions only; not a nationwide case docket census or state judicial record.'},
    'people': {'congressMembers': congress, 'stateLegislatorIndex': state_people_index, 'stateExecutives': executives, 'source': 'https://github.com/unitedstates/congress-legislators', 'stateSource': 'https://github.com/openstates/people', 'sourceLicense': 'CC0-1.0', 'reviewStatus': 'third_party_registry_crosscheck_pending'},
    'legislation': {
        'federalBillCandidates': federal_bills,
        'stateRedistrictingBillCandidates': state_bill_rows,
        'stateRedistrictingRecordedVotes': state_vote_rows,
        'officialStateBillSpotchecks': official_spotcheck_rows,
        'officialArkansasHistoricalRedistricting': {
            'records': official_arkansas_spotcheck_rows,
            'publicationStatus': official_arkansas_spotcheck_doc.get('publicationStatus', 'not_collected'),
            'limitations': official_arkansas_spotcheck_doc.get('limits', 'Historical spotchecks are not complete state coverage'),
            'keywordIndexCandidateRows': 0,
            'officialSourceControls': True
        },
        'officialIdahoCommissionPlans': {
            'records': official_idaho_commission_rows,
            'publicationStatus': official_idaho_commission_doc.get('publicationStatus', 'not_collected'),
            'limitations': official_idaho_commission_doc.get('limitations', 'Commission actions are not legislative bills'),
            'keywordIndexBillCandidateRows': 0,
            'officialSourceControls': True
        },
        'officialWashingtonMemberRollcallSample': wa_sample_summary,
        'stateBillSource': 'https://billcommons.org/docs/api',
        'sourceProvider':'https://www.ballotwatch.io/developers',
        'scopeNote':'Keyword search of public bill titles and secondary-source sponsor IDs. Not exhaustive. No recorded voting outcomes implied.'
    },
    'elections': {'houseStateYears': house_summary, 'representationByStateYear': representation_rows, 'representationMetric': 'Descriptive two-party seat share minus vote share; not a gerrymandering or fairness score', 'house2024KeyAudit': house_2024_audit, 'house2024UnopposedStatusOnly': house_unopposed, 'source': 'https://doi.org/10.7910/DVN/IG0UN2', 'limitations': 'Two-party totals are not gerrymandering scores; compare only within equal reporting and mapping rules.'},
    'lobbying': {'filings': lobbying, 'attribution': 'US Senate Office of Public Records: cannot vouch for analyses after retrieval'},
    'finance': {
        'committeeTotals': totals,
        'committeePayments': payments,
        'committeeRecipientAggregates': recipient_aggregates,
        'candidateCommitteeLinks': {'count':len(fec_links),'cycles': fec_link_doc.get('sources', {}), 'dataset': 'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/finance/fec-candidate-links.json'},
        'committeeMaster': {'count':len(committee_master), 'dataset':'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/finance/fec-committee-master.json'},
        'pacCycleSummaries': {'count':len(pac_cycle_summaries),'dataset':'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/finance/fec-pac-party-summaries.json', 'scope':'FEC official aggregated PAC/party summaries for listed committee IDs only; not transfers to named recipients'}
    },
    'coverage': {
        'sourceIndexedRecords': len(records),
        'rawLegislativeBillCandidatesStaged':reconcile_domain.get('summary',{}).get('billCandidatesStaged',0),
        'rollcallOfficialVerifiedTallies':reconcile_domain.get('summary',{}).get('officiallyVerifiedLegislativeTallies',0),
        'rollcallPartiallyParsedTallies':reconcile_domain.get('summary',{}).get('legislativeVotesWithPartiallyParsedTallies',0),
        'stateBillFirstPageJurisdictions':reconcile_search.get('page1Complete',0),
        'stateBillFullSweepJurisdictions':reconcile_search.get('fullSweep',0),
        'stateBillPendingFirstPageJurisdictions':reconcile_search.get('pendingFirstPage',0),
        'electionAuthorityCanvassesPending':reconcile_elections.get('counts',{}).get('pendingDownload',0),
        'legalFrameworksVersioned':len(reconcile_legal.get('frameworks',[])),
        'redistrictingAnalyticsSourcesIndexed':len(analytics_catalog.get('sources',[])),

        'relationshipRecords': len(relationships),
        'FECcandidateCommitteeLinks': len(fec_links),
        'FECcommitteeMasterRows': len(committee_master),
        'FECpacPartyCycleSummaryRows': len(pac_cycle_summaries),
        'stateCommitteeRows': len(committees),
        'stateCommitteeMembershipEdges': sum(len(c.get('members', [])) for c in committees),
        'committeeTotalRows': len(totals),
        'paymentRows': len(payments),
        'recipientAggregateRows': len(recipient_aggregates),
        'stateSourceReferences': len(states),
        'officialStateElectionAuthorityLinks': len(official_authority_rows),
        'officialStateCanvassesRetrieved': sum(bool(row.get('stateCertifiedVoteTotalsRetrieved')) for row in official_authority_rows),
        'congressionalMapEditions': len(map_editions),
        'congressMemberRows': len(congress),
        'stateLegislatorRows': state_people_count,
        'stateExecutiveRows': len(executives),
        'federalBillCandidateRows': len(federal_bills),
        'stateBillCandidateRows': len(state_bill_rows),
        'officialStateBillSpotcheckRows': len(official_spotcheck_rows),
        'officialArkansasHistoricalSpotcheckRows': len(official_arkansas_spotcheck_rows),
        'officialIdahoCommissionPlanRows': len(official_idaho_commission_rows),
        'stateRedistrictingTitleMatches': sum(r.get('issueClass')=='redistricting_specific_title' for r in state_bill_rows),
        'stateRecordedVoteRows': len(state_vote_rows),
        'officialStateMemberRollcallSampleRows': len(wa_source_rows),
        'officialStateMemberBallotSampleRows': wa_source_doc.get('memberVoteRows', 0),
        'federalBillRedistrictingTitleMatches': sum(r['issueClass']=='redistricting_specific_title' for r in federal_bills),
        'federalBillSponsorEdges': sum(bool(re.fullmatch(r'[A-Z][0-9]{6}',str(r.get('sponsorBioguideId') or ''))) for r in federal_bills),
        'federalJudicialAppointments': fjc_index.get('appointmentRecords', 0),
        'supremeCourtRedistrictingDecisions': len(scotus_decisions),
        'stateLegislatorJurisdictions': len(state_people_index),
        'lobbyingFilingRows': len(lobbying),
        'houseStateYearRows': len(house_summary),
        'representationStateYearRows': len(representation_rows),
        'representationComparableOnIndexedReturns': sum(bool(row.get('comparableOnIndexedReturns')) for row in representation_rows),
        'houseDistrictYearRows': len(house_district_rows),
        'house2024VoteDistrictRows': sum(row.get('year')==2024 for row in house_district_rows),
        'house2024AccountedForDistrictKeys': house_2024_audit.get('accountedForDistrictKeys'),
        'house2024MissingDistrictKeys': house_2024_audit.get('missingCount'),
        'house2024OfficialUnopposedStatusRows': len(house_unopposed),
        'uncovered': uncovered,
        'warning': 'Index counts are not reviewed unique-case or influence counts'
    }
}
feed_path = ROOT / 'data/app-feed.json'
feed_content = json.dumps(feed, ensure_ascii=False, indent=2) + '\n'
if not feed_path.exists() or feed_path.read_text(encoding='utf-8') != feed_content:
    feed_path.write_text(feed_content, encoding='utf-8')
coverage_file = ROOT / 'data/coverage.json'
coverage_body = json.dumps({
    'schema': 'power-atlas.coverage.v1',
    'publicationStatus': 'mixed_source_indexed_coverage_not_completeness',
    'coverage': feed['coverage'],
    'relationshipTypes': {
        typ: sum(1 for rel in relationships.values() if rel.get('type') == typ)
        for typ in sorted({rel['type'] for rel in relationships.values()})
    },
    'dataset': 'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/app-feed.json',
    'warning': 'Counts represent persisted indexed records, not legal determinations, influence findings or all nationwide sources'
}, ensure_ascii=False, indent=2) + '\n'
if not coverage_file.exists() or coverage_file.read_text(encoding='utf-8') != coverage_body:
    coverage_file.write_text(coverage_body, encoding='utf-8')
print('Frontend feed: ' + str(len(feed_content.encode('utf-8'))) + ' bytes')
print('Relationship types:', sorted({rel['type'] for rel in relationships.values()}))

