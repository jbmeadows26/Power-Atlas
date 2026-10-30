"""Explain official House XML parser false rejects without saving raw votes."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from xml.etree import ElementTree as ET
from collections import Counter
import json,re

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/health/official-house-vote-shape-diagnostics.json'
NUMBERS=(2,21,31,80)
VALID={'Yea','Nay','Present','Not Voting'}

def main():
    report=[]
    for number in NUMBERS:
        url=f'https://clerk.house.gov/evs/2025/roll{number:03d}.xml'
        obj={'roll':number,'source':url}
        try:
            with urlopen(Request(url,headers={'User-Agent':'PowerAtlasPublicResearch/1.0 public congressional records'}),timeout=22) as r:
                raw=r.read(450001)
                if len(raw)>450000:raise RuntimeError('XML larger than source bound')
            root=ET.fromstring(raw)
            rows=root.findall('.//vote-data/recorded-vote')
            valid=[]
            invalid_votes=Counter()
            id_formats=Counter()
            for row in rows:
                person=row.find('legislator')
                val=row.findtext('vote','').strip()
                pid=person.get('name-id','') if person is not None else ''
                if re.fullmatch(r'[A-Z][0-9]{6}',pid) and val in VALID:
                    valid.append(pid)
                else:
                    if val not in VALID:invalid_votes[val[:50]]+=1
                    if not re.fullmatch(r'[A-Z][0-9]{6}',pid):id_formats[pid[:20]]+=1
            meta=root.find('vote-metadata')
            obj.update({'status':'official_xml_inspected',
                        'totalRecordedVoteNodes':len(rows),
                        'parsedMemberIds':len(valid),
                        'distinctMemberIds':len(set(valid)),
                        'hasQuestion':bool(meta is not None and meta.findtext('vote-question','').strip()),
                        'invalidVoteValueCounts':dict(invalid_votes.most_common(5)),
                        'invalidIdExamples':dict(id_formats.most_common(5)),
                        'xmlRootTag':root.tag})
        except (HTTPError,URLError,ValueError,RuntimeError,ET.ParseError,TimeoutError) as exc:
            obj.update({'status':'source_unavailable','errorType':type(exc).__name__,
                        'error':str(exc)[:130]})
        report.append(obj)
    DEST.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps({'schema':'power-atlas.house-small-vote-shapes.v1',
                        'meaning':'Identifies whether official Clerk vote data is truly under 200 votes or parser has an ID mismatch',
                        'records':report},indent=2)+'\n'
    DEST.write_text(content,encoding='utf-8')
    print('Small/rejected House roll-call diagnostics:',[(r['roll'],r.get('parsedMemberIds'),r.get('totalRecordedVoteNodes')) for r in report])
if __name__=='__main__':main()
