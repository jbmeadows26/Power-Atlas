"""Evidence-linked state redistricting and elections committee memberships.

Source: openstates/people (CC0-1.0), compiled from official state records.
Member edges represent membership only, never improper influence.
"""
from pathlib import Path
import json
import os
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=Path(os.environ.get('OPENSTATES_PEOPLE_DIR','../openstates-people')).resolve()
OUT=ROOT/'data/organizations/redistricting-committees.json'
STATES='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY DC PR'.split()
TOPICS=('redistrict','reapportion','election','voting right','electoral','districting')

def main():
    committees={}
    scanned=0
    without_source=[]
    for abbr in STATES:
        folder=UPSTREAM/'data'/abbr.lower()/'committees'
        if not folder.is_dir():
            without_source.append(abbr)
            continue
        scanned+=1
        for file in sorted(folder.glob('*.yml')):
            if file.stat().st_size>50000:
                continue
            row=yaml.safe_load(file.read_text(encoding='utf-8'))
            if not isinstance(row,dict):
                continue
            title=str(row.get('name') or '').strip()
            if not any(q in title.lower() for q in TOPICS):
                continue
            uid=str(row.get('id') or '')
            if not re.fullmatch(r'ocd-organization/[a-zA-Z0-9-]{20,50}',uid):
                continue
            links=row.get('links') or []
            official=''
            for link in links:
                u=str(link.get('url') or '') if isinstance(link,dict) else ''
                if u.startswith('https://'):
                    official=u
                    break
            source='https://github.com/openstates/people/blob/main/data/'+abbr.lower()+'/committees/'+file.name
            members={}
            for member in row.get('members') or []:
                if not isinstance(member,dict):
                    continue
                pid=str(member.get('person_id') or '')
                if not re.fullmatch(r'ocd-person/[a-zA-Z0-9-]{20,50}',pid):
                    continue
                members[pid]={
                    'personId':pid,
                    'name':str(member.get('name') or '')[:110],
                    'role':str(member.get('role') or 'member')[:55]
                }
            committees[uid]={
                'id':uid,'state':abbr,'name':title[:150],
                'chamber':str(row.get('chamber') or 'legislature')[:45],
                'topic':'redistricting' if ('redistrict' in title.lower() or 'reapportion' in title.lower()) else 'elections_related',
                'source':source,
                'officialLink':official,
                'reviewStatus':'curated_committee_membership_unreviewed',
                'members':sorted(members.values(),key=lambda x:x['personId'])
            }
    if not 10<=len(committees)<=600:
        raise RuntimeError('Unexpected committee count, refusing overwrite: '+str(len(committees)))
    total_edges=sum(len(c['members']) for c in committees.values())
    doc={
        'schema':'power-atlas.state-committees.v1',
        'publicationStatus':'topic_and_membership_source_review_required',
        'license':'CC0-1.0','sourceCatalog':'https://github.com/openstates/people',
        'criteria':'Committee name contains redistrict/reapportion/election/voting right/electoral/districting',
        'scope':'Committee membership and office role only, no inferred map control or improper political influence',
        'coverage':{'jurisdictionsWithCommitteeFolders':scanned,'jurisdictionsWithoutFolders':without_source,
                    'matchingCommittees':len(committees),'memberLinks':total_edges},
        'committees':sorted(committees.values(),key=lambda c:c['id'])
    }
    text=json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(text.encode())>1200000:
        raise RuntimeError('Committee data exceeds minimal-storage limit')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=text:
        OUT.write_text(text,encoding='utf-8')
    print('Committee corpus:',len(committees),'membership edges:',total_edges,'bytes:',len(text.encode()))

if __name__=='__main__':
    main()
