"""Index election certification authority and official results sources.

Never label MEDSL/OpenElections vote counts as certified without exact
year/office/stage/district comparison to authoritative state canvass.
The FEC republishes state-certified totals but is not certifying authority.
Small state-office source index, no raw HTML retained.
"""
import json
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/elections/official-source-index.json'
STATES=ROOT/'data/geography/states.json'
FEC_DIR='https://www.fec.gov/introduction-campaign-finance/how-to-research-public-records/state-election-offices/'
FEC_RESULT='https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/'
FEC_2024='https://www.fec.gov/documents/5645/2024presgeresults.xlsx'
FEC_2022='https://www.fec.gov/documents/5676/federalelections2022.xlsx'
MAX_BYTES=350000

class TableLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table=False
        self.in_row=False
        self.in_cell=False
        self.cell_text=[]
        self.cell_links=[]
        self.row=[]
        self.rows=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='tr':
            self.in_row=True
            self.row=[]
        elif tag in ('td','th') and self.in_row:
            self.in_cell=True
            self.cell_text=[]
            self.cell_links=[]
        elif tag=='a' and self.in_cell:
            href=attrs.get('href','')
            if href.startswith('https://'):
                self.cell_links.append(href)
    def handle_data(self,content):
        if self.in_cell:
            self.cell_text.append(content)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.in_cell:
            self.row.append({'text':' '.join(''.join(self.cell_text).split()),'links':self.cell_links})
            self.in_cell=False
        elif tag=='tr' and self.in_row:
            if len(self.row)>=3:
                self.rows.append(self.row)
            self.in_row=False

def collect():
    master=json.loads(STATES.read_text(encoding='utf-8'))['states']
    target={r['name'].lower():r for r in master}
    target['district of columbia']=next(r for r in master if r['fips']=='11')
    html=''
    try:
        req=Request(FEC_DIR,headers={'User-Agent':'PowerAtlasResearch/1.0 election-certified source index',
                                      'Accept':'text/html'})
        with urlopen(req,timeout=25) as response:
            if response.status!=200:raise RuntimeError('Unexpected FEC directory status')
            blob=response.read(MAX_BYTES+1)
            if len(blob)>MAX_BYTES:raise RuntimeError('Unexpectedly large FEC directory')
            html=blob.decode('utf-8',errors='replace')
    except HTTPError as exc:
        if exc.code in (401,403,429):
            raise RuntimeError('FEC directory access restriction HTTP '+str(exc.code)+', do not bypass') from exc
        raise
    parser=TableLinks()
    parser.feed(html)
    index={}
    for row in parser.rows:
        label=row[0]['text'].lower()
        # FEC has some split entries such as "Rhode Island (Election Results)".
        label=re.sub(r'\s*\([^)]*\)\s*','',label).strip()
        if label not in target:
            continue
        entity=target[label]
        state=entity['postal']
        urls=[u for cell in row[1:3] for u in cell['links'] if u.startswith('https://')]
        if not urls:continue
        new={
            'state':state,'stateName':entity['name'],'fips':entity['fips'],
            'certificationAuthority':'State election office (see FEC directory)',
            'electionOfficeURL':urls[0],
            'directorySource':FEC_DIR,
            'officialCertifiedResultURL':None,
            'stateCertifiedVoteTotalsRetrieved':False,
            'officialResultStatus':'election_office_link_only_not_certified_canvass',
            'researchAction':'Find official canvass of votes for exact state, year, office, district and stage'
        }
        # Prefer a separately listed election-results entry for split states.
        if state not in index or 'election results' in row[0]['text'].lower():
            index[state]=new
    if len(index)<48:
        raise RuntimeError('Only '+str(len(index))+' official election office URLs parsed, preserve existing output')
    records=sorted(index.values(),key=lambda x:x['state'])
    catalog={
        'schema':'power-atlas.elections.official-sources.v1',
        'publicationStatus':'authority_url_verified_from_FEC_directory_but_canvasses_not_fetched',
        'authorityRule':'State and local election offices certify. FEC compiles reported federal results; research datasets are not automatically official certifications.',
        'records':records,
        'federalCompilations':[
            {'year':2024,'office':'president','source':FEC_2024,'status':'published_FEC_state_reported_compilation_download_unverified'},
            {'year':2022,'office':'president_senate_house','source':FEC_2022,'status':'published_FEC_biennial_compilation_download_unverified'}
        ],
        'analysisComparators':[
            {'provider':'MIT Election Data and Science Lab','office':'US House','years':'1976-2024','source':'https://doi.org/10.7910/DVN/IG0UN2','status':'standardized_research_data_not_an_individual_state_certification','license':'CC0-1.0'},
            {'provider':'OpenElections','level':'state_county_precinct_variable_coverage','source':'https://github.com/openelections','status':'derived_from_official_sources_reconciliation_required'},
            {'provider':'University of Florida Election Lab','level':'turnout_and_voting_administration','source':'https://election.lab.ufl.edu/','status':'analysis_not_official_certification'}
        ],
        'comparisonKey':['state','year','office','electionStage','district','candidateOrParty','voteCountingBasis'],
        'unresolvedCertificationGaps':len(records)
    }
    content=json.dumps(catalog,indent=2,ensure_ascii=False)+'\n'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=content:
        OUT.write_text(content,encoding='utf-8')
    print('Source-indexed official election authorities:',len(records),'certified canvasses:',0)
if __name__=='__main__':
    collect()
