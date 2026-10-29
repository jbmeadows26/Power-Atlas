"""Offline checks for compact, source-linked Power Atlas records."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE = {
    'contributor_name', 'contributor_address', 'street_address',
    'street_1', 'street_2', 'zip_code', 'email',
    'phone', 'occupation', 'employer'
}

def load(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))

class CorpusChecks(unittest.TestCase):
    def test_source_records_and_unique_ids(self):
        records = load('data/research.json')['records']
        ids = [r['id'] for r in records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 8)
        for r in records:
            self.assertTrue(r['source'].startswith('https://'))
            self.assertTrue(r.get('status') or r.get('reviewStatus'))
            self.assertTrue(r.get('title'))
            self.assertTrue(r.get('source_sha256'))
            self.assertFalse(SENSITIVE.intersection(r.keys()))

    def test_frontend_feed_matches_outputs(self):
        feed = load('data/app-feed.json')
        self.assertEqual(feed['publicationStatus'], 'review_required')
        self.assertEqual(feed['records'], load('data/research.json')['records'])
        self.assertEqual(feed['relationships'], load('data/relationships.json')['relationships'])
        states = load('data/geography/states.json')['states'] if (ROOT / 'data/geography/states.json').exists() else []
        self.assertEqual(feed.get('states', []), states)
        self.assertEqual(feed['coverage']['stateSourceReferences'], len(states))
        self.assertEqual(feed['coverage']['sourceIndexedRecords'], len(feed['records']))
        self.assertEqual(feed['coverage']['relationshipRecords'], len(feed['relationships']))
        totals = load('data/finance/fec-totals.json')['records'] if (ROOT / 'data/finance/fec-totals.json').exists() else []
        payments = load('data/finance/fec-disbursements.json')['records'] if (ROOT / 'data/finance/fec-disbursements.json').exists() else []
        self.assertEqual(feed['finance']['committeeTotals'], totals)
        self.assertEqual(feed['finance']['committeePayments'], payments)
        self.assertEqual(feed['coverage']['committeeTotalRows'], len(totals))
        self.assertEqual(feed['coverage']['paymentRows'], len(payments))

    def test_census_map_source_index(self):
        path = ROOT / 'data/geography/states.json'
        if not path.exists():
            self.skipTest('Geography index not initialized')
        states = load('data/geography/states.json')['states']
        self.assertGreaterEqual(len(states), 51)
        self.assertEqual(len({s['fips'] for s in states}), len(states))
        for r in states:
            self.assertTrue(r['districtMapSource'].startswith('https://www2.census.gov/'))
            self.assertFalse(SENSITIVE.intersection(r.keys()))

    def test_house_votes_have_provenance(self):
        if not (ROOT / 'data/elections/house-summary.json').exists():
            self.skipTest('House summaries not initialized')
        summaries = load('data/elections/house-summary.json')['records']
        self.assertGreaterEqual(len(summaries), 50)
        keys = set()
        for r in summaries:
            key = (r['year'], r['state'])
            self.assertNotIn(key, keys)
            keys.add(key)
            self.assertGreaterEqual(r['districts'], r['districtsWithTwoPartyVotes'])
            self.assertEqual(r['democraticVotes'] + r['republicanVotes'], r['twoPartyVotes'])
            self.assertGreaterEqual(r['twoPartyVotes'], 0)
        feed = load('data/app-feed.json')
        self.assertEqual(feed['elections']['houseStateYears'], summaries)
        self.assertEqual(feed['coverage']['houseStateYearRows'], len(summaries))
        if (ROOT / 'data/elections/house-districts.json').exists():
            districts = load('data/elections/house-districts.json')['records']
            self.assertEqual(feed['coverage']['houseDistrictYearRows'],len(districts))
            self.assertEqual(feed['coverage']['house2024VoteDistrictRows'],
                             sum(r['year']==2024 for r in districts))

    def test_congress_roster_and_crosswalks(self):
        if not (ROOT / 'data/people/congress-members.json').exists():
            self.skipTest('Congress registry not initialized')
        people = load('data/people/congress-members.json')['records']
        self.assertGreaterEqual(len(people), 520)
        self.assertEqual(len(people), len({p['bioguideId'] for p in people}))
        self.assertGreaterEqual(sum(p['chamber'] == 'Senate' for p in people), 90)
        for person in people:
            self.assertIsNotNone(re.fullmatch(r'[A-Z][0-9]{6}', person['bioguideId']))
            self.assertEqual(person['sourceLicense'], 'CC0-1.0')
            self.assertIn('reviewStatus', person)
            self.assertFalse(SENSITIVE.intersection(person.keys()))
            for candidate_id in person.get('fecCandidateIds', []):
                self.assertIsNotNone(re.fullmatch(r'[HSP][A-Z0-9]{8}', candidate_id))
        feed = load('data/app-feed.json')
        self.assertEqual(feed['people']['congressMembers'], people)
        self.assertEqual(feed['coverage']['congressMemberRows'], len(people))

    def test_state_legislators_partition_consistency(self):
        index_path = ROOT / 'data/people/state-legislators-index.json'
        if not index_path.exists():
            self.skipTest('State legislators not yet indexed')
        index = load('data/people/state-legislators-index.json')
        self.assertGreaterEqual(len(index['jurisdictions']), 50)
        summed = 0
        for state in index['jurisdictions']:
            abbr = state['state']
            self.assertIsNotNone(re.fullmatch(r'[A-Z]{2}', abbr))
            part = load('data/people/states/' + abbr + '.json')
            self.assertEqual(part['state'], abbr)
            self.assertEqual(part['license'], 'CC0-1.0')
            self.assertEqual(len(part['records']), state['members'])
            for person in part['records']:
                self.assertEqual(person['state'], abbr)
                self.assertFalse(SENSITIVE.intersection(person.keys()))
                self.assertIn('reviewStatus', person)
            summed += len(part['records'])
        self.assertEqual(index['totalIndexed'], summed)
        self.assertGreater(summed, 4000)
        feed = load('data/app-feed.json')
        self.assertEqual(feed['people']['stateLegislatorIndex'], index['jurisdictions'])
        self.assertEqual(feed['coverage']['stateLegislatorRows'], summed)

    def test_fec_official_candidate_committee_linkage(self):
        file = ROOT / 'data/finance/fec-candidate-links.json'
        if not file.exists():
            self.skipTest('FEC bulk candidate linkage not yet collected')
        doc = load('data/finance/fec-candidate-links.json')
        links = doc['records']
        self.assertGreaterEqual(len(links), 300)
        self.assertEqual(len({r['id'] for r in links}), len(links))
        for item in links:
            self.assertIsNotNone(re.fullmatch(r'[HSP][A-Z0-9]{8}',item['fecCandidateId']))
            self.assertIsNotNone(re.fullmatch(r'C[0-9]{8}',item['committeeId']))
            self.assertIn(item['fecYear'], (2024,2026))
            self.assertIn('reviewStatus', item)
            self.assertFalse(SENSITIVE.intersection(item.keys()))
        edges = load('data/relationships.json')['relationships']
        kinds = {}
        for edge in edges:
            kinds[edge['type']] = kinds.get(edge['type'],0) + 1
        self.assertEqual(kinds.get('FEC_reported_candidate_committee_linkage',0),len(links))
        feed = load('data/app-feed.json')
        self.assertEqual(feed['finance']['candidateCommitteeLinks']['count'],len(links))
        coverage = load('data/coverage.json')
        self.assertEqual(coverage['coverage'],feed['coverage'])
        self.assertEqual(coverage['relationshipTypes'].get('FEC_reported_candidate_committee_linkage'),len(links))

    def test_state_committee_memberships_and_graph(self):
        file = ROOT / 'data/organizations/redistricting-committees.json'
        if not file.exists():
            self.skipTest('State redistricting committees not yet collected')
        corpus = load('data/organizations/redistricting-committees.json')
        committees = corpus['committees']
        self.assertGreaterEqual(len(committees), 10)
        self.assertEqual(len({c['id'] for c in committees}), len(committees))
        source_edges = 0
        for c in committees:
            self.assertTrue(c['source'].startswith('https://github.com/openstates/people/'))
            self.assertIn(c['topic'], ('redistricting', 'elections_related'))
            self.assertFalse(SENSITIVE.intersection(c.keys()))
            for person in c.get('members', []):
                self.assertTrue(person['personId'].startswith('ocd-person/'))
                self.assertIn('role', person)
                source_edges += 1
        self.assertEqual(source_edges, corpus['coverage']['memberLinks'])
        graph = load('data/relationships.json')['relationships']
        actual = [e for e in graph if e.get('type') == 'documented_committee_membership']
        self.assertEqual(len(actual), source_edges)
        feed = load('data/app-feed.json')
        self.assertEqual(len(feed['organizations']['stateCommittees']), len(committees))
        self.assertEqual(feed['coverage']['stateCommitteeRows'], len(committees))
        self.assertEqual(feed['coverage']['stateCommitteeMembershipEdges'], source_edges)

    def test_house_representation_gaps_not_causal_and_unopposed(self):
        file = ROOT / 'data/elections/representation-gaps.json'
        if not file.exists():
            self.skipTest('Derived representation records not yet present')
        doc=load('data/elections/representation-gaps.json')
        records=doc['records']
        self.assertGreaterEqual(len(records),300)
        self.assertEqual(len(records),len({r['id'] for r in records}))
        by={(r['year'],r['state']):r for r in records}
        for abbr in ('FL','OK'):
            if (2024,abbr) in by:
                self.assertFalse(by[(2024,abbr)]['comparableOnIndexedReturns'])
                self.assertTrue(by[(2024,abbr)]['knownOfficialUnopposedDistrictExcluded'])
                self.assertNotIn('observedSeatMinusVotePctPoints',by[(2024,abbr)])
        feed=load('data/app-feed.json')
        self.assertEqual(feed['elections']['representationByStateYear'],records)
        self.assertEqual(feed['coverage']['representationStateYearRows'],len(records))

    def test_federal_bill_sponsorship_evidence(self):
        file=ROOT/'data/legislation/federal-bill-candidates.json'
        if not file.exists():
            self.skipTest('Federal bill index not collected')
        doc=load('data/legislation/federal-bill-candidates.json')
        bills=doc['records']
        self.assertGreaterEqual(len(bills),3)
        self.assertEqual(len(bills),len({r['id'] for r in bills}))
        for bill in bills:
            self.assertTrue(bill['source'].startswith('https://www.congress.gov/'))
            self.assertEqual(bill['congress'],119)
            self.assertIn(bill['issueClass'],('redistricting_specific_title','broader_voting_or_elections_title','keyword_hit_not_title_verified'))
            self.assertFalse(SENSITIVE.intersection(bill.keys()))
            self.assertIn('reviewStatus',bill)
        feed=load('data/app-feed.json')
        self.assertEqual(feed['legislation']['federalBillCandidates'],bills)
        self.assertEqual(feed['coverage']['federalBillCandidateRows'],len(bills))
        graph=load('data/relationships.json')['relationships']
        sponsored=[e for e in graph if e.get('type')=='source_reported_federal_bill_sponsorship']
        self.assertEqual(len(sponsored),feed['coverage']['federalBillSponsorEdges'])

    def test_state_bill_source_links_and_vote_tally_status(self):
        p = ROOT / 'data/legislation/state-redistricting-bills.json'
        if not p.exists():
            self.skipTest('State bill index has not yet completed')
        bills = load('data/legislation/state-redistricting-bills.json')
        ids = [row['id'] for row in bills['records']]
        self.assertEqual(len(ids), len(set(ids)))
        for r in bills['records']:
            self.assertTrue(re.fullmatch('[A-Z]{2}', r['state']))
            self.assertTrue(r['source'].startswith('https://'))
            self.assertIn(r['issueClass'], ('redistricting_specific_title', 'keyword_search_candidate_unverified'))
            self.assertFalse(SENSITIVE.intersection(r.keys()))
        vote_file = ROOT / 'data/legislation/state-redistricting-votes.json'
        if vote_file.exists():
            votes = load('data/legislation/state-redistricting-votes.json')['records']
            self.assertEqual(len(votes), len({r['id'] for r in votes}))
            for v in votes:
                self.assertTrue(v['source'].startswith('https://'))
                self.assertFalse(SENSITIVE.intersection(v.keys()))
                if v['counts']:
                    self.assertGreater(sum(v['counts'].values()), 0)
                    self.assertEqual(v['tallyStatus'], 'reported_positive_tally')
                else:
                    self.assertEqual(v['tallyStatus'], 'not_reported_or_unverifiable')
            feed = load('data/app-feed.json')
            self.assertEqual(feed['legislation']['stateRedistrictingRecordedVotes'], votes)
            self.assertEqual(feed['legislation']['stateRedistrictingBillCandidates'], bills['records'])
            self.assertEqual(feed['coverage']['stateRecordedVoteRows'], len(votes))
            self.assertEqual(feed['coverage']['stateBillCandidateRows'], len(bills['records']))

    def test_fec_finance_minimal_provenance(self):
        feed = load('data/app-feed.json')
        for row in feed['finance']['committeeTotals'] + feed['finance']['committeePayments']:
            self.assertIsNotNone(re.fullmatch(r'C[0-9]{8}', row['committeeId']))
            self.assertTrue(row['source'].startswith('https://www.fec.gov/'))
            self.assertFalse(SENSITIVE.intersection(row.keys()))
            self.assertIn('reviewStatus', row)

    def test_census_district_geometry(self):
        path = ROOT / 'data/geography/districts-119.geojson'
        if not path.exists():
            self.skipTest('Generalized district map not yet collected')
        doc = load('data/geography/districts-119.geojson')
        self.assertEqual(doc['type'], 'FeatureCollection')
        self.assertEqual(doc['license'], 'CC0-1.0')
        self.assertGreaterEqual(len(doc['features']), 435)
        self.assertEqual(len(doc['features']), len({f['id'] for f in doc['features']}))
        self.assertLess(path.stat().st_size, 3000000)

    def test_fec_recipient_aggregates_do_not_include_individual_payees(self):
        file = ROOT / 'data/finance/fec-recipient-aggregates.json'
        if not file.exists():
            self.skipTest('FEC aggregate recipient source not yet ingested')
        rows = load('data/finance/fec-recipient-aggregates.json')['records']
        feed = load('data/app-feed.json')
        self.assertEqual(feed['finance']['committeeRecipientAggregates'], rows)
        self.assertEqual(feed['coverage']['recipientAggregateRows'], len(rows))
        for row in rows:
            self.assertRegex(row['sourceCommitteeId'], r'^C[0-9]{8}$')
            self.assertRegex(row['recipientCommitteeId'], r'^C[0-9]{8}$')
            self.assertIsInstance(row['amountUSD'], (int,float))
            self.assertGreaterEqual(row['disbursementCount'], 0)
            self.assertNotIn('recipientAddress', row)
            self.assertNotIn('recipientCity', row)
            self.assertEqual(row['reviewStatus'], 'official_fec_aggregate_unreviewed')

    def test_2024_house_missing_vote_totals_are_not_fabricated(self):
        audit_path = ROOT / 'data/health/house-2024-audit.json'
        official_path = ROOT / 'data/elections/house-2024-unopposed.json'
        if not audit_path.exists() or not official_path.exists():
            self.skipTest('2024 key audit and Clerk status records not initialized')
        audit = load('data/health/house-2024-audit.json')
        official = load('data/elections/house-2024-unopposed.json')['records']
        self.assertEqual(audit['comparisonYear'], 2024)
        self.assertEqual(audit['congress'], 119)
        self.assertEqual(audit['expectedCensusDistrictKeys'],
                         audit['observedMEDSLDistrictKeys'] +
                         audit['officialUnopposedStatusOnlyKeys'] +
                         audit['missingCount'])
        self.assertEqual(len(official), audit['officialUnopposedStatusOnlyKeys'])
        self.assertEqual(len({(r['state'],r['district']) for r in official}),len(official))
        for r in official:
            self.assertIsNone(r['reportedVoteTotal'])
            self.assertEqual(r['year'], 2024)
            self.assertEqual(r['reviewStatus'], 'official_house_clerk_2024_status_only')
            self.assertTrue(r['source'].startswith('https://clerk.house.gov/'))
            self.assertNotIn((r['state'],r['district']),
                             {(m['state'],m['district']) for m in audit['missing']})
        feed = load('data/app-feed.json')
        self.assertEqual(feed['elections']['house2024UnopposedStatusOnly'],official)
        self.assertEqual(feed['elections']['house2024KeyAudit'],audit)
        self.assertEqual(feed['coverage']['house2024MissingDistrictKeys'],audit['missingCount'])

    def test_curated_supreme_court_decisions_have_primary_docket_evidence(self):
        source = load('data/batches/scotus-redistricting-decisions.json')
        rows = source['records']
        self.assertEqual(source['publicationStatus'], 'curated_scotus_decision_index_not_nationwide_docket_coverage')
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({r['docket'] for r in rows}), len(rows))
        allowed = {'affirmed', 'vacated_and_remanded', 'reversed_in_part_remanded_in_part', 'appeal_dismissed'}
        for r in rows:
            self.assertIsNotNone(re.fullmatch(r'[0-9]{2}-[0-9]{1,5}', r['docket']))
            self.assertEqual(r['id'], 'scotus-'+r['docket'])
            self.assertEqual(r['source'], 'https://www.supremecourt.gov/docket/docketfiles/html/public/'+r['docket']+'.html')
            self.assertIsNotNone(re.fullmatch(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}', r['date']))
            self.assertIn(r['disposition'], allowed)
            self.assertEqual(r['court'], 'Supreme Court of the United States')
            self.assertFalse(SENSITIVE.intersection(r.keys()))
        feed = load('data/app-feed.json')
        indexed = feed['judiciary']['supremeCourtRedistrictingDecisions']
        self.assertEqual(len(indexed), 7)
        expected = {r['id'] for r in rows} | {'scotus-allen-2023','scotus-moore-2023','scotus-rucho-2019'}
        self.assertEqual({r['id'] for r in indexed}, expected)
        self.assertEqual(feed['coverage']['supremeCourtRedistrictingDecisions'],len(indexed))
        for r in indexed:
            self.assertIn(r['disposition'],allowed)
            self.assertTrue(r['claimScope'])

    def test_state_redistricting_checkpoint_contract(self):
        path = ROOT / 'data/legislation/state-redistricting-jurisdictions.json'
        if not path.exists():
            self.skipTest('Incremental jurisdiction checkpoint not initialized')
        checkpoint = load('data/legislation/state-redistricting-jurisdictions.json')
        expected = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY DC'.split())
        scanned = checkpoint['jurisdictions']
        remaining = checkpoint['remainingJurisdictions']
        self.assertEqual(len(expected), 51)
        self.assertEqual(checkpoint['jurisdictionsTotal'], 51)
        self.assertEqual(checkpoint['jurisdictionsScanned'], len(scanned))
        self.assertEqual(set(scanned) | set(remaining), expected)
        self.assertFalse(set(scanned) & set(remaining))
        self.assertEqual(len(remaining), len(set(remaining)))
        self.assertLessEqual(len(checkpoint['latestBatch']), 8)
        for state, scope in scanned.items():
            self.assertEqual(scope['status'], 'first_page_indexed_not_exhaustive')
            self.assertEqual(scope['searchPage'], 1)
            self.assertLessEqual(scope['perPage'], 20)
        bills = load('data/legislation/state-redistricting-bills.json')
        self.assertEqual(bills['incrementalJurisdictionsScanned'], len(scanned))
        self.assertEqual(len(bills['records']), len({r['id'] for r in bills['records']}))
        self.assertLess((ROOT / 'data/legislation/state-redistricting-bills.json').stat().st_size, 850000)
        feed = load('data/app-feed.json')
        self.assertEqual(feed['legislation']['stateRedistrictingBillCandidates'], bills['records'])

    def test_compact_derived_feeds(self):
        for name in ['data/research.json', 'data/relationships.json', 'data/app-feed.json']:
            self.assertLess((ROOT / name).stat().st_size, 3000000, name)


if __name__ == '__main__':
    unittest.main()
