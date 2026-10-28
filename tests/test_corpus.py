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
                self.assertIsNotNone(re.fullmatch(r'[HS][0-9]{8}', candidate_id))
        feed = load('data/app-feed.json')
        self.assertEqual(feed['people']['congressMembers'], people)
        self.assertEqual(feed['coverage']['congressMemberRows'], len(people))

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

    def test_compact_derived_feeds(self):
        for name in ['data/research.json', 'data/relationships.json', 'data/app-feed.json']:
            self.assertLess((ROOT / name).stat().st_size, 3000000, name)

if __name__ == '__main__':
    unittest.main()
