"""Bounded official U.S. Senate recorded roll-call indexes (119th Congress).

Two sessions (2025/2026), keyless public XML menus directly from Senate.gov.
Metadata only by default; the small member-level detail subset is limited to
explicitly election/redistricting-related questions, never presumed motive.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/legislation/senate-119-rollcalls.json'
BASE='https://www.senate.gov/legislative/LIS/'
SESSIONS=((1,2025),(2,2026))
MAX_BYTES=300000
TOPICS=('redistrict','reapportion','voting rights','election','ballot','census','congressional district','voter')
MAX_TOPIC_DETAILS=16

def download(url, maximum=MAX_BYTES):
    req=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public records index',
                             'Accept':'application/xml,text/xml'})
    with urlopen(req,timeout=28) as response:
        if response.status!=200:
            raise RuntimeError('Senate source HTTP error')
        raw=response.read(maximum+1)
        if len(raw)>maximum:
            raise RuntimeError('Senate XML source exceeded byte bound')
    return raw

def short(node,name):
    found=node.find('.//'+name)
    return ' '.join((found.text or '').split())[:240] if found is not None else ''

def clean_number(value):
    m=re.search(r'[0-9]{1,4}',value)
    return int(m.group()) if m else 0

def collect():
    existing=json.loads(OUT.read_text(encoding='utf-8'))['records'] if OUT.exists() else []
    by_id={r['id']:r for r in existing}
    sessions=[]
    topical_total=0
    for session,year in SESSIONS:
        menu=BASE+f'roll_call_lists/vote_menu_119_{session}.xml'
        root=ET.fromstring(download(menu))
        elements=root.findall('.//vote')
        if not 80<=len(elements)<=800:
            raise RuntimeError('Unexpected Senate session index size '+str(year)+': '+str(len(elements)))
        seen=set()
        found=0
        for v in elements:
            number=clean_number(short(v,'vote_number'))
            if number<1 or number in seen:
                raise RuntimeError('Missing/duplicate senate roll number in '+str(year))
            seen.add(number)
            vid=f'senate-119-{session}-{number:04d}'
            metadata={
                'id':vid,'year':year,'session':session,'congress':119,'roll':number,
                'dateDisplay':short(v,'vote_date'),
                'issue':short(v,'issue'),'question':short(v,'question'),
                'result':short(v,'result'),'voteTitle':short(v,'vote_title'),
                'source':BASE+f'roll_call_votes/vote119{session}/vote_119_{session}_{number:05d}.xml',
                'reviewStatus':'official_Senate_rollcall_indexed_unreviewed'
            }
            desc=' '.join(metadata[k] for k in ('issue','question','voteTitle')).lower()
            metadata['topicMatch']=any(term in desc for term in TOPICS)
            if metadata['topicMatch']:
                found+=1
            # Preserve text from menu where fields aren't provided; do not invent tally.
            by_id[vid]=metadata
        sessions.append({'year':year,'rollCalls':len(seen),'topicMatches':found,'menu':menu})
        topical_total+=found
        print(year,'roll call metadata',len(seen),'election keyword candidates',found)
    if not 100<=len(by_id)<=1600:
        raise RuntimeError('Unexpected Senate roll index overall size')
    indexed={
        'schema':'power-atlas.senate-119-rollcalls.v1',
        'sourceAuthority':'U.S. Senate Legislative Information System',
        'publicationStatus':'official_rollcall_menu_indexed',
        'scope':'All listed roll calls of 119th Congress; term matches are exploratory, not evidence of redistricting action or causal influence.',
        'searchTerms':list(TOPICS),
        'sessions':sessions,
        'records':sorted(by_id.values(),key=lambda x:(x['year'],x['roll']))
    }
    text=json.dumps(indexed,indent=2,ensure_ascii=False)+'\n'
    if len(text.encode())>800000:
        raise RuntimeError('Senate metadata export exceeds target')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=text:
        OUT.write_text(text,encoding='utf-8')
    print('Indexed Senate roll calls',len(by_id),'topic candidates',topical_total)

if __name__=='__main__':
    collect()
