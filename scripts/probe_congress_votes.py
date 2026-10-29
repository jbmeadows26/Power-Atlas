"""Verify openly documented, no-key CC0 voting-data alternatives.

Do not bypass agency 403/429 or paywalls. Bounded ordinary public requests
against a secondary provider advertising CC0 bulk exports, with provenance.
Diagnostic metadata only; never persist raw HTML or individual voting positions.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError,URLError
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/health/congressional-vote-open-data-probe.json'
BASE='https://www.ballotwatch.io'
DOCS=BASE+'/developers'
MAX_HTML=200000
MAX_JSON=100000
KEYWORDS=('full record downloads','open-data manifest','votes json sample','members csv sample','openapi source')

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[];self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.current={'href':dict(attrs).get('href',''),'parts':[]}
    def handle_data(self,data):
        if self.current:self.current['parts'].append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.current:
            self.links.append({'href':self.current['href'],
                               'label':' '.join(''.join(self.current['parts']).split())[:120]})
            self.current=None

def read(url,limit):
    req=Request(url,headers={'User-Agent':'PowerAtlasResearch/1.0 public civic open-data research'})
    with urlopen(req,timeout=22) as response:
        if response.status!=200:
            raise RuntimeError('Unexpected public source response')
        body=response.read(limit+1)
        if len(body)>limit:
            raise RuntimeError('Bounded public document exceeded limit')
        return body

def probe():
    doc={'schema':'power-atlas.vote-alternative-probe.v1',
         'source':DOCS,'sourceLicenseClaim':'CC0-1.0 (provider documentation)',
         'originalGovernmentSources':['https://clerk.house.gov/','https://www.senate.gov/'],
         'items':[], 'status':'not_confirmed'}
    try:
        html=read(DOCS,MAX_HTML).decode('utf-8',errors='replace')
        parser=Links()
        parser.feed(html)
        for entry in parser.links:
            label=entry['label']
            if not any(term in label.lower() for term in KEYWORDS):
                continue
            absolute=urljoin(DOCS,entry['href'])
            if urlparse(absolute).scheme!='https' or urlparse(absolute).netloc!='www.ballotwatch.io':
                continue
            doc['items'].append({'label':label,'url':absolute})
        doc['status']='public_document_reachable'
        if not doc['items']:
            doc['status']='bulk_link_not_exposed_in_static_html'
    except HTTPError as exc:
        doc['status']='http_access_blocked_or_not_found'
        doc['httpStatus']=exc.code
    except (URLError,OSError,RuntimeError) as exc:
        doc['status']='public_document_unavailable'
        doc['errorType']=type(exc).__name__
    # Public no-key metadata endpoint is documented at /api/v1/stats.
    try:
        payload=json.loads(read(BASE+'/api/v1/stats',MAX_JSON))
        doc['statsEndpoint']={
            'status':'reachable','rootKeys':sorted(payload.keys()) if isinstance(payload,dict) else [],
            'source':BASE+'/api/v1/stats'
        }
    except HTTPError as exc:
        doc['statsEndpoint']={'status':'http_error','code':exc.code}
    except (URLError,OSError,ValueError,RuntimeError) as exc:
        doc['statsEndpoint']={'status':type(exc).__name__}
    # The no-key search endpoint is publicly documented. Test targeted terms,
    # save only response schema and two sanitized public record examples.
    from urllib.parse import urlencode
    doc['searchProbes']=[]
    for phrase in ('redistricting', 'voting rights', 'election'):
        query=BASE+'/api/v1/search?'+urlencode({'q':phrase,'limit':5})
        probe={'query':phrase,'source':query}
        try:
            body=json.loads(read(query,MAX_JSON))
            probe['status']='reachable'
            probe['rootKeys']=list(body.keys()) if isinstance(body,dict) else []
            data=body.get('data') if isinstance(body,dict) else None
            probe['dataType']=type(data).__name__
            if isinstance(data,dict):
                probe['dataKeys']=list(data.keys())
                probe['collections']={}
                for name,rows in data.items():
                    if isinstance(rows,list):
                        probe['collections'][name]={'count':len(rows),'sampleKeys':list(rows[0].keys()) if rows and isinstance(rows[0],dict) else []}
                        if rows and isinstance(rows[0],dict):
                            first=rows[0]
                            probe['collections'][name]['example']={
                                k:str(first[k])[:110] for k in ('id','title','bill_id','vote_id','source','url') if k in first
                            }
            elif isinstance(data,list):
                probe['dataCount']=len(data)
                probe['firstKeys']=list(data[0].keys()) if data and isinstance(data[0],dict) else []
        except HTTPError as exc:
            probe['status']='http_error';probe['httpStatus']=exc.code
        except (URLError,OSError,ValueError,RuntimeError) as exc:
            probe['status']=type(exc).__name__
        doc['searchProbes'].append(probe)
    rendered=json.dumps(doc,indent=2,ensure_ascii=False)+'\n'
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if not OUT.exists() or OUT.read_text(encoding='utf-8')!=rendered:
        OUT.write_text(rendered,encoding='utf-8')
    print('Public CC0 alternative:',doc['status'],'link labels:',len(doc['items']),
          'API:',doc['statsEndpoint']['status'])
if __name__=='__main__':
    probe()
