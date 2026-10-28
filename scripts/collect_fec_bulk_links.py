"""Official FEC bulk candidate-committee association ingestion (2024, 2026).

This uses FEC's separately published keyless candidate-committee linkage files,
not its rate-limited API. Parse a bounded archive locally and retain ONLY
links for candidate IDs already indexed in public congressional roster,
plus committees from Power Atlas's redistricting-specific source index.
No donor, contact, address or transaction data are loaded or persisted.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import io
import zipfile
import csv
import re
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/finance/fec-candidate-links.json'
CONGRESS=ROOT/'data/people/congress-members.json'
TARGETS=ROOT/'data/batches/fec-committees.json'
YEARS=(2026,2024)
MAX_ZIP_BYTES=9_000_000
MAX_UNCOMPRESSED=14_000_000
MAX_LINKS=6000
DOCS='https://www.fec.gov/campaign-finance-data/candidate-committee-linkage-file-description/'

def fetch(year):
    url=f'https://www.fec.gov/files/bulk-downloads/{year}/ccl{str(year)[-2:]}.zip'
    req=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public disclosure indexing'})
    with urlopen(req,timeout=35) as response:
        if response.status!=200:
            raise RuntimeError('FEC public bulk file unavailable')
        data=response.read(MAX_ZIP_BYTES+1)
        if len(data)>MAX_ZIP_BYTES:
            raise RuntimeError('FEC link archive too large; no records overwritten')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries=[item for item in archive.infolist() if not item.is_dir()
                 and item.filename.lower().endswith(('.txt','.csv'))]
        if len(entries)!=1:
            raise RuntimeError('Unexpected candidate-committee ZIP contents')
        info=entries[0]
        if info.file_size>MAX_UNCOMPRESSED:
            raise RuntimeError('Unexpected decompressed FEC link archive size')
        content=archive.read(info).decode('utf-8-sig',errors='replace')
    return content,url

def collect():
    if not CONGRESS.exists() or not TARGETS.exists():
        raise RuntimeError('Congress and indexed FEC committees must exist before association discovery')
    people=json.loads(CONGRESS.read_text(encoding='utf-8'))['records']
    candidate_ids=set()
    for person in people:
        candidate_ids.update(person.get('fecCandidateIds') or [])
    committees=json.loads(TARGETS.read_text(encoding='utf-8'))['records']
    known_committees={row['id'][4:] for row in committees if row['id'].startswith('fec-C')}
    if len(candidate_ids)<300:
        raise RuntimeError('Insufficient verified candidate crosswalk identifiers')
    records={}
    totals={}
    for year in YEARS:
        content,url=fetch(year)
        first=content.splitlines()[0] if content.splitlines() else ''
        delimiter='|' if first.count('|')>=6 else '\t'
        rowcount=0
        for row in csv.reader(io.StringIO(content),delimiter=delimiter):
            rowcount+=1
            if len(row)!=7:
                continue
            candidate,cyear,fy,committee,kind,designation,linkage=[x.strip() for x in row]
            if not re.fullmatch(r'[HSP][A-Z0-9]{8}',candidate):
                continue
            if not re.fullmatch(r'C[0-9]{8}',committee):
                continue
            if candidate not in candidate_ids and committee not in known_committees:
                continue
            if not linkage.isdigit():
                continue
            if not cyear.isdigit() or not fy.isdigit():
                continue
            if int(fy)!=year:
                continue
            key='fec-ccl-'+str(year)+'-'+linkage
            records[key]={
                'id':key,'fecCandidateId':candidate,'committeeId':committee,
                'candidateElectionYear':int(cyear),'fecYear':year,
                'committeeType':kind[:3],'designation':designation[:3],
                'source':url,
                'reviewStatus':'FEC_official_linkage_indexed_unreviewed'
            }
            if len(records)>MAX_LINKS:
                raise RuntimeError('FEC link data exceeded bounded indexed target set')
        totals[str(year)]={'allFileRows':rowcount,'selectedLinks':sum(r['fecYear']==year for r in records.values())}
    if len(records)<300:
        raise RuntimeError('Unusually few FEC links; preserving existing corpus')
    doc={
        'schema':'power-atlas.fec.candidate-committee-links.v1',
        'publicationStatus':'official_fec_identifiers_source_review_pending',
        'sourceCatalog':DOCS,
        'meaning':'Candidate committee registration/linkage, not a monetary transfer or evidence of redistricting influence',
        'sources':totals,
        'records':sorted(records.values(),key=lambda r:r['id'])
    }
    text=json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(text.encode())>1500000:
        raise RuntimeError('Compact FEC association JSON exceeded storage cap')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=text:
        OUT.write_text(text,encoding='utf-8')
    print('FEC candidate/committee association rows:',len(records),'source years:',totals)

if __name__=='__main__':
    collect()
