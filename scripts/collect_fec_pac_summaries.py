"""Small official FEC PAC/party two-year cycle financial summaries.

Use federal public bulk files webk24.zip and webk26.zip, not the rate-limited
OpenFEC API or oversized transaction archives. Keep only indexed committee
IDs, aggregate receipts/disbursements and category totals. No donor names,
treasurer names, street addresses or transaction-level private details.
"""
from pathlib import Path
from io import BytesIO,StringIO
from urllib.request import Request,urlopen
from zipfile import ZipFile
from decimal import Decimal,InvalidOperation
import csv,json,re

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'data/finance/fec-committee-master.json'
OUT=ROOT/'data/finance/fec-pac-party-summaries.json'
YEARS=(2024,2026)
MAX_BYTES=4_000_000
MAX_EXPAND=15_000_000
MAX_ROWS=1500
SOURCE_DESC='https://www.fec.gov/campaign-finance-data/pac-and-party-summary-file-description/'
AMOUNT_FIELDS={
    'totalReceiptsUSD':5, 'transfersFromAffiliatesUSD':6,
    'individualContributionsUSD':7,'otherPoliticalCommitteeContributionsUSD':8,
    'totalDisbursementsUSD':12,'transfersToAffiliatesUSD':13,
    'contributionsToOtherCommitteesUSD':22,'independentExpendituresUSD':23,
    'partyCoordinatedExpendituresUSD':24
}
def amount(value):
    v=str(value or '').strip()
    if not v:return None
    try:
        d=Decimal(v)
        if not d.is_finite():return None
        if abs(d)>Decimal('1000000000000'):
            return None
        return float(d.quantize(Decimal('.01')))
    except (InvalidOperation,ValueError):
        return None

def read_year(year,keep):
    url=f'https://www.fec.gov/files/bulk-downloads/{year}/webk{year%100:02d}.zip'
    with urlopen(Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public FEC summary analysis',
                                     'Accept':'application/zip'}),timeout=36) as response:
        if response.status!=200:raise RuntimeError('FEC PAC archive HTTP not 200')
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise RuntimeError('Unexpectedly large official PAC summary archive')
    with ZipFile(BytesIO(raw)) as z:
        files=[e for e in z.infolist() if e.filename.lower().endswith(('.txt','.csv')) and not e.is_dir()]
        if len(files)!=1 or files[0].file_size>MAX_EXPAND:
            raise RuntimeError('Unexpected PAC summary archive contents/size')
        contents=z.read(files[0]).decode('utf-8-sig',errors='replace')
    parsed={}
    inspected=0
    first=contents.splitlines()[0] if contents else ''
    delimiter='|' if first.count('|')>=20 else '\t'
    for row in csv.reader(StringIO(contents),delimiter=delimiter):
        inspected+=1
        if len(row)!=27:continue
        cid=row[0].strip()
        if cid not in keep or not re.fullmatch(r'C[0-9]{8}',cid):continue
        fields={key:amount(row[pos]) for key,pos in AMOUNT_FIELDS.items()}
        record={'id':f'fec-pac-{year}-{cid}','cycle':year,'committeeId':cid,
                'name':row[1].strip()[:150],
                'committeeType':row[2].strip()[:5],
                'designation':row[3].strip()[:5],
                'coverageEnd':row[26].strip()[:16],
                'source':url,'reviewStatus':'FEC_official_cycle_summary_unreviewed',
                **fields}
        if record['totalReceiptsUSD'] is None and record['totalDisbursementsUSD'] is None:
            continue
        parsed[record['id']]=record
    return parsed,{'cycle':year,'source':url,'rawRowsInspected':inspected,'matchingCommitteeRows':len(parsed)}

def main():
    records=json.loads(MASTER.read_text(encoding='utf-8'))['records']
    ids={r['committeeId'] for r in records}
    if not 100<=len(ids)<=5000:raise RuntimeError('Committee identity target range invalid')
    all_records={}
    sources=[]
    for year in YEARS:
        filtered,info=read_year(year,ids)
        all_records.update(filtered);sources.append(info)
    if not 10<=len(all_records)<=MAX_ROWS:
        raise RuntimeError('Source match count unexpected: '+str(len(all_records)))
    doc={'schema':'power-atlas.fec-pac-party-summaries.v1',
         'publicationStatus':'official_FEC_cycle_aggregate_not_party_donation_network',
         'sourceCatalog':SOURCE_DESC,
         'meaning':'PAC/party aggregate reported categories for each election cycle; totals do not reveal recipient committees, particular donors or map-related influence.',
         'scope':'Only committees already in compact FEC committee master, not all federal PACs',
         'years':sources,
         'records':sorted(all_records.values(),key=lambda r:r['id'])}
    body=json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n'
    if len(body.encode())>425000:
        raise RuntimeError('PAC summary output exceeds storage limit')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=body:
        OUT.write_text(body,encoding='utf-8')
    print('Official PAC-party financial summaries:',len(all_records),'cycles:',sources)
if __name__=='__main__':
    main()
