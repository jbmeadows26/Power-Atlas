"""Ingest source-linked federal redistricting/elections bill candidates.

BallotWatch openly documents CC0 data and free no-key API.
This is a secondary normalized index, not primary-source validation.
Keep public bill IDs, titles, sponsor IDs and Congress.gov links only.
Search results are top-N candidates rather than exhaustive Congress census.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/legislation/federal-bill-candidates.json'
API='https://www.ballotwatch.io/api/v1/search'
DOCS='https://www.ballotwatch.io/developers'
TERMS=(
  'redistricting','gerrymandering','congressional district','reapportionment',
  'voting rights','election administration','election maps',
  'voter registration','independent redistricting'
)
MAX_RESPONSE=300000
REDIST=('redistrict','gerrymander','reapportion','congressional district')
VOTING=('voting right','voter registr','election administr','election integrity','federal election','election security')

def classify(title):
    lower=title.lower()
    if any(term in lower for term in REDIST):
        return 'redistricting_specific_title'
    if any(term in lower for term in VOTING):
        return 'broader_voting_or_elections_title'
    return 'keyword_hit_not_title_verified'

def fetch(term):
    url=API+'?'+urlencode({'q':term,'limit':40})
    req=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public CC0 legislation index'})
    with urlopen(req,timeout=25) as response:
        if response.status!=200:
            raise RuntimeError('Public bill search API unavailable')
        raw=response.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE:raise RuntimeError('Public search exceeded response cap')
    doc=json.loads(raw)
    if not isinstance(doc.get('data'),dict) or not isinstance(doc['data'].get('bills'),list):
        raise ValueError('Unexpected candidate-bill search schema')
    return doc['data']['bills'],url

def collect():
    current={}
    coverage=[]
    for term in TERMS:
        try:
            rows,url=fetch(term)
        except HTTPError as exc:
            if exc.code in (401,403,429):
                raise RuntimeError('Provider access or rate restriction HTTP '+str(exc.code)+'; existing data retained') from exc
            raise
        hit_count=0
        for row in rows:
            bid=str(row.get('id') or '')
            if not re.fullmatch(r'119-(?:hr|hres|hjres|hconres|s|sres|sjres|sconres)-[0-9]{1,6}',bid):
                continue
            title=' '.join(str(row.get('title') or '').split())[:240]
            source=str(row.get('source_url') or '')
            if not title or not source.startswith(('https://www.congress.gov/','https://congress.gov/')):
                continue
            sponsor=str(row.get('sponsor_bioguide_id') or '')
            if sponsor and not re.fullmatch(r'[A-Z][0-9]{6}',sponsor):
                sponsor=''
            event={
                'id':'federal-bill-'+bid,'billId':bid,'congress':119,
                'title':title,'issueClass':classify(title),
                'sponsorBioguideId':sponsor,
                'sponsorName':str(row.get('sponsor_name') or '')[:100],
                'sponsorParty':str(row.get('sponsor_party') or '')[:30],
                'sponsorState':str(row.get('sponsor_state') or '')[:2],
                'introducedAt':str(row.get('introduced_at') or '')[:32],
                'legislativeStage':str(row.get('legislative_stage') or '')[:75],
                'source':source,
                'indexProvider':DOCS,
                'reviewStatus':'CC0_secondary_bill_index_primary_source_check_pending'
            }
            if event['id'] not in current:
                current[event['id']]=event;hit_count+=1
        coverage.append({'query':term,'returned':len(rows),'uniqueNewMatches':hit_count,
                         'searchURL':url,'pagination':'first bounded results only'})
    if not 3<=len(current)<=350:
        raise RuntimeError('Unexpected federal bill candidates count '+str(len(current)))
    indexed={
        'schema':'power-atlas.federal-bill-candidates.v1',
        'publicationStatus':'candidate_for_primary_Congressgov_review',
        'license':'CC0-1.0 per BallotWatch bulk/API documentation',
        'provider':DOCS,
        'meaning':'Congress bill titles, sponsors, and reported legislative stages; NOT a completed-vote or legislative-outcome census',
        'searchCoverage':coverage,
        'records':sorted(current.values(),key=lambda x:x['id'])
    }
    rendered=json.dumps(indexed,indent=2,ensure_ascii=False)+'\n'
    if len(rendered.encode())>280000:
        raise RuntimeError('Candidate bill index exceeded compact size target')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=rendered:
        OUT.write_text(rendered,encoding='utf-8')
    print('Indexed public federal candidate bills:',len(current),
          'redistrict-specific titles:',sum(r['issueClass']=='redistricting_specific_title' for r in current.values()))

if __name__=='__main__':
    collect()
