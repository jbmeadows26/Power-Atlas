"""Official FEC committee master names for already indexed candidate links.

Reads keyless public committee master archives (2024 and 2026), filters to
previously indexed FEC committee IDs and emits one current-best metadata row
per committee. Does not retain treasurer names, mailing addresses or ZIPs.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile
from io import BytesIO, StringIO
import csv
import json
import re

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'data/finance/fec-candidate-links.json'
DISCOVERY=ROOT/'data/batches/fec-committees.json'
OUTPUT=ROOT/'data/finance/fec-committee-master.json'
YEARS=(2024,2026)
LIMIT=7_000_000
SOURCE_DOCS='https://www.fec.gov/campaign-finance-data/committee-master-file-description/'

def collect():
    if not INPUT.exists():
        raise RuntimeError('FEC candidate link data missing: collect before master enrichment')
    raw_links=json.loads(INPUT.read_text(encoding='utf-8'))['records']
    keep={x['committeeId'] for x in raw_links}
    keep|={x['id'][4:] for x in json.loads(DISCOVERY.read_text(encoding='utf-8'))['records'] if x['id'].startswith('fec-C')}
    if len(keep)<300:
        raise RuntimeError('Not enough target committees to justify download')
    committees={}
    counts={}
    for year in YEARS:
        url=f'https://www.fec.gov/files/bulk-downloads/{year}/cm{year%100:02d}.zip'
        with urlopen(Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public political committee indexing'}),timeout=35) as r:
            if r.status!=200:
                raise RuntimeError('FEC committee master not available')
            body=r.read(LIMIT+1)
            if len(body)>LIMIT:
                raise RuntimeError('Archive exceeds small FEC bulk source cap')
        archive=ZipFile(BytesIO(body))
        files=[f for f in archive.infolist() if not f.is_dir() and f.filename.lower().endswith(('.txt','.csv'))]
        if len(files)!=1 or files[0].file_size>25_000_000:
            raise RuntimeError('Unexpected FEC committee master ZIP layout')
        data=archive.read(files[0]).decode('utf-8-sig',errors='replace')
        lines=data.splitlines()
        delimiter='|' if lines and lines[0].count('|')>=14 else '\t'
        matched=0
        for item in csv.reader(StringIO(data),delimiter=delimiter):
            if len(item)!=15:
                continue
            committee_id=item[0].strip()
            if committee_id not in keep or not re.fullmatch(r'C[0-9]{8}',committee_id):
                continue
            name=item[1].strip()
            if not name:
                continue
            row={
                'id':'fec-'+committee_id,'committeeId':committee_id,
                'name':name[:200],'state':item[6].strip()[:2],
                'designation':item[8].strip()[:2],
                'committeeType':item[9].strip()[:2],
                'partyCode':item[10].strip()[:5],
                'filingFrequency':item[11].strip()[:2],
                'organizationType':item[12].strip()[:2],
                'connectedOrganization':item[13].strip()[:190],
                'candidateId':item[14].strip()[:9],
                'source':url,'sourceYear':year,
                'reviewStatus':'official_FEC_committee_master_unreviewed'
            }
            committees[committee_id]=row
            matched+=1
        counts[str(year)]=matched
    if len(committees)<300:
        raise RuntimeError('FEC committee enrichment count unexpectedly low')
    data={'schema':'power-atlas.fec.committee-master.v1',
          'publicationStatus':'official_committee_source_indexed',
          'sourceCatalog':SOURCE_DOCS,
          'meaning':'Committee registration identity and formal reported affiliations, not proof of expenditure or map influence',
          'matchedPerCycle':counts,
          'records':sorted(committees.values(),key=lambda x:x['committeeId'])}
    text=json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(text.encode())>650000:
        raise RuntimeError('Compact committee master output exceeded cap')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8')!=text:
        OUTPUT.write_text(text,encoding='utf-8')
    print('Official committee names indexed:',len(committees),'per-year matches:',counts)

if __name__=='__main__':
    collect()
