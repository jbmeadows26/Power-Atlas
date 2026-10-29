"""Conservative district-return-based descriptive representation gap.

This is NOT an efficiency gap, partisan symmetry estimate, cause of a seat gap,
or a measure of legally improper gerrymandering. We exclude a state-year from
interpretation when any indexed district lacks competitive two-party returns.
"""
from collections import defaultdict
from pathlib import Path
import json
import math

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/elections/house-districts.json'
OUT=ROOT/'data/elections/representation-gaps.json'

def run():
    raw=json.loads(SOURCE.read_text(encoding='utf-8'))
    groups=defaultdict(list)
    for row in raw['records']:
        year=row.get('year')
        state=row.get('state')
        if not isinstance(year,int) or not isinstance(state,str) or len(state)!=2:
            raise ValueError('Unrecognized state-year grain in source')
        groups[(year,state)].append(row)
    result=[]
    for (year,state),rows in sorted(groups.items()):
        ids=[r['district'] for r in rows]
        if len(ids)!=len(set(ids)):
            raise ValueError(f'Duplicate congressional district in {state}, {year}')
        contested=[r for r in rows if r['democraticVotes']>0 and r['republicanVotes']>0]
        valid=[r for r in rows if r['twoPartyVotes']>0]
        d_votes=sum(r['democraticVotes'] for r in rows)
        r_votes=sum(r['republicanVotes'] for r in rows)
        total=d_votes+r_votes
        d_seats=sum(1 for r in valid if r['democraticVotes']>r['republicanVotes'])
        r_seats=sum(1 for r in valid if r['republicanVotes']>r['democraticVotes'])
        tied=len(valid)-d_seats-r_seats
        complete_contested=bool(total and len(contested)==len(rows) and not tied)
        values={
            'id':f'representation-{year}-{state}', 'year':year, 'state':state,
            'districtsWithIndexedReturns':len(rows),
            'districtsWithVotes':len(valid),
            'twoMajorPartyContestedDistricts':len(contested),
            'observedDemocraticSeats':d_seats,'observedRepublicanSeats':r_seats,
            'ties':tied,
            'democraticVotes':d_votes,'republicanVotes':r_votes,
            'twoPartyVotes':total,
            'comparableOnIndexedReturns':complete_contested,
            'evidenceSource':raw.get('sourceCatalog') or 'https://doi.org/10.7910/DVN/IG0UN2',
            'status':'derived_from_unreviewed_house_returns',
            'limitations':'Descriptive gap is not partisan bias, gerrymandering causality, or judicial evidence. Missing election districts and candidate-party coding may affect interpretation.'
        }
        if complete_contested and total>0:
            dv=d_votes/total
            ds=d_seats/len(rows)
            values['democraticTwoPartyVoteSharePct']=round(dv*100,2)
            values['democraticObservedSeatSharePct']=round(ds*100,2)
            values['observedSeatMinusVotePctPoints']=round((ds-dv)*100,2)
        result.append(values)
    years=sorted({row['year'] for row in result})
    if len(result)<300 or len(years)<6:
        raise RuntimeError('Unexpected state-year coverage, old file preserved')
    doc={
        'schema':'power-atlas.house-representation-descriptive.v1',
        'sourceDataset':raw.get('sourceDataset','MIT Election Data and Science Lab US House'),
        'sourceLicense':raw.get('sourceLicense','CC0-1.0'),
        'publicationStatus':'derived_unreviewed_descriptive_not_causal',
        'interpretation':'Seat-vote gap is descriptive only. Values are calculated only for observed fully two-party-contested district datasets; additional per-year district completeness checks are needed.',
        'years':years,
        'counts':{
            'indexedStateYears':len(result),
            'twoPartyContestedSourceStateYears':sum(r['comparableOnIndexedReturns'] for r in result),
            'notComparableStateYears':sum(not r['comparableOnIndexedReturns'] for r in result)
        },
        'records':result
    }
    body=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
    if len(body.encode())>600000:raise RuntimeError('Representation summary unexpectedly large')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=body:
        OUT.write_text(body,encoding='utf-8')
    print('Representation state-years',len(result),'two-party contested only',doc['counts']['twoPartyContestedSourceStateYears'])

if __name__=='__main__':
    run()
