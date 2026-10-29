"""Index public House Clerk roll-call metadata from its static year tables.

Official Clerk of the U.S. House, 119th Congress sessions 2025/2026.
Each year has static ROLL_000.asp, ROLL_100.asp etc indexes. Index only
roll numbers, issue, question, result, title and provenance. Exclude member
voting positions until the source XML access and reconciliation are checked.
"""
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/legislation/house-119-rollcalls.json'
YEARS=(2025,2026)
BASE='https://clerk.house.gov/evs/'
TOPICS=('redistrict','reapportion','voting rights','election','ballot','census','congressional district','voter')
MAX_PAGE_BYTES=350000

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.row=False;self.incell=0;self.textparts=[];self.cells=[];self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=='tr':
            self.row=True;self.cells=[];self.textparts=[];self.incell=0
        elif tag in ('td','th') and self.row:
            self.incell+=1
            if self.incell==1:self.textparts=[]
    def handle_data(self,data):
        if self.row and self.incell:self.textparts.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.row and self.incell:
            value=' '.join(''.join(self.textparts).split())
            self.cells.append(value);self.textparts=[];self.incell-=1
        elif tag=='tr' and self.row:
            if len(self.cells)>=6:self.rows.append(self.cells[:6])
            self.row=False;self.cells=[];self.incell=0;self.textparts=[]

def read_page(url):
    req=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 (official public roll-call index)','Accept':'text/html'})
    with urlopen(req,timeout=25) as res:
        if res.status!=200:
            raise RuntimeError('Clerk HTML index returned non-200')
        raw=res.read(MAX_PAGE_BYTES+1)
        if len(raw)>MAX_PAGE_BYTES:
            raise RuntimeError('Clerk year index page exceeded 350 KB')
    page=TableParser()
    page.feed(raw.decode('utf-8',errors='replace'))
    return page.rows

def collect():
    old=json.loads(OUT.read_text(encoding='utf-8'))['records'] if OUT.exists() else []
    records={r['id']:r for r in old}
    series=[]
    for year in YEARS:
        encountered=set(); pages=0
        for group in range(0,800,100):
            url=BASE+str(year)+f'/ROLL_{group:03d}.asp'
            try:
                rows=read_page(url)
            except HTTPError as err:
                if err.code==404 and group>=100:
                    break
                if err.code in (401,403,429):
                    raise RuntimeError(f'House Clerk access/rate restriction HTTP {err.code}; no changes written') from err
                raise
            valid=0
            for cells in rows:
                m=re.fullmatch(r'0*([0-9]{1,4})',cells[0].strip())
                if not m:continue
                number=int(m.group(1))
                if number<1 or number>1500:continue
                if number in encountered:continue
                encountered.add(number);valid+=1
                roll_id=f'house-119-{year}-{number:04d}'
                title=cells[5][:300]
                issue=cells[2][:100]
                question=cells[3][:160]
                text=' '.join((title,issue,question)).lower()
                records[roll_id]={
                    'id':roll_id,'chamber':'House','congress':119,'year':year,
                    'roll':number,'dateDisplay':cells[1][:32],
                    'issue':issue,'question':question,'resultCode':cells[4][:15],
                    'title':title,
                    'topicKeywordMatch':any(t in text for t in TOPICS),
                    'source':BASE+str(year)+f'/roll{number:03d}.xml',
                    'sourceIndex':url,
                    'reviewStatus':'official_house_clerk_rollcall_indexed'
                }
            if valid:
                pages+=1
            elif group>=100:
                break
        count=sum(r['year']==year for r in records.values())
        if not 90<=count<=900:
            raise RuntimeError(f'Unexpected House roll-index count {year}: {count}; existing data preserved')
        series.append({'year':year,'rolls':count,'pages':pages,
                       'topicKeywordCandidates':sum(r['year']==year and r['topicKeywordMatch'] for r in records.values())})
        print('House year',year,'rolls',count,'pages',pages,flush=True)
    data={
        'schema':'power-atlas.house-119-rollcall-index.v1',
        'sourceAuthority':'Office of the Clerk, U.S. House of Representatives',
        'sourceIndex':'https://clerk.house.gov/evs/2026/index.asp',
        'publicationStatus':'official_Clerk_metadata_indexed',
        'limitations':'Member-level positions are NOT ingested. Keyword matches are exploratory; a legislative roll call does not itself establish a redistricting outcome or improper influence.',
        'years':series,'records':sorted(records.values(),key=lambda r:(r['year'],r['roll']))
    }
    content=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    if len(content.encode())>1000000:raise RuntimeError('House roll index exceeded compact output cap')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=content:
        OUT.write_text(content,encoding='utf-8')
    print('Published House index count:',len(records))

if __name__=='__main__':
    collect()
